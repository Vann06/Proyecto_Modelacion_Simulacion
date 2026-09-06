"""Pruebas del paso de polinizacion. Ver F9 en el plan."""

import math
import unittest

import numpy as np

from bee_sim.generators.lcg import LCG
from bee_sim.generators.poisson import poisson_inversa
from bee_sim.simulation.pollination import media_marginal_teorica, polinizar, tasa_observada


class PollinationTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"pollination": {"p_success": 0.65}}

    def test_flores_visitadas_negativas_falla(self):
        with self.assertRaises(ValueError):
            polinizar(-1, self.cfg, LCG(seed=1))

    def test_polinizadas_nunca_supera_visitadas(self):
        rng = LCG(seed=7)
        for f in range(0, 30):
            x = polinizar(f, self.cfg, rng)
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x, f)

    def test_visitadas_cero_da_polinizadas_cero_sin_consumir(self):
        rng = LCG(seed=1)
        self.assertEqual(polinizar(0, self.cfg, rng), 0)
        self.assertEqual(rng.consumidos, 0)

    def test_reproducibilidad_misma_semilla(self):
        a = polinizar(20, self.cfg, LCG(seed=42))
        b = polinizar(20, self.cfg, LCG(seed=42))
        self.assertEqual(a, b)

    def test_tasa_observada_indefinida_sin_visitas(self):
        self.assertIsNone(tasa_observada(0, 0))

    def test_tasa_observada_converge_a_p_success(self):
        rng = LCG(seed=11)
        f = 40
        tasas = [tasa_observada(f, polinizar(f, self.cfg, rng)) for _ in range(2000)]
        self.assertTrue(math.isclose(np.mean(tasas), self.cfg["pollination"]["p_success"], rel_tol=0.05))

    def test_adelgazamiento_media_y_varianza_con_nivel_fijo(self):
        """F ~ Poisson(mu), X = polinizar(F, p) -> la marginal de X es
        Poisson(mu*p): media y varianza deben coincidir con media_marginal_teorica.
        Solo vale con un nivel de disponibilidad fijo (ver docstring de
        media_marginal_teorica en simulation/pollination.py)."""
        mu = 8.0
        rng = LCG(seed=31)
        xs = np.array([polinizar(poisson_inversa(mu, rng), self.cfg, rng) for _ in range(20000)])
        teorica = media_marginal_teorica(mu, self.cfg)
        self.assertTrue(math.isclose(xs.mean(), teorica, rel_tol=0.08))
        self.assertTrue(math.isclose(xs.var(), teorica, rel_tol=0.15))


if __name__ == "__main__":
    unittest.main()
