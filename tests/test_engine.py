"""Pruebas de F4 compatibles con unittest y pytest; no requieren escrituras."""

import copy
from contextlib import ExitStack
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from bee_sim.config import cargar
from bee_sim.generators import crear_fuente
from bee_sim.simulation import engine
from bee_sim.simulation.metrics import resumir, verificar_invariantes


CONFIG = Path(__file__).resolve().parents[1] / "config"


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cargar(CONFIG / "base.yaml")

    def test_reproducibilidad_todos_los_escenarios_fuentes_y_metodos(self):
        total = 0
        for ruta in sorted(CONFIG.glob("*.yaml")):
            for fuente in ("lcg", "numpy"):
                for metodo in ("A", "B"):
                    with self.subTest(escenario=ruta.name, fuente=fuente, metodo=metodo):
                        cfg = cargar(ruta)
                        cfg["departures"]["generation_method"] = metodo
                        original = copy.deepcopy(cfg)
                        rng1 = crear_fuente(fuente, 2026)
                        rng2 = crear_fuente(fuente, 2026)
                        a = engine.simular_jornada(cfg, rng1, run_id=7)
                        b = engine.simular_jornada(cfg, rng2, run_id=7)
                        self.assertIsInstance(a, list)
                        self.assertGreater(len(a), 0)
                        self.assertEqual(a, b)
                        self.assertEqual(rng1.consumidos, rng2.consumidos)
                        self.assertIsNot(a.colonia, b.colonia)
                        self.assertTrue(all(v.run_id == 7 for v in a))
                        self.assertEqual([v.trip_id for v in a], list(range(len(a))))
                        verificar_invariantes(a, cfg)
                        resumen = resumir(a, a.colonia, cfg)
                        self.assertEqual(resumen, resumir(b, b.colonia, cfg))
                        self.assertEqual(resumen["salidas_totales"],
                                         resumen["salidas_atendidas"] + resumen["salidas_perdidas"])
                        self.assertEqual(cfg, original)
                        total += len(a) + len(b)
        self.assertGreater(total, 0)

    def test_saturacion_reutilizacion_y_retiro(self):
        self.cfg["colony"]["active_bees"] = 1
        self.cfg["simulation"]["day_minutes"] = 10
        self.cfg["foraging"]["velocity_km_min"] = 1
        with ExitStack() as stack:
            stack.enter_context(patch.object(engine, "generar_salidas_desde_config", return_value=[0, 1, 5, 6, 10]))
            for nombre, valor in (("sortear_distancia", 1.0), ("flores_del_viaje", 2),
                                  ("polinizar", 1), ("recolectar", .4),
                                  ("tiempo_busqueda", 1.0), ("tiempo_forrajeo", 2.0)):
                stack.enter_context(patch.object(engine, nombre, return_value=valor))
            retorno = stack.enter_context(patch.object(engine, "retorna", side_effect=[(True, .5), (False, .5)]))
            rng = crear_fuente("lcg", 2026)
            viajes = engine.simular_jornada(self.cfg, rng)
        self.assertEqual([v.departure_time for v in viajes], [0, 5])
        self.assertEqual([v.bee_id for v in viajes], [0, 0])
        self.assertTrue(viajes[1].fits_in_day)  # 5 + 5 == cierre
        self.assertEqual(retorno.call_count, 2)
        self.assertEqual(rng.consumidos, 2)  # solo disponibilidad de viajes atendidos
        self.assertEqual(viajes.colonia.salidas_totales, 5)
        self.assertEqual(viajes.colonia.salidas_perdidas, 3)
        self.assertEqual(viajes.colonia.viajes_completos(), 1)
        self.assertFalse(viajes.colonia.bees[0].activa)

    def test_cero_salidas(self):
        rng = crear_fuente("lcg", 2026)
        with patch.object(engine, "generar_salidas_desde_config", return_value=[]):
            viajes = engine.simular_jornada(self.cfg, rng)
        self.assertEqual(viajes, [])
        self.assertEqual(rng.consumidos, 0)
        self.assertEqual(viajes.colonia.activas(), 90)
        self.assertEqual(resumir(viajes, viajes.colonia, self.cfg)["salidas_totales"], 0)

    def test_orden_de_generacion_documentado(self):
        eventos = []

        def registrar(nombre, valor):
            def paso(*args):
                eventos.append(nombre)
                return valor
            return paso

        with ExitStack() as stack:
            stack.enter_context(patch.object(engine, "generar_salidas_desde_config",
                                             side_effect=registrar("salida", [0.0])))
            stack.enter_context(patch.object(engine.Environment, "sortear_nivel",
                                             side_effect=registrar("nivel", "media")))
            for nombre, valor in (("sortear_distancia", 1.0), ("flores_del_viaje", 2),
                                  ("polinizar", 1), ("recolectar", .4),
                                  ("tiempo_busqueda", 1.0), ("tiempo_forrajeo", 2.0),
                                  ("retorna", (True, .5))):
                stack.enter_context(patch.object(engine, nombre, side_effect=registrar(nombre, valor)))
            engine.simular_jornada(self.cfg, crear_fuente("lcg", 2026))
        self.assertEqual(eventos, ["salida", "nivel", "sortear_distancia", "flores_del_viaje",
                                  "polinizar", "recolectar", "tiempo_busqueda", "tiempo_forrajeo", "retorna"])

    def test_salida_sin_flores_y_fuera_del_horizonte(self):
        with ExitStack() as stack:
            stack.enter_context(patch.object(engine, "generar_salidas_desde_config", return_value=[600.0]))
            stack.enter_context(patch.object(engine, "flores_del_viaje", return_value=0))
            viajes = engine.simular_jornada(self.cfg, crear_fuente("lcg", 2026))
        v = viajes[0]
        self.assertEqual((v.flowers_pollinated, v.nectar_collected, v.foraging_time_min), (0, 0.0, 0.0))
        self.assertGreater(v.search_time_min, 0)
        self.assertFalse(v.returned)
        self.assertFalse(v.fits_in_day)
        self.assertEqual(viajes.colonia.activas(), 89)

    def test_binomial_negativa_integrada(self):
        self.cfg["foraging"]["flower_count_model"] = "negbin"
        self.cfg["foraging"]["overdispersion"] = 3.0
        a = engine.simular_jornada(self.cfg, crear_fuente("lcg", 2026))
        b = engine.simular_jornada(self.cfg, crear_fuente("lcg", 2026))
        self.assertEqual(a, b)
        verificar_invariantes(a, self.cfg)

    def test_rng_no_se_reinicia_y_run_id_no_cambia_el_azar(self):
        a = crear_fuente("lcg", 19)
        b = crear_fuente("lcg", 19)
        a.uniform()
        b.uniform()
        viajes_a = engine.simular_jornada(self.cfg, a, 2)
        viajes_b = engine.simular_jornada(self.cfg, b, 3)
        self.assertEqual(a.consumidos, b.consumidos)
        self.assertEqual([{**v.as_dict(), "run_id": 0} for v in viajes_a],
                         [{**v.as_dict(), "run_id": 0} for v in viajes_b])
        self.assertNotEqual(viajes_a, engine.simular_jornada(self.cfg, crear_fuente("lcg", 19), 2))

    def test_entradas_invalidas_fallan_antes_de_sortear(self):
        casos = [("simulation", "day_minutes"), ("departures", "lambda_per_min"),
                 ("foraging", "velocity_km_min"), ("colony", "active_bees")]
        for seccion, campo in casos:
            for valor in (0, -1, math.inf, math.nan, True, "3", None):
                with self.subTest(campo=campo, valor=valor):
                    cfg = copy.deepcopy(self.cfg)
                    cfg[seccion][campo] = valor
                    rng = crear_fuente("lcg", 2026)
                    with self.assertRaises(ValueError):
                        engine.simular_jornada(cfg, rng)
                    self.assertEqual(rng.consumidos, 0)
        for run_id in (-1, True, 1.5, "1"):
            with self.assertRaises(ValueError):
                engine.simular_jornada(self.cfg, crear_fuente("lcg", 2026), run_id)
        with self.assertRaises(ValueError):
            engine.simular_jornada(self.cfg, None)
        with self.assertRaises(ValueError):
            engine.simular_jornada({}, crear_fuente("lcg", 2026))


if __name__ == "__main__":
    unittest.main()
