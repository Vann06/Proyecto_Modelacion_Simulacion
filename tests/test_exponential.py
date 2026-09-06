"""Pruebas del generador Exponencial. Ver docs/plan_implementacion.md, F9."""

import math
import unittest

import numpy as np
from scipy import stats

from bee_sim.generators.exponential import exponencial, exponencial_muestra, suma_exponenciales
from bee_sim.generators.lcg import LCG


class ExponencialTests(unittest.TestCase):
    def test_lambda_no_positiva_falla(self):
        with self.assertRaises(ValueError):
            exponencial(0.0, LCG(seed=1))
        with self.assertRaises(ValueError):
            exponencial(-1.0, LCG(seed=1))

    def test_media_y_varianza_teoricas(self):
        lam = 2.0
        rng = LCG(seed=7)
        m = np.array(exponencial_muestra(lam, 20000, rng))
        self.assertGreater(m.min(), 0.0)
        self.assertTrue(math.isclose(m.mean(), 1.0 / lam, rel_tol=0.05))
        self.assertTrue(math.isclose(m.var(), 1.0 / lam ** 2, rel_tol=0.15))

    def test_bondad_de_ajuste_ks(self):
        lam = 1.5
        rng = LCG(seed=99)
        m = np.array(exponencial_muestra(lam, 20000, rng))
        ks = stats.kstest(m, "expon", args=(0, 1.0 / lam))
        self.assertGreater(ks.pvalue, 0.01)

    def test_reproducibilidad_misma_semilla(self):
        a = exponencial_muestra(2.0, 500, LCG(seed=42))
        b = exponencial_muestra(2.0, 500, LCG(seed=42))
        self.assertEqual(a, b)

    def test_consume_exactamente_un_uniforme_por_muestra(self):
        rng = LCG(seed=3)
        exponencial_muestra(2.0, 500, rng)
        self.assertEqual(rng.consumidos, 500)

    def test_suma_exponenciales_n_cero_es_cero_sin_consumir(self):
        rng = LCG(seed=1)
        self.assertEqual(suma_exponenciales(2.0, 0, rng), 0.0)
        self.assertEqual(rng.consumidos, 0)

    def test_suma_exponenciales_media_escala_con_n(self):
        """Con n fijo, la suma de n exponenciales(lam) es Gamma(n, 1/lam),
        media n/lam (ver docstring de suma_exponenciales)."""
        rng = LCG(seed=5)
        n, lam = 10, 3.0
        muestras = [suma_exponenciales(lam, n, rng) for _ in range(5000)]
        self.assertTrue(math.isclose(np.mean(muestras), n / lam, rel_tol=0.1))


if __name__ == "__main__":
    unittest.main()
