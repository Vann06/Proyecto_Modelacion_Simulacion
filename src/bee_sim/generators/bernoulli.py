"""Bernoulli(p) y la Binomial construida por convolucion."""


def bernoulli(p, rng):
    """Inversa trivial sobre una acumulada de dos escalones: U < p."""
    if not 0.0 <= p <= 1.0:
        raise ValueError("p debe estar en [0, 1]")
    return 1 if rng.uniform() < p else 0


def binomial_por_convolucion(n, p, rng):
    """Binomial(n, p) como suma de n ensayos Bernoulli independientes.

    No se usa inversa binomial a proposito. En el motor n es el numero de
    flores visitadas, que cambia en cada viaje, de modo que una inversa
    obligaria a reconstruir la funcion acumulada con cada n distinto. La
    suma respeta el anidamiento X | F ~ Binomial(F, p) y deja el metodo a la
    vista. Ver docs/model.md, seccion 6.
    """
    if n < 0:
        raise ValueError("n no puede ser negativo")
    return sum(bernoulli(p, rng) for _ in range(n))
