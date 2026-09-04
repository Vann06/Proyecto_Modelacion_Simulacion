"""Poisson(mu) por inversa discreta y Binomial Negativa por composicion."""

import math

from .continuous import gamma

# Tope de mu por bloque. Por encima de este valor, math.exp(-mu) pierde
# precision y termina desbordando a cero: exp(-745) ya es 0.0 en punto
# flotante de doble precision. Con la acumulada en cero, la busqueda nunca
# termina. El Metodo B necesita Poisson(lambda * horizonte), que con los
# parametros del proyecto es Poisson(1200), asi que el caso no es hipotetico.
MU_MAX_BLOQUE = 200.0


def _dividir(mu):
    """Numero de bloques en que se parte mu para mantenerlo representable."""
    return int(mu / MU_MAX_BLOQUE) + 1


def _poisson_inversa_bloque(mu, rng):
    u = rng.uniform()
    p = math.exp(-mu)
    acumulada = p
    k = 0
    while u > acumulada:
        k += 1
        p *= mu / k
        acumulada += p
    return k


def poisson_inversa(mu, rng):
    """Inversa discreta por busqueda acumulada.

    Acumula p(0), p(0)+p(1), ... con la recurrencia p(k) = p(k-1) * mu / k y
    devuelve el primer k cuya acumulada supera U. Consume exactamente un
    uniforme por muestra, sin importar cuantas iteraciones internas haga.

    Para mu grande se aplica la propiedad de division del Poisson: la suma
    de m variables Poisson(mu/m) independientes es Poisson(mu). Eso mantiene
    cada bloque numericamente seguro, a costa de consumir m uniformes en vez
    de uno. Es una convolucion, y conviene mencionarla en el informe porque
    cambia el conteo de uniformes del Metodo B.
    """
    if mu < 0:
        raise ValueError("mu no puede ser negativa")
    if mu <= MU_MAX_BLOQUE:
        return _poisson_inversa_bloque(mu, rng)
    m = _dividir(mu)
    return sum(_poisson_inversa_bloque(mu / m, rng) for _ in range(m))


def _poisson_knuth_bloque(mu, rng):
    limite = math.exp(-mu)
    k = 0
    producto = rng.uniform()
    while producto > limite:
        k += 1
        producto *= rng.uniform()
    return k


def poisson_knuth(mu, rng):
    """Alternativa de Knuth: multiplica uniformes hasta bajar de e^(-mu).

    Se implementa para comparar tiempo de ejecucion contra la busqueda
    acumulada. A diferencia de poisson_inversa, consume un numero variable
    de uniformes, en promedio mu + 1. Usa la misma division por bloques, y
    por el mismo motivo.
    """
    if mu < 0:
        raise ValueError("mu no puede ser negativa")
    if mu <= MU_MAX_BLOQUE:
        return _poisson_knuth_bloque(mu, rng)
    m = _dividir(mu)
    return sum(_poisson_knuth_bloque(mu / m, rng) for _ in range(m))


def binomial_negativa(mu, forma, rng):
    """Binomial Negativa por composicion (mezcla Gamma-Poisson).

        lambda' ~ Gamma(forma, mu/forma)
        F       ~ Poisson(lambda')

    Con esta parametrizacion E[F] = mu y Var[F] = mu + mu^2/forma, de modo
    que el escenario mueve solo la media y `forma` controla la
    sobredispersion de manera independiente. Con forma grande se recupera la
    Poisson. Decision D-08.
    """
    if forma <= 0:
        raise ValueError("la forma debe ser positiva")
    return poisson_inversa(gamma(forma, mu / forma, rng), rng)
