"""Validacion y resumen deterministas de una replica, sin volver a simular."""

import math
from numbers import Integral, Real

from ..models import Trip
from .distance import tiempo_vuelo
from .return_model import cabe_en_jornada


def _exigir(condicion, mensaje):
    """Valida sin assert para conservar las comprobaciones con Python -O."""
    if not condicion:
        raise ValueError(mensaje)


def _numero(valor, minimo=0, estricto=False):
    """Comprueba un dominio numerico finito sin consumir azar."""
    return (not isinstance(valor, bool) and isinstance(valor, Real)
            and math.isfinite(valor) and (valor > minimo if estricto else valor >= minimo))


def verificar_invariantes(viajes, cfg) -> None:
    """Valida registros y secuencia temporal de una replica sin sortear (D-09).

    trip_id es unico dentro del run_id. run_id se repite en la replica y
    bee_id puede repetirse en viajes sucesivos; no puede solaparse ni salir
    otra vez despues de no retornar. Los errores se comunican como ValueError.
    """
    horizonte = cfg["simulation"]["day_minutes"]
    n_abejas = cfg["colony"]["active_bees"]
    _exigir(_numero(horizonte, estricto=True), "day_minutes debe ser finito positivo")
    _exigir(not isinstance(n_abejas, bool) and isinstance(n_abejas, Integral) and n_abejas > 0,
            "active_bees debe ser un entero positivo")
    _exigir(_numero(cfg["foraging"]["velocity_km_min"], estricto=True),
            "velocity_km_min debe ser finita positiva")
    identificadores, disponibles = set(), {}
    replica, ultima_salida = None, 0.0
    for viaje in viajes:
        _exigir(isinstance(viaje, Trip), "viajes debe contener objetos Trip")
        contexto = "viaje %r: " % viaje.trip_id
        for campo in ("run_id", "bee_id", "trip_id", "flowers_visited", "flowers_pollinated"):
            valor = getattr(viaje, campo)
            _exigir(not isinstance(valor, bool) and isinstance(valor, Integral) and valor >= 0,
                    contexto + campo + " debe ser un entero no negativo")
        _exigir(viaje.bee_id < n_abejas, contexto + "bee_id fuera de la colonia")
        if replica is None:
            replica = viaje.run_id
        _exigir(viaje.run_id == replica, "los viajes deben pertenecer a una sola replica")
        _exigir(viaje.trip_id not in identificadores, contexto + "trip_id duplicado")
        identificadores.add(viaje.trip_id)

        for campo in ("departure_time", "nectar_collected", "foraging_time_min", "return_probability"):
            _exigir(_numero(getattr(viaje, campo)), contexto + campo + " debe ser finito no negativo")
        for campo in ("distance_km", "search_time_min", "flight_time_min", "trip_duration_min"):
            _exigir(_numero(getattr(viaje, campo), estricto=True),
                    contexto + campo + " debe ser finito positivo")
        _exigir(viaje.return_probability <= 1, contexto + "return_probability debe estar en [0, 1]")
        _exigir(type(viaje.returned) is bool and type(viaje.fits_in_day) is bool,
                contexto + "returned y fits_in_day deben ser bool")
        _exigir(viaje.flower_availability in ("baja", "media", "alta"),
                contexto + "disponibilidad floral desconocida")
        # Trip.validar es el contrato existente; las comprobaciones explicitas
        # tambien cubren su contenido cuando los assert se desactivan con -O.
        try:
            viaje.validar(horizonte)
        except AssertionError as exc:
            raise ValueError(contexto + str(exc)) from exc
        _exigir(viaje.flowers_pollinated <= viaje.flowers_visited, contexto + "polinizadas > visitadas")
        _exigir((viaje.nectar_collected == 0) == (viaje.flowers_visited == 0),
                contexto + "nectar debe ser cero si y solo si no hubo visitas")
        _exigir((viaje.foraging_time_min == 0) == (viaje.flowers_visited == 0),
                contexto + "forrajeo debe ser cero si y solo si no hubo visitas")
        _exigir(viaje.trip_duration_min >= viaje.flight_time_min, contexto + "duracion menor que vuelo")
        _exigir(math.isclose(viaje.flight_time_min, tiempo_vuelo(viaje.distance_km, cfg)),
                contexto + "vuelo no coincide con 2D/V")
        _exigir(math.isclose(viaje.trip_duration_min,
                            viaje.flight_time_min + viaje.search_time_min + viaje.foraging_time_min),
                contexto + "duracion no coincide con la suma de componentes")
        cabe = cabe_en_jornada(viaje.departure_time, viaje.trip_duration_min, cfg)
        _exigir(viaje.fits_in_day == cabe, contexto + "fits_in_day contradice el horizonte")
        _exigir(not viaje.returned or cabe, contexto + "retorno fuera del horizonte")
        _exigir(not viaje.returned or viaje.return_probability > 0, contexto + "retorno con probabilidad cero")
        _exigir(not (cabe and viaje.return_probability == 1) or viaje.returned,
                contexto + "no retorno con probabilidad uno dentro del horizonte")
        _exigir(ultima_salida <= viaje.departure_time <= horizonte,
                contexto + "salidas desordenadas o fuera de la jornada")
        _exigir(viaje.departure_time >= disponibles.get(viaje.bee_id, 0.0),
                contexto + "abeja ocupada o retirada")
        ultima_salida = viaje.departure_time
        disponibles[viaje.bee_id] = (viaje.departure_time + viaje.trip_duration_min
                                     if viaje.returned else math.inf)


def _cociente(numerador, denominador):
    """Cociente determinista; None cuando el denominador es cero."""
    return numerador / denominador if denominador else None


def resumir(viajes, colonia, cfg) -> dict:
    """Agrega una replica sin generar numeros aleatorios ni escribir archivos.

    Recibe la colonia FINAL (viajes.colonia cuando procede del motor).
    Las tasas son fracciones [0, 1]; medias y tasas sin denominador son None.
    Nectar recolectado incluye todos los viajes; entregado solo los retornados.
    Duracion y distancia de ida y vuelta son planificadas, incluso en viajes
    sin retorno; no se infiere el instante de perdida ni se trunca rendimiento.

    El no retorno se particiona en fuera de jornada y fallo de distancia
    DENTRO de jornada. Fuera de jornada el registro no permite recuperar el
    Bernoulli, por lo que no se atribuye una segunda causa no observada (D-09).
    """
    viajes = list(viajes)
    verificar_invariantes(viajes, cfg)
    n = len(viajes)
    completos = sum(v.returned for v in viajes)
    fuera = sum(not v.fits_in_day for v in viajes)
    _exigir(len(colonia) == cfg["colony"]["active_bees"], "colonia no coincide con active_bees")
    _exigir(colonia.salidas_atendidas == n, "colonia no coincide con los viajes atendidos")
    _exigir(not isinstance(colonia.salidas_perdidas, bool)
            and isinstance(colonia.salidas_perdidas, Integral) and colonia.salidas_perdidas >= 0,
            "salidas_perdidas debe ser un entero no negativo")
    _exigir(colonia.viajes_completos() == completos, "colonia no coincide con los retornos")
    _exigir(len(colonia) - colonia.activas() == n - completos,
            "colonia no coincide con las abejas retiradas")
    visitadas = sum(v.flowers_visited for v in viajes)
    polinizadas = sum(v.flowers_pollinated for v in viajes)
    polinizadas_que_caben = sum(
        v.flowers_pollinated for v in viajes if v.fits_in_day
    )
    polinizadas_completos = sum(
        v.flowers_pollinated for v in viajes if v.returned
    )
    nectar = sum((v.nectar_collected for v in viajes), 0.0)
    duracion = sum((v.trip_duration_min for v in viajes), 0.0)
    distancia_ida = sum((v.distance_km for v in viajes), 0.0)
    return {
        "viajes_iniciados": n,
        "viajes_completos": completos,
        "viajes_no_retornados": n - completos,
        "no_retorno_horizonte": fuera,
        "no_retorno_distancia_en_jornada": n - completos - fuera,
        "salidas_totales": colonia.salidas_totales,
        "salidas_atendidas": colonia.salidas_atendidas,
        "salidas_perdidas": colonia.salidas_perdidas,
        "tasa_salidas_perdidas": _cociente(colonia.salidas_perdidas, colonia.salidas_totales),
        "abejas_activas_final": colonia.activas(),
        "abejas_retiradas": len(colonia) - colonia.activas(),
        "flores_visitadas": visitadas,
        "flores_polinizadas": polinizadas,
        # La metrica historica incluye el resultado planificado de todo viaje
        # iniciado. Estas variantes eliminan la ambiguedad del horizonte.
        "flores_polinizadas_viajes_que_caben": polinizadas_que_caben,
        "flores_polinizadas_viajes_completos": polinizadas_completos,
        "tasa_polinizacion": _cociente(polinizadas, visitadas),
        "nectar_recolectado_ml": nectar,
        "nectar_entregado_ml": sum((v.nectar_collected for v in viajes if v.returned), 0.0),
        "duracion_total_planificada_min": duracion,
        "duracion_media_min": _cociente(duracion, n),
        "distancia_total_planificada_km": 2.0 * distancia_ida,
        "distancia_media_ida_km": _cociente(distancia_ida, n),
        "tasa_retorno": _cociente(completos, n),
        "flores_polinizadas_por_viaje": _cociente(polinizadas, n),
        "flores_polinizadas_por_minuto_planificado": _cociente(polinizadas, duracion),
        "flores_polinizadas_por_km_planificado": _cociente(polinizadas, 2.0 * distancia_ida),
        "nectar_por_minuto_planificado_ml": _cociente(nectar, duracion),
    }
