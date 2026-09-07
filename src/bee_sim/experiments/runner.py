"""F6.3: corre un escenario o la campana completa sobre varias replicas.

Solo calcula: no lee ni escribe archivos, no imprime. Las semillas llegan
ya resueltas desde el script que llama (run_experiment.py), que es quien
decide si el archivo de semillas se genera o se reutiliza.
"""

from numbers import Integral

from ..generators import crear_fuente
from ..simulation.engine import simular_jornada
from ..simulation.metrics import resumir
from .scenarios import ESCENARIOS, cargar_escenario


def _validar_replicas(n_replicas, semillas):
    if isinstance(n_replicas, bool) or not isinstance(n_replicas, Integral) or n_replicas < 1:
        raise ValueError("n_replicas debe ser un entero positivo")
    if len(semillas) < n_replicas:
        raise ValueError(
            "se pidieron %d replicas pero solo hay %d semillas" % (n_replicas, len(semillas))
        )


def correr_escenario(nombre, n_replicas, semillas) -> list[dict]:
    """Corre n_replicas jornadas del escenario 'nombre', una por semilla.

    Devuelve una lista de resumenes (metrics.resumir), en el mismo orden
    que las semillas recibidas. No persiste las Jornada completas: quien
    necesite los viajes crudos debe correrlos aparte con run_simulation.py.
    """
    _validar_replicas(n_replicas, semillas)
    cfg = cargar_escenario(nombre)
    fuente = cfg["simulation"]["rng_source"]
    resumenes = []
    for i in range(n_replicas):
        rng = crear_fuente(fuente, semillas[i])
        viajes = simular_jornada(cfg, rng, run_id=i)
        resumenes.append(resumir(viajes, viajes.colonia, cfg))
    return resumenes


def correr_campana(n_replicas, semillas) -> dict:
    """Corre los doce escenarios de ESCENARIOS con el mismo conjunto de semillas.

    Devuelve {nombre_escenario: [resumenes...]}. Las semillas se pasan tal
    cual a cada escenario, para que la comparacion entre escenarios corra
    sobre la misma suerte.
    """
    return {nombre: correr_escenario(nombre, n_replicas, semillas) for nombre in ESCENARIOS}
