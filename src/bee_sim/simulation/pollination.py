"""Paso 6: cuantas de las flores visitadas quedan efectivamente polinizadas.

Cada visita es un ensayo Bernoulli independiente con probabilidad p_success.
El total se construye sumando esos ensayos, no invirtiendo una Binomial: en el
motor el numero de intentos es F, que cambia en cada viaje, y una inversa
obligaria a reconstruir la funcion acumulada con cada F distinto.

Visitar no es polinizar: de F flores visitadas se polinizan alrededor de
F * p_success, y la diferencia queda registrada en el viaje.
"""

from ..generators.bernoulli import binomial_por_convolucion


def polinizar(flores_visitadas, cfg, rng):
    """Flores efectivamente polinizadas en un viaje.

    Consume exactamente un uniforme por flor visitada.
    """
    if flores_visitadas < 0:
        raise ValueError("las flores visitadas no pueden ser negativas")
    return binomial_por_convolucion(flores_visitadas, cfg["pollination"]["p_success"], rng)


def tasa_observada(visitadas, polinizadas):
    """Proporcion de visitas que terminaron en polinizacion. Devuelve None
    cuando no hubo visitas, porque la tasa no esta definida en ese caso."""
    if visitadas == 0:
        return None
    return polinizadas / visitadas


def media_marginal_teorica(mu, cfg):
    """Media de X cuando F ~ Poisson(mu): por adelgazamiento vale mu * p.

    ADVERTENCIA para quien escriba las pruebas. Si F ~ Poisson(mu) y cada visita
    se filtra con un ensayo Bernoulli(p), la marginal de X es exactamente
    Poisson(mu * p), de modo que su media Y SU VARIANZA valen mu * p. Esa
    igualdad es la prueba de fuego y no depende de calibrar ningun parametro.

    Pero la propiedad exige un unico nivel de disponibilidad floral. En el
    escenario BASE, donde A_f se sortea por viaje, la marginal agregada es una
    mezcla de tres Poissons, que es sobredispersa y NO es Poisson. Validar el
    adelgazamiento sobre esa mezcla falla, y no porque el codigo este mal.
    """
    return mu * cfg["pollination"]["p_success"]
