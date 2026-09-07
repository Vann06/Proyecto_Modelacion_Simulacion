"""Pruebas de F6: catalogo de escenarios y ejecucion de campana."""

from pathlib import Path
import unittest

from bee_sim.config import cargar
from bee_sim.experiments.runner import correr_campana, correr_escenario
from bee_sim.experiments.scenarios import ESCENARIOS, cargar_escenario


class ScenariosTests(unittest.TestCase):
    def test_los_doce_escenarios_cargan_sin_error(self):
        for nombre in ESCENARIOS:
            with self.subTest(escenario=nombre):
                cfg = cargar_escenario(nombre)
                self.assertIn("simulation", cfg)

    def test_cargar_escenario_coincide_con_config_cargar(self):
        directo = cargar(Path("config") / "base.yaml")
        via_catalogo = cargar_escenario("base")
        self.assertEqual(directo, via_catalogo)

    def test_nombre_desconocido_lanza_value_error_con_nombres_validos(self):
        with self.assertRaises(ValueError) as ctx:
            cargar_escenario("no_existe")
        mensaje = str(ctx.exception)
        for nombre in ESCENARIOS:
            self.assertIn(nombre, mensaje)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.semillas = [2026 + i for i in range(10)]

    def test_correr_escenario_devuelve_un_resumen_por_replica(self):
        resumenes = correr_escenario("bees_low", 5, self.semillas)
        self.assertEqual(len(resumenes), 5)
        for resumen in resumenes:
            self.assertIn("viajes_iniciados", resumen)

    def test_correr_escenario_es_reproducible_con_las_mismas_semillas(self):
        a = correr_escenario("base", 4, self.semillas)
        b = correr_escenario("base", 4, self.semillas)
        self.assertEqual(a, b)

    def test_correr_escenario_falla_si_faltan_semillas(self):
        with self.assertRaises(ValueError):
            correr_escenario("base", 20, self.semillas)

    def test_correr_escenario_nombre_desconocido_propaga_value_error(self):
        with self.assertRaises(ValueError):
            correr_escenario("no_existe", 1, self.semillas)

    def test_correr_campana_cubre_los_doce_escenarios(self):
        resultado = correr_campana(2, self.semillas)
        self.assertEqual(set(resultado.keys()), set(ESCENARIOS.keys()))
        for nombre, resumenes in resultado.items():
            with self.subTest(escenario=nombre):
                self.assertEqual(len(resumenes), 2)

    def test_correr_campana_no_mezcla_escenarios(self):
        resultado = correr_campana(3, self.semillas)
        # flowers_low fija disponibilidad baja; base la sortea. Si comparten
        # el mismo resumen para todas las corridas, algo se esta mezclando.
        self.assertNotEqual(resultado["flowers_low"], resultado["base"])


if __name__ == "__main__":
    unittest.main()
