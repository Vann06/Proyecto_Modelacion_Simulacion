"""Paso 5: cuantas flores visita la abeja en este viaje.

Es la variable bisagra del modelo. F no es una metrica mas: es el contador que
dice cuantas veces se repite todo lo que ocurre en el parche. De el cuelgan la
polinizacion (un ensayo Bernoulli por flor), el nectar (una Gamma por flor) y el
tiempo de forrajeo (una espera exponencial por flor). Un error aqui daña tres
metricas del informe a la vez, y por eso es lo primero que hay que probar.

La media mu_F la fija el nivel de disponibilidad floral; ver models/environment.py.
"""

from ..generators.poisson import binomial_negativa, poisson_inversa

MODELOS = ("poisson", "negbin")


def _modelo(cfg):
    modelo = cfg["foraging"]["flower_count_model"]
    if modelo not in MODELOS:
        raise ValueError("flower_count_model debe ser uno de %s, es %r" % (MODELOS, modelo))
    return modelo


def sortear_flores(mu, cfg, rng):
    """Numero de flores visitadas en un viaje, dada la media del parche.

    Con `poisson` consume exactamente un uniforme. Con `negbin` consume los de
    la Gamma de la mezcla mas uno, porque la composicion sortea primero la media
    del viaje y despues el conteo.
    """
    if mu < 0:
        raise ValueError("mu no puede ser negativa")
    if _modelo(cfg) == "poisson":
        return poisson_inversa(mu, rng)

    forma = cfg["foraging"]["overdispersion"]
    if forma is None:
        raise ValueError(
            "flower_count_model es 'negbin' pero overdispersion es null; "
            "defina la forma r en la configuracion")
    return binomial_negativa(mu, forma, rng)


def flores_del_viaje(env, nivel, cfg, rng):
    """Encadena el paso 3 con el paso 5: el nivel del parche fija mu_F."""
    return sortear_flores(env.mu_flores(nivel), cfg, rng)


def momentos_teoricos(mu, cfg):
    """Media y varianza que debe tener el generador. Se usa en la validacion.

    La Poisson obliga a que media y varianza sean iguales. La Binomial Negativa
    agrega el termino mu^2/r, que es exactamente la variacion entre viajes
    buenos y malos que una Poisson no puede representar (decision D-08).
    """
    if _modelo(cfg) == "poisson":
        return mu, mu
    forma = cfg["foraging"]["overdispersion"]
    return mu, mu + mu ** 2 / forma
