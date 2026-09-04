"""Fuente alterna de uniformes y variables que salen directo de U(0,1)."""

import numpy as np

from .lcg import LCG


class NumpyStream:
    """Adaptador con la misma interfaz que LCG, respaldado por NumPy.

    Genera los uniformes por bloques para no pagar una llamada de NumPy por
    muestra. Se usa en la campana experimental completa, donde el LCG en
    Python puro resulta demasiado lento (decision D-10).
    """

    def __init__(self, seed=12345, bloque=100000):
        self.semilla_inicial = seed
        self._rng = np.random.default_rng(seed)
        self._bloque = int(bloque)
        self._buf = self._rng.random(self._bloque)
        self._i = 0
        self.consumidos = 0

    def uniform(self):
        if self._i >= self._bloque:
            self._buf = self._rng.random(self._bloque)
            self._i = 0
        u = float(self._buf[self._i])
        self._i += 1
        self.consumidos += 1
        return u

    def uniform_array(self, n):
        return [self.uniform() for _ in range(n)]

    def reset(self):
        self.__init__(self.semilla_inicial, self._bloque)
        return self

    @property
    def nombre(self):
        return "NumPy PCG64"


FUENTES = {"lcg": LCG, "numpy": NumpyStream}


def crear_fuente(tipo, seed):
    """Fabrica la fuente de uniformes segun configuracion.

    El YAML decide cual se usa, de modo que cambiar de fuente no obliga a
    tocar el motor.
    """
    try:
        return FUENTES[tipo](seed=seed)
    except KeyError:
        raise ValueError("fuente desconocida: %r (use 'lcg' o 'numpy')" % tipo)


def uniforme(a, b, rng):
    """U(a, b) por transformada inversa: X = a + (b - a) U."""
    if b < a:
        raise ValueError("se requiere a <= b")
    return a + (b - a) * rng.uniform()


def categorica(probabilidades, rng):
    """Inversa discreta sobre una categorica. Devuelve el indice sorteado.

    Compara U contra la acumulada. En el proyecto sortea la disponibilidad
    floral A_f, pero solo en el escenario BASE: en FLORES-BAJA y FLORES-ALTA
    el nivel se fija por configuracion y esta funcion no se llama, porque
    ahi A_f es un factor experimental y no una variable aleatoria
    (decision D-07).
    """
    total = sum(probabilidades)
    if abs(total - 1.0) > 1e-9:
        raise ValueError("las probabilidades deben sumar 1, suman %r" % total)
    u = rng.uniform()
    acumulada = 0.0
    for i, p in enumerate(probabilidades):
        acumulada += p
        if u <= acumulada:
            return i
    return len(probabilidades) - 1
