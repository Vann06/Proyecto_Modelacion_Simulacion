"""Escritura del trio de archivos de una corrida (F5.1).

Unico lugar donde se decide el formato de guardado en disco. Lo usan tanto
run_simulation.py como run_experiment.py para no duplicar la logica de
escritura. Nadie en src/bee_sim toca disco salvo config.py; este modulo
vive en scripts/ a proposito, por la misma regla.
"""

import csv
import json
from pathlib import Path

import yaml

from bee_sim.models import CAMPOS


def siguiente_run_id(carpeta) -> int:
    """Escanea 'run_*.csv' en carpeta y devuelve el siguiente numero libre.

    Empieza en 1 si la carpeta no existe o no hay corridas previas. No
    reutiliza numeros aunque se hayan borrado corridas intermedias.
    """
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        return 1
    numeros = []
    for archivo in carpeta.glob("run_*.csv"):
        try:
            numeros.append(int(archivo.stem.split("_")[1]))
        except (IndexError, ValueError):
            continue
    return max(numeros, default=0) + 1


def guardar_corrida(viajes, cfg, resumen, carpeta, run_numero=None) -> dict:
    """Escribe run_XXXX.csv, _config.yaml y _summary.json en carpeta.

    run_numero se autocalcula con siguiente_run_id si no se indica. Devuelve
    las tres rutas escritas para que el llamador las reporte o las use en
    export_results.py. No genera ni consume azar; solo serializa lo que ya
    se calculo.
    """
    viajes = list(viajes)  # falla aqui, antes de tocar disco, si no es iterable
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    if run_numero is None:
        run_numero = siguiente_run_id(carpeta)
    nombre = "run_%04d" % run_numero

    ruta_csv = carpeta / (nombre + ".csv")
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for viaje in viajes:
            escritor.writerow(viaje.as_dict())

    ruta_config = carpeta / (nombre + "_config.yaml")
    with open(ruta_config, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    ruta_summary = carpeta / (nombre + "_summary.json")
    with open(ruta_summary, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    return {"csv": ruta_csv, "config": ruta_config, "summary": ruta_summary}
