"""Pasos 8 a 10: busqueda, forrajeo y duracion construida del viaje."""

import math
from numbers import Integral, Real

from ..generators.continuous import gamma
from ..generators.exponential import suma_exponenciales


def _validar_tiempo(nombre, valor, permite_cero=False):
    """Valida un parametro temporal deterministamente, sin consumir azar."""
    if (isinstance(valor, bool) or not isinstance(valor, Real)
            or not math.isfinite(valor)
            or (valor < 0 if permite_cero else valor <= 0)):
        dominio = "no negativo" if permite_cero else "positivo"
        raise ValueError("%s debe ser un numero finito %s" % (nombre, dominio))


def tiempo_busqueda(escala_busqueda, cfg, rng) -> float:
    """Gamma por aceptacion y rechazo (Marsaglia-Tsang), decision D-02.

    La escala procede de Environment.escala_busqueda(nivel): buscar en un
    parche pobre cuesta mas tiempo. Se genera incluso si no hubo visitas.
    """
    forma = cfg["foraging"]["search_shape"]
    _validar_tiempo("foraging.search_shape", forma)
    _validar_tiempo("escala_busqueda", escala_busqueda)
    return float(gamma(forma, escala_busqueda, rng))


def tiempo_forrajeo(flores_visitadas, cfg, rng) -> float:
    """Convolucion de una exponencial por visita, generada por inversa (D-01).

    La configuracion da la MEDIA; el generador recibe su inversa, la tasa.
    Con cero visitas devuelve 0.0 y no consume uniformes.
    """
    if (isinstance(flores_visitadas, bool)
            or not isinstance(flores_visitadas, Integral) or flores_visitadas < 0):
        raise ValueError("flores_visitadas debe ser un entero no negativo")
    media = cfg["foraging"]["time_per_flower_mean"]
    _validar_tiempo("foraging.time_per_flower_mean", media)
    return float(suma_exponenciales(1.0 / media, flores_visitadas, rng))


def duracion_total(t_vuelo, t_busqueda, t_forrajeo) -> float:
    """Suma determinista de los tres componentes, sin sortear una Gamma (D-01).

    t_vuelo ya incluye ida y vuelta, segun distance.tiempo_vuelo. El forrajeo
    puede ser cero cuando F = 0; la busqueda debe ser positiva.
    """
    _validar_tiempo("t_vuelo", t_vuelo, permite_cero=True)
    _validar_tiempo("t_busqueda", t_busqueda)
    _validar_tiempo("t_forrajeo", t_forrajeo, permite_cero=True)
    total = float(t_vuelo + t_busqueda + t_forrajeo)
    _validar_tiempo("duracion_total", total)
    return total
