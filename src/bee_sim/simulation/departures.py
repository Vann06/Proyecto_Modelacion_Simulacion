"""Generacion de los tiempos de salida de la colmena.

Aqui viven los dos metodos que el proyecto compara. Ambos devuelven
exactamente el mismo objeto: una lista ordenada de tiempos de salida dentro
de [0, horizonte]. Esa equivalencia de salida es lo que los hace
comparables; si devolvieran cosas distintas, la comparacion no seria justa.
"""

from ..generators.exponential import exponencial
from ..generators.poisson import poisson_inversa


def metodo_a_interarribos(intensidad, horizonte, rng):
    """Metodo A: tiempos entre salidas Exponencial(lambda) por inversa.

    Acumula esperas hasta rebasar el horizonte. El numero total de salidas
    es una consecuencia del proceso, no una entrada.
    """
    if intensidad <= 0 or horizonte <= 0:
        raise ValueError("intensidad y horizonte deben ser positivos")
    tiempos = []
    t = 0.0
    while True:
        t += exponencial(intensidad, rng)
        if t > horizonte:
            return tiempos
        tiempos.append(t)


def metodo_b_conteo(intensidad, horizonte, rng):
    """Metodo B: conteo Poisson directo mas uniformidad condicional.

    Genera N ~ Poisson(lambda * horizonte) y despues reparte esas N salidas
    dentro del intervalo. El reparto no es un adorno: dado que ocurrieron N
    eventos en [0, T], sus tiempos se distribuyen como N uniformes
    independientes en (0, T), ordenados. Sin ese paso el metodo daria el
    conteo pero no serviria como motor, porque no diria cuando sale cada
    abeja. Decision D-06 en docs/decisions.md.
    """
    if intensidad <= 0 or horizonte <= 0:
        raise ValueError("intensidad y horizonte deben ser positivos")
    n = poisson_inversa(intensidad * horizonte, rng)
    return sorted(rng.uniform() * horizonte for _ in range(n))


METODOS = {"A": metodo_a_interarribos, "B": metodo_b_conteo}


def generar_salidas(metodo, intensidad, horizonte, rng):
    """Despacha segun configuracion (clave `generation_method` del YAML)."""
    try:
        generador = METODOS[metodo]
    except KeyError:
        raise ValueError("metodo desconocido: %r (use 'A' o 'B')" % metodo)
    return generador(intensidad, horizonte, rng)


def generar_salidas_desde_config(cfg, rng):
    """Paso 1 leyendo directo de la configuracion del escenario."""
    return generar_salidas(
        cfg["departures"]["generation_method"],
        cfg["departures"]["lambda_per_min"],
        cfg["simulation"]["day_minutes"],
        rng,
    )
