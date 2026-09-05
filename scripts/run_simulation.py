#!/usr/bin/env python
"""F5.2: corre una jornada y la deja en disco (CSV + config + summary).

Uso:
    python scripts/run_simulation.py --config config/base.yaml --seed 2026

Reproducir una corrida guardada usando solo su _config.yaml:
    python scripts/run_simulation.py --config results/runs/run_0001_config.yaml
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bee_sim.config import cargar
from bee_sim.generators import crear_fuente
from bee_sim.simulation.engine import simular_jornada
from bee_sim.simulation.metrics import resumir

from _persistence import guardar_corrida


def parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--config", required=True, help="ruta al YAML del escenario")
    parser.add_argument("--seed", type=int, default=None,
                         help="sobreescribe simulation.seed sin tocar el YAML")
    parser.add_argument("--out", default="results/runs", help="carpeta de salida")
    parser.add_argument("--run-id", type=int, default=0,
                         help="run_id que llevan los Trip generados (no el numero de archivo)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parsear_argumentos(argv)

    try:
        cfg = cargar(args.config)
    except (OSError, ValueError, KeyError) as exc:
        print("error cargando %r: %s" % (args.config, exc), file=sys.stderr)
        return 1

    if args.seed is not None:
        cfg["simulation"]["seed"] = args.seed

    try:
        rng = crear_fuente(cfg["simulation"]["rng_source"], cfg["simulation"]["seed"])
        viajes = simular_jornada(cfg, rng, run_id=args.run_id)
        resumen = resumir(viajes, viajes.colonia, cfg)
    except ValueError as exc:
        print("error simulando: %s" % exc, file=sys.stderr)
        return 1

    rutas = guardar_corrida(viajes, cfg, resumen, args.out)
    print("corrida guardada:")
    for etiqueta, ruta in rutas.items():
        print("  %s: %s" % (etiqueta, ruta))
    return 0


if __name__ == "__main__":
    sys.exit(main())
