"""Motor espacial agregado sintético y contrato común de Proyecto 2."""
from .config import load_config, with_parameters
from .simulation import simulate

__all__ = ['simulate', 'load_config', 'with_parameters']
