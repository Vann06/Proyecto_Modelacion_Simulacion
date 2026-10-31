"""Entidades conceptuales; no equiparar permiso de colmena con recurso floral."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FloralPatch:
    patch_id: str
    exclusive_area_m2: float
    # Cero área asignada implica cero recurso bajo la regla sintética, no falta de flores observada.


@dataclass(frozen=True)
class CandidateHiveSite:
    site_id: str
    parent_patch_id: str
    x_m: float
    y_m: float


@dataclass(frozen=True)
class Hive:
    hive_slot: int
    site_id: str
