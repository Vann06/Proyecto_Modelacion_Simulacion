"""Pruebas del generador Poisson. Ver docs/plan_implementacion.md, F9.

El caso de mu grande no es opcional: es el bug que ya se encontro una vez
(math.exp(-mu) desborda a cero para mu > ~745) y esta prueba evita que
vuelva. mu = 1200 es exactamente lo que pide el Metodo B con lambda=2 y
horizonte=600 (config/base.yaml).
"""

import math
import unittest

import numpy as np

from bee_sim.analysis.validation import validar_poisson
from bee_sim.generators.lcg import LCG
from bee_sim.generators.poisson import MU_MAX_BLOQUE, _dividir, poisson_inversa, poisson_knuth


class PoissonTests(unittest.TestCase):
    def test_mu_negativa_falla(self):
        with self.assertRaises(ValueError):
            poisson_inversa(-1.0, LCG(seed=1))
        with self.assertRaises(ValueError):
            poisson_knuth(-1.0, LCG(seed=1))

    def test_media_y_varianza_teoricas(self):
        mu = 8.0
        rng = LCG(seed=23)
        m = np.array([poisson_inversa(mu, rng) for _ in range(20000)])
        self.assertTrue(math.isclose(m.mean(), mu, rel_tol=0.05))
        self.assertTrue(math.isclose(m.var(), mu, rel_tol=0.15))

    def test_mu_grande_no_se_cuelga_ni_desborda(self):
        mu = 1200.0
        valor = poisson_inversa(mu, LCG(seed=1))
        self.assertIsInstance(valor, int)
        self.assertGreater(valor, 0)

        muestra = np.array([poisson_inversa(mu, LCG(seed=100 + i)) for i in range(300)])
        self.assertTrue(math.isclose(muestra.mean(), mu, rel_tol=0.1))

    def test_poisson_knuth_tambien_soporta_mu_grande(self):
        mu = 1200.0
        valor = poisson_knuth(mu, LCG(seed=1))
        self.assertIsInstance(valor, int)
        self.assertGreater(valor, 0)

    def test_division_en_bloques_no_cambia_la_media(self):
        """Poisson(mu) partido en m bloques de Poisson(mu/m) debe seguir
        teniendo media mu, por la propiedad de division del Poisson."""
        mu = 3 * MU_MAX_BLOQUE + 50
        self.assertGreater(_dividir(mu), 1)
        muestra = np.array([poisson_inversa(mu, LCG(seed=200 + i)) for i in range(400)])
        self.assertTrue(math.isclose(muestra.mean(), mu, rel_tol=0.05))

    def test_poisson_knuth_misma_media_que_inversa(self):
        mu = 6.0
        a = np.array([poisson_inversa(mu, LCG(seed=1000 + i)) for i in range(3000)])
        b = np.array([poisson_knuth(mu, LCG(seed=2000 + i)) for i in range(3000)])
        self.assertTrue(math.isclose(a.mean(), b.mean(), rel_tol=0.1))

    def test_reproducibilidad_misma_semilla(self):
        a = poisson_inversa(8.0, LCG(seed=42))
        b = poisson_inversa(8.0, LCG(seed=42))
        self.assertEqual(a, b)

    def test_bondad_de_ajuste_chi2(self):
        """Reusa la validacion oficial en vez de reimplementar chi2 a mano."""
        resultado = validar_poisson(5.0, LCG(seed=77), n=20000)
        self.assertGreater(resultado["p_valor"], 0.01)


if __name__ == "__main__":
    unittest.main()
