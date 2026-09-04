"""Pasos 11 y 12: retorno por horizonte temporal y supervivencia por distancia."""

import math
from numbers import Real

from ..generators.bernoulli import bernoulli
from .distance import probabilidad_retorno


def _validar_numero(nombre, valor, permite_cero=False):
    """Valida un parametro deterministamente, sin consumir uniformes."""
    if (isinstance(valor, bool) or not isinstance(valor, Real)
            or not math.isfinite(valor)
            or (valor < 0 if permite_cero else valor <= 0)):
        dominio = "no negativo" if permite_cero else "positivo"
        raise ValueError("%s debe ser un numero finito %s" % (nombre, dominio))


def _probabilidad(distancia_km, cfg):
    """Evalua la logistica existente sin sortear (decision D-09)."""
    _validar_numero("distancia_km", distancia_km, permite_cero=True)
    _validar_numero("return.sensitivity", cfg["return"]["sensitivity"])
    _validar_numero("return.midpoint_km", cfg["return"]["midpoint_km"], permite_cero=True)
    try:
        return float(probabilidad_retorno(distancia_km, cfg))
    except OverflowError:
        # exp(a * (D - d0)) desborda en la cola lejana; alli p redondea a 0.
        return 0.0


def cabe_en_jornada(t_salida, duracion, cfg) -> bool:
    """Condicion determinista t_salida + duracion <= horizonte (D-09).

    Llegar exactamente al cierre cuenta como retorno dentro de la jornada.
    """
    horizonte = cfg["simulation"]["day_minutes"]
    _validar_numero("t_salida", t_salida, permite_cero=True)
    _validar_numero("duracion", duracion)
    _validar_numero("simulation.day_minutes", horizonte)
    return bool(t_salida + duracion <= horizonte)


def sobrevive_distancia(distancia_km, cfg, rng) -> bool:
    """Bernoulli(p_ret(D)) por inversa trivial, independiente del horario (D-09).

    Consume un uniforme. La probabilidad la calcula distance.
    """
    return bool(bernoulli(_probabilidad(distancia_km, cfg), rng))


def retorna(t_salida, duracion, distancia_km, cfg, rng) -> tuple[bool, float]:
    """Combina horizonte y Bernoulli por inversa trivial; devuelve (retorno, p).

    Ambas condiciones deben cumplirse (D-09). Siempre sortea la supervivencia,
    incluso fuera de horario, respetando el orden de docs/model.md y el
    consumo de un uniforme por viaje. p es p_ret(D), no se anula por horario.
    """
    cabe = cabe_en_jornada(t_salida, duracion, cfg)
    p_ret = _probabilidad(distancia_km, cfg)
    sobrevive = bool(bernoulli(p_ret, rng))
    return cabe and sobrevive, p_ret
