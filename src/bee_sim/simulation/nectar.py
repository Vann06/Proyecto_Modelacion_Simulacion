"""Paso 7: nectar recolectado sobre las flores visitadas."""

import math
from numbers import Integral, Real

from ..generators.continuous import suma_gammas


def recolectar(flores_visitadas, escala_nectar, cfg, rng) -> float:
    """Suma una Gamma por flor, por aceptacion y rechazo (Marsaglia-Tsang).

    Se acumula sobre las visitadas, independientemente de la polinizacion
    (D-03), y flor por flor (D-04). Con cero visitas devuelve 0.0 sin consumir
    uniformes. La escala procede de Environment.escala_nectar(nivel).
    """
    if (isinstance(flores_visitadas, bool)
            or not isinstance(flores_visitadas, Integral) or flores_visitadas < 0):
        raise ValueError("flores_visitadas debe ser un entero no negativo")
    forma = cfg["nectar"]["shape"]
    for nombre, valor in (("nectar.shape", forma), ("escala_nectar", escala_nectar)):
        if (isinstance(valor, bool) or not isinstance(valor, Real)
                or not math.isfinite(valor) or valor <= 0):
            raise ValueError("%s debe ser un numero finito positivo" % nombre)
    return float(suma_gammas(forma, escala_nectar, flores_visitadas, rng))
