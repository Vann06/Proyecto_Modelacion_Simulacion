"""La colonia: la fila de forrajeras y el conteo de salidas atendidas."""

from .bee import Bee


class Colony:
    """Guarda las abejas y responde la pregunta del paso 2.

    La asignacion es determinista a proposito: se toma la primera abeja libre,
    no una al azar. Sortearla consumiria uniformes sin agregar realismo y
    haria mas dificil reproducir una corrida paso a paso.
    """

    def __init__(self, n_abejas):
        if n_abejas < 1:
            raise ValueError("la colonia necesita al menos una abeja")
        self.bees = [Bee(bee_id=i) for i in range(n_abejas)]
        self.salidas_atendidas = 0
        self.salidas_perdidas = 0

    @classmethod
    def desde_config(cls, cfg):
        return cls(cfg["colony"]["active_bees"])

    def buscar_libre(self, t):
        """Primera abeja con available_at <= t, o None si no hay ninguna.

        Devolver None no es un error: es la salida perdida, y contarlas es uno
        de los resultados del modelo.
        """
        for abeja in self.bees:
            if abeja.esta_libre(t):
                self.salidas_atendidas += 1
                return abeja
        self.salidas_perdidas += 1
        return None

    def activas(self):
        return sum(1 for b in self.bees if b.activa)

    def ocupadas(self, t):
        return sum(1 for b in self.bees if b.activa and not b.esta_libre(t))

    def viajes_completos(self):
        return sum(b.completed_trips for b in self.bees)

    @property
    def salidas_totales(self):
        return self.salidas_atendidas + self.salidas_perdidas

    def __len__(self):
        return len(self.bees)
