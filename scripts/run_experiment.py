#!/usr/bin/env python
"""F6.4: corre un escenario o la campana completa y persiste cada replica.

Uso:
    python scripts/run_experiment.py --escenario base --n-replicas 50
    python scripts/run_experiment.py --campana --n-replicas 50

El archivo de semillas se genera una sola vez (results/runs/semillas_campana.json
por defecto) y se reutiliza despues, para que todos los escenarios se
comparen sobre la misma suerte (docs/plan_implementacion.md, F6).
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bee_sim.config import cargar
from bee_sim.experiments.scenarios import ESCENARIOS, cargar_escenario
from bee_sim.generators import crear_fuente
from bee_sim.simulation.engine import simular_jornada
from bee_sim.simulation.metrics import resumir

from _persistence import guardar_corrida


def parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--escenario", choices=sorted(ESCENARIOS), help="un solo escenario")
    grupo.add_argument("--campana", action="store_true", help="los ocho escenarios")
    parser.add_argument("--n-replicas", type=int, required=True)
    parser.add_argument("--out", default="results/runs", help="carpeta de salida")
    parser.add_argument("--semillas", default=None,
                         help="ruta al archivo de semillas (default: <out>/semillas_campana.json)")
    return parser.parse_args(argv)


def resolver_semillas(ruta, n_minimo, seed_base):
    """Lee el archivo de semillas si existe; si no, lo genera y lo persiste.

    Reutilizar el archivo existente es lo que permite comparar escenarios
    distintos sobre la misma suerte. No se regenera si ya hay suficientes.
    """
    ruta = Path(ruta)
    if ruta.is_file():
        with open(ruta, "r", encoding="utf-8") as f:
            semillas = json.load(f)["semillas"]
        if len(semillas) >= n_minimo:
            return semillas
        # el archivo existe pero se quedo corto: se extiende sin tocar las ya usadas
        faltantes = n_minimo - len(semillas)
        semillas = semillas + [seed_base + len(semillas) + i for i in range(faltantes)]
    else:
        semillas = [seed_base + i for i in range(n_minimo)]

    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"semillas": semillas}, f, indent=2)
    return semillas


def _correr_y_guardar(nombre, n_replicas, semillas, carpeta_out):
    """Repite lo que hace runner.correr_escenario pero persistiendo cada
    Jornada completa (no solo el resumen), porque el runner no toca disco."""
    cfg = cargar_escenario(nombre)
    fuente = cfg["simulation"]["rng_source"]
    for i in range(n_replicas):
        rng = crear_fuente(fuente, semillas[i])
        viajes = simular_jornada(cfg, rng, run_id=i)
        resumen = resumir(viajes, viajes.colonia, cfg)
        guardar_corrida(viajes, cfg, resumen, carpeta_out)


def main(argv=None) -> int:
    args = parsear_argumentos(argv)

    ruta_semillas = args.semillas or str(Path(args.out) / "semillas_campana.json")
    seed_base = cargar("config/base.yaml")["simulation"]["seed"]
    semillas = resolver_semillas(ruta_semillas, args.n_replicas, seed_base)

    inicio = time.perf_counter()
    if args.campana:
        for nombre in ESCENARIOS:
            _correr_y_guardar(nombre, args.n_replicas, semillas, args.out)
    else:
        _correr_y_guardar(args.escenario, args.n_replicas, semillas, args.out)
    duracion = time.perf_counter() - inicio

    n_escenarios = len(ESCENARIOS) if args.campana else 1
    print("%d replicas x %d escenario(s) en %.2f s (%.3f s/replica)"
          % (args.n_replicas, n_escenarios, duracion, duracion / (args.n_replicas * n_escenarios)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
