"""Pruebas del lector de campanas planas y anidadas."""

import json
from pathlib import Path
import tempfile
import unittest

import yaml

from bee_sim.analysis.campaign_io import cargar_resumenes, csvs_por_escenario


class CampaignIOTests(unittest.TestCase):
    def _crear_trio(self, carpeta, numero, escenario, semilla):
        carpeta.mkdir(parents=True, exist_ok=True)
        nombre = f"run_{numero:04d}"
        (carpeta / f"{nombre}.csv").write_text("run_id\n0\n", encoding="utf-8")
        (carpeta / f"{nombre}_summary.json").write_text(
            json.dumps({"flores_polinizadas": 10}), encoding="utf-8"
        )
        cfg = {
            "simulation": {"seed": semilla, "replications": 2},
            "_origen": f"{escenario}.yaml",
        }
        (carpeta / f"{nombre}_config.yaml").write_text(
            yaml.safe_dump(cfg), encoding="utf-8"
        )

    def test_lee_disposicion_plana(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            self._crear_trio(raiz, 1, "base", 123)
            self._crear_trio(raiz, 2, "base", 456)
            filas = cargar_resumenes(raiz)
            self.assertEqual(filas[0]["escenario"], "base")
            self.assertEqual(filas[0]["semilla"], 123)
            self.assertEqual(len(csvs_por_escenario(raiz, "base")), 2)
            self.assertEqual(
                cargar_resumenes(raiz, ultimos_por_escenario=1)[0]["semilla"],
                456,
            )
            self.assertEqual(len(csvs_por_escenario(raiz, "base", ultimos=1)), 1)

    def test_lee_disposicion_anidada_anterior(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            self._crear_trio(raiz / "flowers_low", 1, "flowers_low", 456)
            self.assertEqual(cargar_resumenes(raiz)[0]["escenario"], "flowers_low")


if __name__ == "__main__":
    unittest.main()
