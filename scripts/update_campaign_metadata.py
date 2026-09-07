#!/usr/bin/env python
"""Actualiza una campana creada por una version anterior.

No cambia los CSV. Corrige los YAML y agrega a los resumenes las metricas de
polinizacion por alcance temporal. Por seguridad solo escribe con ``--apply`` y
debe ejecutarse cuando la campana haya terminado.
"""

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import yaml


def parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", default="results/runs")
    parser.add_argument("--n-replicas", type=int, required=True)
    parser.add_argument("--semillas", default=None)
    parser.add_argument(
        "--apply", action="store_true",
        help="actualiza YAML y resumenes; sin esto solo informa",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parsear_argumentos(argv)
    carpeta = Path(args.runs)
    ruta_semillas = Path(args.semillas) if args.semillas else carpeta / "semillas_campana.json"
    with open(ruta_semillas, "r", encoding="utf-8") as archivo:
        semillas = json.load(archivo)["semillas"]
    if len(semillas) < args.n_replicas:
        raise ValueError("el archivo no contiene suficientes semillas")

    def numero_corrida(ruta):
        return int(ruta.name.split("_")[1])

    por_escenario = {}
    for ruta in sorted(carpeta.glob("run_*_config.yaml"), key=numero_corrida):
        with open(ruta, "r", encoding="utf-8") as archivo:
            cfg = yaml.safe_load(archivo) or {}
        escenario = Path(cfg.get("_origen", "")).stem
        if not escenario:
            raise ValueError(f"{ruta} no contiene _origen")
        por_escenario.setdefault(escenario, []).append((ruta, cfg))

    seleccion = {}
    for escenario, elementos in por_escenario.items():
        if len(elementos) < args.n_replicas:
            raise ValueError(
                f"{escenario} solo tiene {len(elementos)} configuraciones; "
                f"se esperaban al menos {args.n_replicas}"
            )
        # Si hay campañas anteriores, se actualiza únicamente el bloque más
        # reciente, igual que hacen los notebooks.
        seleccion[escenario] = elementos[-args.n_replicas:]

    preparados = []
    for escenario, elementos in seleccion.items():
        for indice, (ruta, cfg) in enumerate(elementos):
            semilla = int(semillas[indice])
            cfg.setdefault("simulation", {})["seed"] = semilla
            cfg["simulation"]["replications"] = int(args.n_replicas)
            fecha = datetime.fromtimestamp(ruta.stat().st_mtime, timezone.utc).isoformat()
            cfg["_run_metadata"] = {
                "scenario": escenario,
                "replica_index": indice,
                "replications": int(args.n_replicas),
                "seed": semilla,
                "generated_at_utc": fecha,
                "recovered_from_legacy_output": True,
            }
            base = ruta.name.removesuffix("_config.yaml")
            ruta_csv = ruta.parent / f"{base}.csv"
            ruta_summary = ruta.parent / f"{base}_summary.json"
            if not ruta_csv.is_file() or not ruta_summary.is_file():
                raise ValueError(f"falta CSV o resumen compañero de {ruta}")
            with open(ruta_summary, "r", encoding="utf-8") as archivo:
                resumen = json.load(archivo)
            pol_que_caben = 0
            pol_completos = 0
            with open(ruta_csv, newline="", encoding="utf-8") as archivo:
                for fila in csv.DictReader(archivo):
                    polinizadas = int(fila["flowers_pollinated"])
                    if fila["fits_in_day"].lower() == "true":
                        pol_que_caben += polinizadas
                    if fila["returned"].lower() == "true":
                        pol_completos += polinizadas
            resumen["flores_polinizadas_viajes_que_caben"] = pol_que_caben
            resumen["flores_polinizadas_viajes_completos"] = pol_completos
            preparados.append((ruta, cfg, ruta_summary, resumen))

    print("configuraciones encontradas:", len(preparados))
    print("por escenario:", {k: len(v) for k, v in sorted(seleccion.items())})
    if not args.apply:
        print("modo de revision: no se escribio nada; agregue --apply despues de verificar")
        return 0
    for ruta, cfg, ruta_summary, resumen in preparados:
        with open(ruta, "w", encoding="utf-8") as archivo:
            yaml.safe_dump(cfg, archivo, allow_unicode=True, sort_keys=False)
        with open(ruta_summary, "w", encoding="utf-8") as archivo:
            json.dump(resumen, archivo, indent=2, ensure_ascii=False)
    print("configuraciones y resumenes actualizados:", len(preparados))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
