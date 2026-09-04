"""Metricas contrastadas con una replica pequena calculada a mano."""

import copy
from dataclasses import replace
import json
import math
from pathlib import Path
import unittest

from bee_sim.config import cargar
from bee_sim.models import Colony, Trip
from bee_sim.simulation.metrics import resumir, verificar_invariantes


CONFIG = Path(__file__).resolve().parents[1] / "config"


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cargar(CONFIG / "base.yaml")
        self.cfg["simulation"]["day_minutes"] = 20
        self.cfg["colony"]["active_bees"] = 2
        self.cfg["foraging"]["velocity_km_min"] = 1
        primero = Trip(4, 0, 0, 0.0, "media", 1.0, 2, 1, .4, 1.0, 2.0, 2.0, 5.0, .5, True, True)
        segundo = replace(primero, bee_id=1, trip_id=1, departure_time=1.0,
                          flowers_visited=4, flowers_pollinated=3, nectar_collected=.8, returned=False)
        tercero = replace(primero, trip_id=2, departure_time=18.0, flowers_visited=0,
                          flowers_pollinated=0, nectar_collected=0.0, foraging_time_min=0.0,
                          trip_duration_min=3.0, returned=False, fits_in_day=False)
        self.viajes = [primero, segundo, tercero]
        self.colonia = Colony(2)
        self.colonia.buscar_libre(0).ocupar_hasta(5)
        self.colonia.buscar_libre(1).retirar()
        self.colonia.buscar_libre(2)
        self.colonia.buscar_libre(18).retirar()
        self.colonia.buscar_libre(19)

    def test_resumen_con_valores_conocidos(self):
        r = resumir(self.viajes, self.colonia, self.cfg)
        esperados = {
            "viajes_iniciados": 3, "viajes_completos": 1, "viajes_no_retornados": 2,
            "no_retorno_horizonte": 1, "no_retorno_distancia_en_jornada": 1,
            "salidas_totales": 5, "salidas_atendidas": 3, "salidas_perdidas": 2,
            "tasa_salidas_perdidas": .4, "abejas_activas_final": 0, "abejas_retiradas": 2,
            "flores_visitadas": 6, "flores_polinizadas": 4, "tasa_polinizacion": 4/6,
            "nectar_recolectado_ml": 1.2, "nectar_entregado_ml": .4,
            "duracion_total_planificada_min": 13, "duracion_media_min": 13/3,
            "distancia_total_planificada_km": 6, "distancia_media_ida_km": 1,
            "tasa_retorno": 1/3, "flores_polinizadas_por_viaje": 4/3,
            "flores_polinizadas_por_minuto_planificado": 4/13,
            "flores_polinizadas_por_km_planificado": 4/6,
            "nectar_por_minuto_planificado_ml": 1.2/13,
        }
        self.assertEqual(set(r), set(esperados))
        for campo, valor in esperados.items():
            with self.subTest(campo=campo):
                self.assertAlmostEqual(r[campo], valor)
        json.dumps(r, allow_nan=False)

    def test_resumen_vacio_sin_division_por_cero(self):
        r = resumir([], Colony(2), self.cfg)
        self.assertEqual(r["viajes_iniciados"], 0)
        self.assertEqual(r["nectar_recolectado_ml"], 0.0)
        self.assertEqual(r["abejas_activas_final"], 2)
        for campo in ("tasa_retorno", "tasa_polinizacion", "duracion_media_min",
                      "tasa_salidas_perdidas", "nectar_por_minuto_planificado_ml"):
            self.assertIsNone(r[campo])
        json.dumps(r, allow_nan=False)

    def test_invariantes_permiten_reutilizacion_de_abeja(self):
        self.assertIsNone(verificar_invariantes(self.viajes, self.cfg))
        self.assertIsNone(verificar_invariantes([], self.cfg))

    def test_identificadores_duplicados_y_replicas_mezcladas(self):
        for cambio in ({"trip_id": 0}, {"run_id": 5}, {"bee_id": 2},
                       {"trip_id": -1}, {"run_id": True}, {"bee_id": 1.5}):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                verificar_invariantes([self.viajes[0], replace(self.viajes[1], **cambio)], self.cfg)

    def test_viajes_solapados_y_abejas_retiradas(self):
        for cambio in ({"departure_time": 2.0, "fits_in_day": True}, {"bee_id": 1}):
            with self.subTest(cambio=cambio), self.assertRaisesRegex(ValueError, "ocupada o retirada"):
                verificar_invariantes(self.viajes[:2] + [replace(self.viajes[2], **cambio)], self.cfg)

    def test_registros_invalidos(self):
        cambios = [
            {"flowers_pollinated": 3}, {"flowers_visited": -1}, {"flowers_visited": 2.5},
            {"nectar_collected": 0}, {"nectar_collected": -1}, {"nectar_collected": math.nan},
            {"foraging_time_min": 0}, {"search_time_min": 0}, {"distance_km": 0},
            {"distance_km": math.inf}, {"flight_time_min": 3}, {"trip_duration_min": 10},
            {"departure_time": -1}, {"departure_time": 21}, {"return_probability": 1.1},
            {"return_probability": 0}, {"returned": 1}, {"fits_in_day": False},
            {"flower_availability": "desconocido"},
            {"return_probability": 1, "returned": False},
        ]
        for cambio in cambios:
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                verificar_invariantes([replace(self.viajes[0], **cambio)], self.cfg)
        with self.assertRaises(ValueError):
            verificar_invariantes([object()], self.cfg)
        with self.assertRaises(ValueError):
            verificar_invariantes(self.viajes[::-1], self.cfg)

    def test_colonia_ajena_y_contadores_inconsistentes(self):
        with self.assertRaises(ValueError):
            resumir(self.viajes, Colony(2), self.cfg)
        colonia = copy.deepcopy(self.colonia)
        colonia.salidas_perdidas = -1
        with self.assertRaises(ValueError):
            resumir(self.viajes, colonia, self.cfg)

    def test_no_modifica_entradas(self):
        cfg = copy.deepcopy(self.cfg)
        viajes = copy.deepcopy(self.viajes)
        bees = copy.deepcopy(self.colonia.bees)
        a = resumir(self.viajes, self.colonia, self.cfg)
        b = resumir(iter(self.viajes), self.colonia, self.cfg)
        self.assertEqual(a, b)
        self.assertEqual(self.cfg, cfg)
        self.assertEqual(self.viajes, viajes)
        self.assertEqual(self.colonia.bees, bees)


if __name__ == "__main__":
    unittest.main()
