"""Estructuras del sistema. Aqui viven los datos, no la logica del motor."""

from .bee import Bee
from .colony import Colony
from .environment import Environment
from .trip import CAMPOS, Trip

__all__ = ["Bee", "Colony", "Environment", "Trip", "CAMPOS"]
