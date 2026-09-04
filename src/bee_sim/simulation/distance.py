"""Paso 4: distancia al parche floral y el tiempo de vuelo que implica."""

from ..generators.continuous import weibull

MODELOS = ("weibull",)


def sortear_distancia(cfg, rng):
    """Distancia de la colmena al parche, SOLO DE IDA, en kilometros.

    Weibull por transformada inversa. Se eligio sobre Gamma y Lognormal
    porque es la unica de las tres con acumulada invertible en forma cerrada
    (decision D-05). El escenario mueve la escala; la forma se queda fija.
    """
    d = cfg["foraging"]["distance"]
    if d["model"] not in MODELOS:
        raise ValueError("modelo de distancia no soportado: %r" % d["model"])
    return weibull(d["shape"], d["scale"], rng)


def tiempo_vuelo(distancia_km, cfg):
    """Ida y vuelta: 2D/V. Deterministico una vez que existe la distancia.

    No consume uniformes. Es la primera de las tres piezas que arman la
    duracion del viaje; las otras dos son la busqueda y el forrajeo.
    """
    return 2.0 * distancia_km / cfg["foraging"]["velocity_km_min"]


def probabilidad_retorno(distancia_km, cfg):
    """p_ret(D) = 1 / (1 + e^(a(D - d0))), la logistica del paso 11.

    Se calcula aqui porque depende solo de la distancia, pero el volado que
    la usa vive en return_model.py. ADVERTENCIA: esta funcion es una
    construccion del modelo sin calibracion biologica; sus dos parametros son
    supuestos declarados.
    """
    import math
    r = cfg["return"]
    if r["model"] != "logistic":
        raise ValueError("modelo de retorno no soportado: %r" % r["model"])
    return 1.0 / (1.0 + math.exp(r["sensitivity"] * (distancia_km - r["midpoint_km"])))
