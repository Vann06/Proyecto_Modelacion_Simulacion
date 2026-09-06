"""F6.1: catalogo de escenarios y su carga. Solo mapea nombre -> YAML.

No reimplementa la carga: delega en config.cargar, que ya resuelve extends
y valida. Aqui no se lee nada que config.py no sepa leer.
"""

from pathlib import Path

from ..config import cargar

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"

ESCENARIOS = {
    "base": CONFIG_DIR / "base.yaml",
    "bees_high": CONFIG_DIR / "bees_high.yaml",
    "bees_low": CONFIG_DIR / "bees_low.yaml",
    "combined": CONFIG_DIR / "combined.yaml",
    "distance_far": CONFIG_DIR / "distance_far.yaml",
    "distance_near": CONFIG_DIR / "distance_near.yaml",
    "flowers_high": CONFIG_DIR / "flowers_high.yaml",
    "flowers_low": CONFIG_DIR / "flowers_low.yaml",
    "lambda_high": CONFIG_DIR / "lambda_high.yaml",
    "lambda_low": CONFIG_DIR / "lambda_low.yaml",
    "pollination_high": CONFIG_DIR / "pollination_high.yaml",
    "pollination_low": CONFIG_DIR / "pollination_low.yaml",
}


def cargar_escenario(nombre) -> dict:
    """Carga la config de un escenario por su nombre corto.

    ValueError con la lista de nombres validos si nombre no esta en
    ESCENARIOS. No cachea: cada llamada relee el YAML, igual que config.cargar.
    """
    try:
        ruta = ESCENARIOS[nombre]
    except KeyError:
        raise ValueError(
            "escenario desconocido: %r (validos: %s)"
            % (nombre, ", ".join(sorted(ESCENARIOS)))
        )
    return cargar(ruta)
