#!/usr/bin/env python
"""F5.3: consolida los summary.json de results/runs en una tabla unica.

No vuelve a simular nada; solo lee lo que run_simulation.py o
run_experiment.py ya dejaron en disco.

Uso:
    python scripts/export_results.py --runs results/runs --out results/tables
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yaml


def parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--runs", default="results/runs", help="carpeta con las corridas")
    parser.add_argument("--out", default="results/tables", help="carpeta de salida")
    parser.add_argument("--nombre", default="resumen_corridas.csv",
                         help="nombre del CSV consolidado")
    return parser.parse_args(argv)


def recolectar_filas(carpeta_runs):
    """Une cada *_summary.json con su _config.yaml. Orden estable por nombre."""
    filas = []
    for ruta_summary in sorted(Path(carpeta_runs).glob("run_*_summary.json")):
        nombre = ruta_summary.stem.replace("_summary", "")
        ruta_config = ruta_summary.parent / (nombre + "_config.yaml")
        with open(ruta_summary, "r", encoding="utf-8") as f:
            resumen = json.load(f)
        escenario = None
        if ruta_config.is_file():
            with open(ruta_config, "r", encoding="utf-8") as f:
                escenario = (yaml.safe_load(f) or {}).get("_origen")
        filas.append({"run": nombre, "escenario": escenario, **resumen})
    return filas


def main(argv=None) -> int:
    args = parsear_argumentos(argv)
    filas = recolectar_filas(args.runs)

    carpeta_out = Path(args.out)
    carpeta_out.mkdir(parents=True, exist_ok=True)
    ruta_salida = carpeta_out / args.nombre

    if filas:
        columnas = list(filas[0].keys())
    else:
        columnas = ["run", "escenario"]

    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        for fila in filas:
            escritor.writerow(fila)

    print("tabla consolidada: %s (%d corridas)" % (ruta_salida, len(filas)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
