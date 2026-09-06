"""Pruebas de los dos metodos de generacion de salidas. Ver F9 en el plan."""

import math
import unittest

import numpy as np

from bee_sim.generators.lcg import LCG
from bee_sim.simulation.departures import (
    generar_salidas,
    generar_salidas_desde_config,
    metodo_a_interarribos,
    metodo_b_conteo,
)

LAMBDA = 2.0
HORIZONTE = 600.0
METODOS = (metodo_a_interarribos, metodo_b_conteo)


class DeparturesTests(unittest.TestCase):
    def test_salidas_ordenadas_y_dentro_del_horizonte(self):
        for metodo in METODOS:
            with self.subTest(metodo=metodo.__name__):
                tiempos = metodo(LAMBDA, HORIZONTE, LCG(seed=1))
                self.assertEqual(tiempos, sorted(tiempos))
                self.assertTrue(all(0.0 <= t <= HORIZONTE for t in tiempos))

    def test_parametros_invalidos_fallan(self):
        for metodo in METODOS:
            with self.subTest(metodo=metodo.__name__):
                with self.assertRaises(ValueError):
                    metodo(0.0, HORIZONTE, LCG(seed=1))
                with self.assertRaises(ValueError):
                    metodo(LAMBDA, 0.0, LCG(seed=1))
                with self.assertRaises(ValueError):
                    metodo(-1.0, HORIZONTE, LCG(seed=1))

    def test_reproducibilidad_misma_semilla(self):
        for metodo in METODOS:
            with self.subTest(metodo=metodo.__name__):
                a = metodo(LAMBDA, HORIZONTE, LCG(seed=42))
                b = metodo(LAMBDA, HORIZONTE, LCG(seed=42))
                self.assertEqual(a, b)

    def test_horizonte_cero_o_intensidad_minuscula_no_produce_salidas_fuera_de_rango(self):
        tiempos_a = metodo_a_interarribos(0.001, 1.0, LCG(seed=1))
        tiempos_b = metodo_b_conteo(0.001, 1.0, LCG(seed=1))
        self.assertTrue(all(0.0 <= t <= 1.0 for t in tiempos_a))
        self.assertTrue(all(0.0 <= t <= 1.0 for t in tiempos_b))

    def test_cantidad_de_salidas_cerca_de_lambda_por_horizonte(self):
        """Semillas dispersas: ver la advertencia en analysis/comparison.py
        sobre por que semillas consecutivas sesgan el Metodo B."""
        semillas = np.random.default_rng(0).integers(0, 2 ** 31, size=300)
        for metodo in METODOS:
            with self.subTest(metodo=metodo.__name__):
                conteos = [len(metodo(LAMBDA, HORIZONTE, LCG(seed=int(s)))) for s in semillas]
                self.assertTrue(math.isclose(np.mean(conteos), LAMBDA * HORIZONTE, rel_tol=0.05))

    def test_generar_salidas_despacha_por_nombre(self):
        a = generar_salidas("A", LAMBDA, HORIZONTE, LCG(seed=1))
        b = metodo_a_interarribos(LAMBDA, HORIZONTE, LCG(seed=1))
        self.assertEqual(a, b)
        with self.assertRaises(ValueError):
            generar_salidas("Z", LAMBDA, HORIZONTE, LCG(seed=1))

    def test_generar_salidas_desde_config_lee_las_llaves_correctas(self):
        cfg = {
            "departures": {"generation_method": "A", "lambda_per_min": LAMBDA},
            "simulation": {"day_minutes": HORIZONTE},
        }
        a = generar_salidas_desde_config(cfg, LCG(seed=1))
        b = metodo_a_interarribos(LAMBDA, HORIZONTE, LCG(seed=1))
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
