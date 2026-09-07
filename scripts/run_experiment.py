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
import copy
from datetime import datetime, timezone
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bee_sim.config import cargar
from bee_sim.experiments.scenarios import ESCENARIOS, cargar_escenario
from bee_sim.generators import crear_fuente
from bee_sim.simulation.engine import simular_jornada
from bee_sim.simulation.metrics import resumir

from _persistence import guardar_corrida, siguiente_run_id


def parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--escenario", choices=sorted(ESCENARIOS), help="un solo escenario")
    grupo.add_argument("--campana", action="store_true", help="los doce escenarios")
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
            usadas = semillas[:n_minimo]
            if len(usadas) > 1 and max(usadas) - min(usadas) < n_minimo * 100:
                warnings.warn(
                    "el archivo existente usa semillas muy cercanas; se conserva "
                    "para no invalidar corridas en curso, pero conviene generar una "
                    "campana nueva con semillas dispersas",
                    RuntimeWarning,
                )
            return semillas
        # El archivo existe pero se quedo corto: se extiende sin tocar las ya usadas.
        generador = np.random.default_rng(seed_base)
        candidatas = generador.integers(0, 2 ** 31, size=n_minimo).tolist()
        semillas = semillas + candidatas[len(semillas):]
    else:
        # Evita flujos correlacionados al inicializar repetidamente un LCG con
        # semillas consecutivas.
        semillas = np.random.default_rng(seed_base).integers(
            0, 2 ** 31, size=n_minimo
        ).tolist()

    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"semillas": semillas}, f, indent=2)
    return semillas


def _correr_y_guardar(nombre, n_replicas, semillas, carpeta_out):
    """Repite lo que hace runner.correr_escenario pero persistiendo cada
    Jornada completa (no solo el resumen), porque el runner no toca disco."""
    cfg = cargar_escenario(nombre)
    fuente = cfg["simulation"]["rng_source"]
    # El numero de corrida se resuelve UNA sola vez. Dejar que guardar_corrida
    # lo autocalculara hacia que siguiente_run_id reescaneara la carpeta en cada
    # replica, con costo cuadratico en el numero de corridas: medido, la campana
    # pasaba de 0.25 s a 1.26 s por replica al llegar a 166 archivos.
    primero = siguiente_run_id(carpeta_out)
    for i in range(n_replicas):
        semilla = int(semillas[i])
        cfg_corrida = copy.deepcopy(cfg)
        cfg_corrida["simulation"]["seed"] = semilla
        cfg_corrida["simulation"]["replications"] = int(n_replicas)
        cfg_corrida["_run_metadata"] = {
            "scenario": nombre,
            "replica_index": i,
            "replications": int(n_replicas),
            "seed": semilla,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        rng = crear_fuente(fuente, semilla)
        viajes = simular_jornada(cfg_corrida, rng, run_id=i)
        resumen = resumir(viajes, viajes.colonia, cfg_corrida)
        guardar_corrida(
            viajes, cfg_corrida, resumen, carpeta_out,
            run_numero=primero + i,
        )


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
