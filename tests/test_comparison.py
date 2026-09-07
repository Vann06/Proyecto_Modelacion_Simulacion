"""Pruebas del criterio de equivalencia entre metodos."""

import unittest

from bee_sim.analysis.comparison import _prueba_equivalencia_pareada


class EquivalenceTests(unittest.TestCase):
    def test_demuestra_equivalencia_dentro_del_margen(self):
        a = [100, 102, 98, 101, 99, 100]
        b = [100, 101, 99, 100, 100, 100]
        resultado = _prueba_equivalencia_pareada(a, b, margen=2.0)
        self.assertTrue(resultado["equivalentes"])
        self.assertGreater(resultado["ic_equivalencia"][0], -2.0)
        self.assertLess(resultado["ic_equivalencia"][1], 2.0)

    def test_no_confunde_no_diferencia_con_equivalencia(self):
        # Poca informacion y variacion amplia: aunque la media sea similar, el
        # intervalo no cabe dentro del margen practico.
        a = [90, 110, 90, 110]
        b = [100, 100, 100, 100]
        resultado = _prueba_equivalencia_pareada(a, b, margen=2.0)
        self.assertFalse(resultado["equivalentes"])

    def test_diferencia_constante_fuera_del_margen(self):
        resultado = _prueba_equivalencia_pareada(
            [105, 105, 105], [100, 100, 100], margen=2.0,
        )
        self.assertFalse(resultado["equivalentes"])
        self.assertEqual(resultado["p_inferior"], 0.0)
        self.assertEqual(resultado["p_superior"], 1.0)


if __name__ == "__main__":
    unittest.main()
