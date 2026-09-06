"""Pruebas de la recoleccion de nectar. Ver F9 en el plan.

Invariantes de simulation/nectar.py: Q >= 0 siempre, Q = 0 si y solo si
F = 0 (decision D-04), y se acumula sobre las flores VISITADAS, no las
polinizadas (decision D-03), lo que ya queda garantizado por la firma de
`recolectar`, que no recibe el conteo de polinizadas.
"""

import math
import unittest

import numpy as np

from bee_sim.generators.lcg import LCG
from bee_sim.simulation.nectar import recolectar

FORMA = 1.8
ESCALA = 0.033  # nivel 'media' en config/base.yaml


class NectarTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"nectar": {"shape": FORMA}}

    def test_flores_visitadas_invalidas_falla(self):
        for valor in (-1, -1.0, 1.5, True, "3"):
            with self.subTest(flores_visitadas=valor):
                with self.assertRaises(ValueError):
                    recolectar(valor, ESCALA, self.cfg, LCG(seed=1))

    def test_forma_y_escala_invalidas_fallan(self):
        rng = LCG(seed=1)
        with self.assertRaises(ValueError):
            recolectar(5, ESCALA, {"nectar": {"shape": 0.0}}, rng)
        with self.assertRaises(ValueError):
            recolectar(5, 0.0, self.cfg, rng)
        with self.assertRaises(ValueError):
            recolectar(5, -1.0, self.cfg, rng)
        with self.assertRaises(ValueError):
            recolectar(5, float("nan"), self.cfg, rng)

    def test_cero_visitas_da_cero_sin_consumir_uniformes(self):
        rng = LCG(seed=1)
        self.assertEqual(recolectar(0, ESCALA, self.cfg, rng), 0.0)
        self.assertEqual(rng.consumidos, 0)

    def test_con_visitas_el_nectar_es_positivo(self):
        rng = LCG(seed=7)
        for f in (1, 2, 5, 20):
            with self.subTest(flores_visitadas=f):
                self.assertGreater(recolectar(f, ESCALA, self.cfg, rng), 0.0)

    def test_reproducibilidad_misma_semilla(self):
        a = recolectar(10, ESCALA, self.cfg, LCG(seed=42))
        b = recolectar(10, ESCALA, self.cfg, LCG(seed=42))
        self.assertEqual(a, b)

    def test_media_escala_con_flores_visitadas(self):
        """Suma de F Gammas(forma, escala) tiene media F * forma * escala."""
        rng = LCG(seed=5)
        f = 8
        muestras = [recolectar(f, ESCALA, self.cfg, rng) for _ in range(4000)]
        esperado = f * FORMA * ESCALA
        self.assertTrue(math.isclose(np.mean(muestras), esperado, rel_tol=0.1))

    def test_no_depende_de_cuantas_flores_fueron_polinizadas(self):
        """D-03: recolectar no recibe el conteo de polinizadas, solo el de
        visitadas, asi que su firma ya impide acumular sobre las polinizadas."""
        import inspect
        parametros = list(inspect.signature(recolectar).parameters)
        self.assertEqual(parametros[0], "flores_visitadas")
        self.assertNotIn("flores_polinizadas", parametros)
        self.assertNotIn("polinizadas", parametros)


if __name__ == "__main__":
    unittest.main()
