"""Lectura de campanas guardadas en disco.

La disposicion canonica es una carpeta plana (``results/runs``) con el trio
CSV/configuracion/resumen de cada replica. El lector tambien acepta la antigua
disposicion con una subcarpeta por escenario para no invalidar resultados ya
generados.
"""

import json
from pathlib import Path

import yaml


def _clave_corrida(ruta):
    try:
        numero = int(ruta.name.split("_")[1])
    except (IndexError, ValueError):
        numero = -1
    return str(ruta.parent), numero, ruta.name


def _escenario_de_config(ruta_config, carpeta):
    if ruta_config.is_file():
        with open(ruta_config, "r", encoding="utf-8") as archivo:
            cfg = yaml.safe_load(archivo) or {}
        metadata = cfg.get("_run_metadata", {})
        escenario = metadata.get("scenario")
        if escenario:
            return escenario, cfg
        origen = cfg.get("_origen")
        if origen:
            return Path(origen).stem, cfg
        return None, cfg
    # Compatibilidad con results/campana/<escenario>/run_XXXX.*.
    return carpeta.name, {}


def cargar_resumenes(carpeta, ultimos_por_escenario=None):
    """Devuelve resumenes y agrega escenario/semilla desde su configuracion.

    ``ultimos_por_escenario`` evita mezclar una campana nueva con corridas
    antiguas que ya existieran en la misma carpeta plana.
    """
    carpeta = Path(carpeta)
    filas = []
    for ruta in sorted(carpeta.rglob("run_*_summary.json"), key=_clave_corrida):
        nombre = ruta.stem.removesuffix("_summary")
        ruta_config = ruta.parent / (nombre + "_config.yaml")
        escenario, cfg = _escenario_de_config(ruta_config, ruta.parent)
        with open(ruta, "r", encoding="utf-8") as archivo:
            fila = json.load(archivo)
        fila["escenario"] = escenario
        if cfg:
            fila["semilla"] = cfg.get("simulation", {}).get("seed")
            fila["replicas_configuradas"] = cfg.get("simulation", {}).get("replications")
        filas.append(fila)
    if ultimos_por_escenario is None:
        return filas
    if ultimos_por_escenario < 1:
        raise ValueError("ultimos_por_escenario debe ser positivo")
    grupos = {}
    for fila in filas:
        grupos.setdefault(fila["escenario"], []).append(fila)
    return [
        fila
        for grupo in grupos.values()
        for fila in grupo[-ultimos_por_escenario:]
    ]


def csvs_por_escenario(carpeta, escenario, ultimos=None):
    """Localiza CSV de un escenario en disposiciones planas o anidadas."""
    carpeta = Path(carpeta)
    encontrados = []
    for ruta_csv in sorted(carpeta.rglob("run_*.csv"), key=_clave_corrida):
        ruta_config = ruta_csv.parent / (ruta_csv.stem + "_config.yaml")
        encontrado, _ = _escenario_de_config(ruta_config, ruta_csv.parent)
        if encontrado == escenario:
            encontrados.append(ruta_csv)
    if ultimos is not None:
        if ultimos < 1:
            raise ValueError("ultimos debe ser positivo")
        encontrados = encontrados[-ultimos:]
    return encontrados
