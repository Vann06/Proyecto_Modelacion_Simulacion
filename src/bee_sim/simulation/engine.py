"""Motor de una jornada: coordina los pasos sin implementar distribuciones."""

import math
from numbers import Integral, Real

from ..config import validar
from ..models import Colony, Environment, Trip
from .departures import generar_salidas_desde_config
from .distance import sortear_distancia, tiempo_vuelo
from .flowers import flores_del_viaje
from .nectar import recolectar
from .pollination import polinizar
from .return_model import cabe_en_jornada, retorna
from .trip_duration import duracion_total, tiempo_busqueda, tiempo_forrajeo
from .metrics import verificar_invariantes


class Jornada(list):
    """Lista de Trip con la colonia final para resumir salidas y saturacion.

    Se comporta como una lista normal (iteracion, igualdad, indices). La
    colonia pertenece a esta corrida; nunca se guarda estado global.
    """

    def __init__(self, colonia):
        super().__init__()
        self.colonia = colonia


def simular_jornada(cfg, rng, run_id=0) -> list[Trip]:
    """Ejecuta el orden de docs/model.md usando los generadores existentes.

    Las salidas usan A o B; cada viaje encadena disponibilidad, distancia,
    flores, polinizacion, nectar, busqueda, forrajeo y retorno (D-01 a D-09).
    Solo las salidas atendidas consumen azar para un viaje. Una abeja que no
    retorna queda retirada el resto del dia. El rng se recibe sin reiniciarlo.

    Devuelve una Jornada, subclase de list[Trip]. Para las metricas:
    resumir(viajes, viajes.colonia, cfg). No lee archivos ni imprime.
    """
    try:
        validar(cfg)
    except KeyError as exc:
        raise ValueError(str(exc)) from exc
    if isinstance(run_id, bool) or not isinstance(run_id, Integral) or run_id < 0:
        raise ValueError("run_id debe ser un entero no negativo")
    n = cfg["colony"]["active_bees"]
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 1:
        raise ValueError("colony.active_bees debe ser un entero positivo")
    for nombre, valor in (
        ("simulation.day_minutes", cfg["simulation"]["day_minutes"]),
        ("departures.lambda_per_min", cfg["departures"]["lambda_per_min"]),
        ("foraging.velocity_km_min", cfg["foraging"]["velocity_km_min"]),
    ):
        if (isinstance(valor, bool) or not isinstance(valor, Real)
                or not math.isfinite(valor) or valor <= 0):
            raise ValueError("%s debe ser un numero finito positivo" % nombre)
    if not math.isfinite(cfg["simulation"]["day_minutes"] * cfg["departures"]["lambda_per_min"]):
        raise ValueError("lambda_per_min * day_minutes debe ser finito")
    if not callable(getattr(rng, "uniform", None)):
        raise ValueError("rng debe proporcionar un metodo uniform()")

    colonia = Colony.desde_config(cfg)
    entorno = Environment.desde_config(cfg)
    viajes = Jornada(colonia)
    for t_salida in generar_salidas_desde_config(cfg, rng):
        abeja = colonia.buscar_libre(t_salida)
        if abeja is None:
            continue
        nivel = entorno.sortear_nivel(rng)
        distancia = sortear_distancia(cfg, rng)
        flores = flores_del_viaje(entorno, nivel, cfg, rng)
        polinizadas = polinizar(flores, cfg, rng)
        nectar = recolectar(flores, entorno.escala_nectar(nivel), cfg, rng)
        busqueda = tiempo_busqueda(entorno.escala_busqueda(nivel), cfg, rng)
        forrajeo = tiempo_forrajeo(flores, cfg, rng)
        vuelo = tiempo_vuelo(distancia, cfg)
        duracion = duracion_total(vuelo, busqueda, forrajeo)
        returned, p_ret = retorna(t_salida, duracion, distancia, cfg, rng)
        viajes.append(Trip(
            run_id=int(run_id), bee_id=abeja.bee_id, trip_id=len(viajes),
            departure_time=t_salida, flower_availability=nivel,
            distance_km=distancia, flowers_visited=flores,
            flowers_pollinated=polinizadas, nectar_collected=nectar,
            search_time_min=busqueda, foraging_time_min=forrajeo,
            flight_time_min=vuelo, trip_duration_min=duracion,
            return_probability=p_ret, returned=returned,
            fits_in_day=cabe_en_jornada(t_salida, duracion, cfg),
        ))
        if returned:
            abeja.ocupar_hasta(t_salida + duracion)
        else:
            abeja.retirar()

    verificar_invariantes(viajes, cfg)
    return viajes
