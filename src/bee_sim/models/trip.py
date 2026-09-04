"""El registro de un viaje. Sus campos son las columnas del CSV de resultados.

Cada replica escribe una fila por viaje, no solo el resumen. De este archivo
salen todas las tablas y todas las figuras del informe, y por eso guardarlo
completo no es opcional: una grafica que no se puede reconstruir desde los
datos crudos es un dato que nadie puede verificar.
"""

from dataclasses import asdict, dataclass, fields


@dataclass
class Trip:
    run_id: int
    bee_id: int
    trip_id: int
    departure_time: float
    flower_availability: str
    distance_km: float
    flowers_visited: int = 0
    flowers_pollinated: int = 0
    nectar_collected: float = 0.0
    search_time_min: float = 0.0
    foraging_time_min: float = 0.0
    flight_time_min: float = 0.0
    trip_duration_min: float = 0.0
    return_probability: float = 0.0
    returned: bool = False
    fits_in_day: bool = True

    def as_dict(self):
        return asdict(self)

    def as_row(self):
        return [getattr(self, c) for c in CAMPOS]

    def validar(self, horizonte):
        """Invariantes que deben cumplirse en todos los viajes de toda corrida."""
        assert self.flowers_pollinated <= self.flowers_visited, "polinizadas > visitadas"
        assert self.nectar_collected >= 0.0, "nectar negativo"
        assert self.distance_km > 0.0, "distancia no positiva"
        assert self.departure_time <= horizonte, "salida despues del cierre"
        assert self.trip_duration_min >= self.flight_time_min, "duracion menor que el vuelo"
        return True


CAMPOS = [f.name for f in fields(Trip)]
