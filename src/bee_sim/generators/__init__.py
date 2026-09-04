"""Generadores de variables aleatorias.

Regla de este paquete: aqui no hay logica de abejas. Un generador no sabe
que significa la muestra que produce. Toda funcion recibe `rng` como ultimo
argumento, donde `rng` es cualquier objeto con un metodo uniform().
"""

from .bernoulli import bernoulli, binomial_por_convolucion
from .continuous import gamma, normal_polar, normal_rechazo, suma_gammas, weibull
from .exponential import exponencial, exponencial_muestra, suma_exponenciales
from .lcg import LCG
from .poisson import binomial_negativa, poisson_inversa, poisson_knuth
from .uniform import NumpyStream, categorica, crear_fuente, uniforme

__all__ = [
    "LCG", "NumpyStream", "crear_fuente", "uniforme", "categorica",
    "exponencial", "exponencial_muestra", "suma_exponenciales",
    "poisson_inversa", "poisson_knuth", "binomial_negativa",
    "bernoulli", "binomial_por_convolucion",
    "normal_polar", "normal_rechazo", "gamma", "suma_gammas", "weibull",
]
