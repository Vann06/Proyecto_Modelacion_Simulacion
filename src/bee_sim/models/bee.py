"""Estado de una forrajera. Es el paso 2 del flujo."""

from dataclasses import dataclass

RETIRADA = float("inf")


@dataclass
class Bee:
    """Una abeja no guarda su historia, solo cuando vuelve a estar disponible.

    `available_at` es el unico dato que sobrevive de un viaje al siguiente, y
    por lo tanto el unico acoplamiento entre viajes de toda la simulacion. De
    ese campo sale la saturacion: si todas las abejas tienen available_at por
    delante del reloj, la salida se pierde.
    """

    bee_id: int
    available_at: float = 0.0
    completed_trips: int = 0

    def esta_libre(self, t):
        return self.available_at <= t

    def ocupar_hasta(self, t):
        """La abeja regreso: vuelve a la fila y suma un viaje completo."""
        self.available_at = t
        self.completed_trips += 1

    def retirar(self):
        """La abeja no regreso: sale de la fuerza de forrajeo por el resto
        del dia. No se elimina de la lista para que los identificadores no se
        recorran entre replicas."""
        self.available_at = RETIRADA

    @property
    def activa(self):
        return self.available_at != RETIRADA
