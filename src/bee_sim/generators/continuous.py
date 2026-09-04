"""Variables continuas: las que no tienen inversa cerrada, mas la Weibull."""

import math


def normal_polar(mu, sigma, rng):
    """Normal(mu, sigma^2) por el metodo polar de Marsaglia.

    Sortea puntos en el cuadrado [-1,1]^2 y descarta los que caen fuera del
    circulo unitario, lo que ya es aceptacion y rechazo, y transforma el que
    sobrevive. Consume 2 uniformes por intento y acepta con probabilidad
    pi/4 (0.785), asi que gasta unos 2.55 uniformes por muestra.

    El motor no modela ninguna variable con Normal, pero la necesita porque
    el generador Gamma la usa por dentro.
    """
    while True:
        u1 = 2.0 * rng.uniform() - 1.0
        u2 = 2.0 * rng.uniform() - 1.0
        s = u1 * u1 + u2 * u2
        if 0.0 < s < 1.0:
            return mu + sigma * u1 * math.sqrt(-2.0 * math.log(s) / s)


def normal_rechazo(mu, sigma, rng):
    """Normal(mu, sigma^2) por aceptacion y rechazo con envolvente Exp(1).

    El motor no la usa. Se conserva para la comparacion secundaria de
    metodos (polar contra rechazo) en analysis/comparison.py.
    """
    while True:
        y = -math.log(rng.uniform())
        if rng.uniform() <= math.exp(-0.5 * (y - 1.0) ** 2):
            z = y if rng.uniform() < 0.5 else -y
            return mu + sigma * z


def gamma(forma, escala, rng):
    """Gamma(forma, escala) por aceptacion y rechazo (Marsaglia y Tsang).

    La acumulada de la Gamma es la funcion gamma incompleta y no se puede
    invertir en forma cerrada, por eso va por rechazo. Para forma < 1 se
    aplica el truco de aumento: se genera con forma+1 y se multiplica por
    U^(1/forma), que es una composicion.

    Es el generador mas caro del motor: unos 4.5 uniformes por muestra. En
    un viaje de 10 flores, el nectar se lleva mas de la mitad del consumo
    total de numeros aleatorios.
    """
    if forma <= 0 or escala <= 0:
        raise ValueError("forma y escala deben ser positivas")
    if forma < 1.0:
        return gamma(forma + 1.0, escala, rng) * rng.uniform() ** (1.0 / forma)
    d = forma - 1.0 / 3.0
    c = 1.0 / math.sqrt(9.0 * d)
    while True:
        x = normal_polar(0.0, 1.0, rng)
        v = (1.0 + c * x) ** 3
        if v <= 0.0:
            continue
        u = rng.uniform()
        if math.log(u) < 0.5 * x * x + d - d * v + d * math.log(v):
            return d * v * escala


def suma_gammas(forma, escala, n, rng):
    """Convolucion de n Gammas. Devuelve 0.0 cuando n = 0.

    Asi se genera el nectar: flor por flor sobre las visitadas. Generarlo
    como una sola Gamma con forma proporcional a n fallaria con n = 0
    (decision D-04).
    """
    return sum(gamma(forma, escala, rng) for _ in range(n))


def weibull(forma, escala, rng):
    """Weibull(forma, escala) por transformada inversa.

        F(x) = 1 - e^(-(x/escala)^forma)
        =>    X = escala * (-ln(1 - U))^(1/forma)

    Segunda inversa derivada con algebra del informe. Se eligio sobre Gamma
    y Lognormal justamente porque es la unica de las tres invertible en
    forma cerrada (decision D-05). Con forma = 1 se reduce a una
    Exponencial(1/escala), lo que sirve de prueba de humo.
    """
    if forma <= 0 or escala <= 0:
        raise ValueError("forma y escala deben ser positivas")
    return escala * (-math.log(1.0 - rng.uniform())) ** (1.0 / forma)
