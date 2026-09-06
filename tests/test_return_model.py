"""Pruebas del modelo de retorno. Ver F9 en el plan.

Las dos condiciones del retorno se prueban por separado (decision D-09):
`cabe_en_jornada` es puramente determinista dado t_salida y duracion;
`sobrevive_distancia` es Bernoulli(p_ret(D)) e independiente del horario;
`retorna` exige que ambas se cumplan a la vez, y siempre sortea la
supervivencia aunque el viaje ya no quepa en la jornada.
"""

import math
import unittest

import numpy as np

from bee_sim.generators.lcg import LCG
from bee_sim.simulation.distance import probabilidad_retorno
from bee_sim.simulation.return_model import cabe_en_jornada, retorna, sobrevive_distancia

CFG_BASE = {
    "simulation": {"day_minutes": 100.0},
    "return": {"model": "logistic", "sensitivity": 1.2, "midpoint_km": 4.0},
}


class CabeEnJornadaTests(unittest.TestCase):
    def test_determinista_dentro_del_horizonte(self):
        self.assertTrue(cabe_en_jornada(10.0, 20.0, CFG_BASE))

    def test_llegar_exacto_al_cierre_cuenta_como_dentro(self):
        self.assertTrue(cabe_en_jornada(80.0, 20.0, CFG_BASE))

    def test_fuera_del_horizonte(self):
        self.assertFalse(cabe_en_jornada(90.0, 20.0, CFG_BASE))

    def test_no_consume_uniformes(self):
        # cabe_en_jornada ni siquiera recibe rng: si esto compila y corre,
        # ya es la prueba de que es puramente determinista.
        self.assertIsInstance(cabe_en_jornada(0.0, 1.0, CFG_BASE), bool)

    def test_parametros_invalidos_fallan(self):
        with self.assertRaises(ValueError):
            cabe_en_jornada(-1.0, 10.0, CFG_BASE)
        with self.assertRaises(ValueError):
            cabe_en_jornada(0.0, 0.0, CFG_BASE)
        with self.assertRaises(ValueError):
            cabe_en_jornada(0.0, 10.0, {"simulation": {"day_minutes": 0.0}})


class SobreviveDistanciaTests(unittest.TestCase):
    def test_reproducibilidad_misma_semilla(self):
        a = sobrevive_distancia(3.0, CFG_BASE, LCG(seed=42))
        b = sobrevive_distancia(3.0, CFG_BASE, LCG(seed=42))
        self.assertEqual(a, b)

    def test_consume_exactamente_un_uniforme(self):
        rng = LCG(seed=1)
        sobrevive_distancia(3.0, CFG_BASE, rng)
        self.assertEqual(rng.consumidos, 1)

    def test_tasa_empirica_coincide_con_p_ret(self):
        """La tasa de exito de sobrevive_distancia debe acercarse a
        probabilidad_retorno(D, cfg), que es lo que consume por dentro."""
        for distancia in (1.0, 4.0, 8.0):
            with self.subTest(distancia_km=distancia):
                p_teorica = probabilidad_retorno(distancia, CFG_BASE)
                rng = LCG(seed=123)
                exitos = sum(sobrevive_distancia(distancia, CFG_BASE, rng) for _ in range(4000))
                self.assertTrue(math.isclose(exitos / 4000, p_teorica, abs_tol=0.03))

    def test_probabilidad_decrece_con_la_distancia(self):
        cercana = probabilidad_retorno(0.5, CFG_BASE)
        lejana = probabilidad_retorno(20.0, CFG_BASE)
        self.assertGreater(cercana, lejana)


class RetornaTests(unittest.TestCase):
    def test_devuelve_tupla_booleano_y_probabilidad(self):
        returned, p_ret = retorna(0.0, 1.0, 3.0, CFG_BASE, LCG(seed=1))
        self.assertIsInstance(returned, bool)
        self.assertTrue(0.0 <= p_ret <= 1.0)

    def test_exige_ambas_condiciones_a_la_vez(self):
        """Con distancia 0 y midpoint muy lejano, p_ret es practicamente 1:
        la unica razon para no retornar debe ser el horizonte."""
        cfg = {
            "simulation": {"day_minutes": 50.0},
            "return": {"model": "logistic", "sensitivity": 1.0, "midpoint_km": 100.0},
        }
        # Cabe en la jornada: con p_ret ~ 1 casi siempre retorna.
        exitos = sum(retorna(0.0, 10.0, 0.0, cfg, LCG(seed=i))[0] for i in range(200))
        self.assertGreater(exitos, 190)

        # No cabe en la jornada: nunca retorna, aunque p_ret siga siendo ~1.
        for i in range(50):
            returned, p_ret = retorna(45.0, 10.0, 0.0, cfg, LCG(seed=i))
            self.assertFalse(returned)
            self.assertGreater(p_ret, 0.99)

    def test_siempre_sortea_la_supervivencia_incluso_fuera_de_horario(self):
        """El Bernoulli se consume aunque el viaje no quepa en la jornada
        (un uniforme por viaje, sin importar el resultado de cabe_en_jornada)."""
        rng_a = LCG(seed=1)
        rng_b = LCG(seed=1)
        retorna(90.0, 20.0, 3.0, CFG_BASE, rng_a)  # no cabe
        sobrevive_distancia(3.0, CFG_BASE, rng_b)
        self.assertEqual(rng_a.consumidos, rng_b.consumidos)

    def test_p_ret_no_se_anula_por_el_horario(self):
        _, p_ret_dentro = retorna(0.0, 10.0, 3.0, CFG_BASE, LCG(seed=1))
        _, p_ret_fuera = retorna(99.0, 10.0, 3.0, CFG_BASE, LCG(seed=1))
        self.assertEqual(p_ret_dentro, p_ret_fuera)

    def test_reproducibilidad_misma_semilla(self):
        a = retorna(10.0, 5.0, 3.0, CFG_BASE, LCG(seed=42))
        b = retorna(10.0, 5.0, 3.0, CFG_BASE, LCG(seed=42))
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
