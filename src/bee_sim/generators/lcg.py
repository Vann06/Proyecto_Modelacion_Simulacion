"""Generador congruencial lineal (LCG), la fuente base de uniformes.

    x_{n+1} = (a * x_n + c) mod m,    U = x / m

Se usa en la validacion de generadores y en la comparacion contra el
generador estandar del lenguaje. Para la campana experimental completa se
usa NumpyStream (uniform.py) por costo computacional: ver decision D-10 en
docs/decisions.md.
"""


class LCG:
    """Fuente U(0,1) reproducible.

    Los parametros por defecto son los de Numerical Recipes, con periodo
    2^32. Su debilidad conocida es la estructura de reticula, que la
    validacion busca a proposito con la autocorrelacion y el diagrama
    U_i contra U_{i+1}.
    """

    def __init__(self, seed=12345, a=1664525, c=1013904223, m=2 ** 32):
        if not 0 <= seed < m:
            raise ValueError("la semilla debe estar en [0, m)")
        self.semilla_inicial = seed
        self.estado = seed
        self.a, self.c, self.m = a, c, m
        self.consumidos = 0

    def uniform(self):
        """Devuelve el siguiente U(0,1) y lleva la cuenta del consumo."""
        self.estado = (self.a * self.estado + self.c) % self.m
        self.consumidos += 1
        return self.estado / self.m

    def uniform_array(self, n):
        return [self.uniform() for _ in range(n)]

    def reset(self):
        """Vuelve a la semilla inicial. Util para comparar metodos sobre la
        misma secuencia de uniformes."""
        self.estado = self.semilla_inicial
        self.consumidos = 0
        return self

    @property
    def nombre(self):
        return "LCG(a=%d, c=%d, m=%d)" % (self.a, self.c, self.m)
