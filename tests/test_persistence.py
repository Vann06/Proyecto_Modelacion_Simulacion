"""Pruebas de F5: escritura del trio de archivos y los scripts de CLI.

Usan tempfile para no ensuciar results/runs real. Compatibles con unittest
y pytest, igual que el resto de tests/.
"""

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bee_sim.config import cargar
from bee_sim.generators import crear_fuente
from bee_sim.models import CAMPOS
from bee_sim.simulation.engine import simular_jornada
from bee_sim.simulation.metrics import resumir

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _persistence import guardar_corrida, siguiente_run_id  # noqa: E402
from run_experiment import resolver_semillas  # noqa: E402

CONFIG = Path(__file__).resolve().parents[1] / "config"
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
RAIZ = Path(__file__).resolve().parents[1]


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cargar(CONFIG / "base.yaml")
        self.cfg["colony"]["active_bees"] = 3
        self.cfg["simulation"]["day_minutes"] = 60
        rng = crear_fuente("lcg", 2026)
        self.viajes = simular_jornada(self.cfg, rng, run_id=0)
        self.resumen = resumir(self.viajes, self.viajes.colonia, self.cfg)

    def test_siguiente_run_id_carpeta_inexistente(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(siguiente_run_id(Path(tmp) / "no_existe"), 1)

    def test_siguiente_run_id_autoincrementa(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "run_0001.csv").write_text("x")
            (carpeta / "run_0007.csv").write_text("x")
            self.assertEqual(siguiente_run_id(carpeta), 8)

    def test_semillas_de_campana_son_dispersas_y_reutilizables(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "semillas.json"
            primera = resolver_semillas(ruta, 20, 2026)
            segunda = resolver_semillas(ruta, 20, 2026)
            self.assertEqual(primera, segunda)
            self.assertEqual(len(set(primera)), 20)
            self.assertGreater(max(primera) - min(primera), 2000)

    def test_guardar_corrida_escribe_los_tres_archivos(self):
        with tempfile.TemporaryDirectory() as tmp:
            rutas = guardar_corrida(self.viajes, self.cfg, self.resumen, tmp, run_numero=1)
            self.assertTrue(rutas["csv"].is_file())
            self.assertTrue(rutas["config"].is_file())
            self.assertTrue(rutas["summary"].is_file())
            self.assertEqual(rutas["csv"].name, "run_0001.csv")

    def test_csv_tiene_las_columnas_de_trip_en_orden(self):
        with tempfile.TemporaryDirectory() as tmp:
            rutas = guardar_corrida(self.viajes, self.cfg, self.resumen, tmp, run_numero=1)
            with open(rutas["csv"], newline="", encoding="utf-8") as f:
                encabezado = next(csv.reader(f))
            self.assertEqual(encabezado, CAMPOS)

    def test_csv_tiene_una_fila_por_viaje(self):
        with tempfile.TemporaryDirectory() as tmp:
            rutas = guardar_corrida(self.viajes, self.cfg, self.resumen, tmp, run_numero=1)
            with open(rutas["csv"], newline="", encoding="utf-8") as f:
                filas = list(csv.DictReader(f))
            self.assertEqual(len(filas), len(self.viajes))

    def test_summary_json_coincide_con_resumir(self):
        with tempfile.TemporaryDirectory() as tmp:
            rutas = guardar_corrida(self.viajes, self.cfg, self.resumen, tmp, run_numero=1)
            with open(rutas["summary"], encoding="utf-8") as f:
                guardado = json.load(f)
            self.assertEqual(guardado, self.resumen)

    def test_config_guardado_es_recargable_y_reproduce_la_corrida(self):
        """El criterio de F5: solo con el _config.yaml guardado se reproduce
        un CSV identico."""
        with tempfile.TemporaryDirectory() as tmp:
            rutas = guardar_corrida(self.viajes, self.cfg, self.resumen, tmp, run_numero=1)
            cfg_recargado = cargar(rutas["config"])
            rng = crear_fuente(cfg_recargado["simulation"]["rng_source"],
                                cfg_recargado["simulation"]["seed"])
            viajes_2 = simular_jornada(cfg_recargado, rng, run_id=0)
            self.assertEqual(self.viajes, viajes_2)

    def test_no_escribe_nada_si_falla_antes_de_guardar(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp) / "runs"
            with self.assertRaises((TypeError, AttributeError, ValueError)):
                guardar_corrida(None, self.cfg, self.resumen, carpeta, run_numero=1)
            self.assertFalse(carpeta.exists())


class RunSimulationScriptTests(unittest.TestCase):
    """Prueba el CLI real invocandolo como subproceso, con PYTHONPATH=src."""

    def _correr(self, *args):
        entorno = {"PYTHONPATH": str(RAIZ / "src")}
        import os
        entorno = {**os.environ, **entorno}
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "run_simulation.py"), *args],
            cwd=RAIZ, capture_output=True, text=True, env=entorno,
        )

    def test_dos_corridas_misma_semilla_generan_csv_identico(self):
        with tempfile.TemporaryDirectory() as tmp:
            r1 = self._correr("--config", "config/base.yaml", "--seed", "2026", "--out", tmp)
            r2 = self._correr("--config", "config/base.yaml", "--seed", "2026", "--out", tmp)
            self.assertEqual(r1.returncode, 0, r1.stderr)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            csv1 = (Path(tmp) / "run_0001.csv").read_text(encoding="utf-8")
            csv2 = (Path(tmp) / "run_0002.csv").read_text(encoding="utf-8")
            self.assertEqual(csv1, csv2)

    def test_config_inexistente_falla_con_codigo_distinto_de_cero(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._correr("--config", "config/no_existe.yaml", "--out", tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(list(Path(tmp).glob("*")), [])


if __name__ == "__main__":
    unittest.main()
