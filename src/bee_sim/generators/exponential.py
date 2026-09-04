"""Exponencial(lambda) por transformada inversa.

    F(t) = 1 - e^(-lambda t)
    =>    T = -ln(1 - U) / lambda

Es una de las dos inversas que el informe deriva con algebra; la otra es la
Weibull, en continuous.py. Consume exactamente un uniforme por muestra.
"""

import math


def exponencial(lam, rng):
    """Una muestra Exponencial(lam). E[T] = 1/lam, Var[T] = 1/lam^2."""
    if lam <= 0:
        raise ValueError("lambda debe ser positiva")
    return -math.log(1.0 - rng.uniform()) / lam


def exponencial_muestra(lam, n, rng):
    return [exponencial(lam, rng) for _ in range(n)]


def suma_exponenciales(lam, n, rng):
    """Convolucion de n exponenciales.

    Con n fijo esto es exactamente una Gamma(n, 1/lam). En el motor n es el
    numero de flores visitadas, que es aleatorio, asi que el resultado no es
    Gamma sino una suma aleatoria: esa es la razon por la que la duracion del
    viaje se construye y no se sortea (decision D-01).
    """
    return sum(exponencial(lam, rng) for _ in range(n))
