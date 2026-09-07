#!/usr/bin/env python
"""F7: valida los generadores y compara los metodos del proyecto.

Empaqueta lo que `notebooks/01_generator_validation.ipynb` ya corrio y
verifico a mano (9 de 9 validaciones con p > 0.05), y agrega lo que al
notebook le faltaba: tiempo de ejecucion por generador y la comparacion
formal de M-A contra M-B y de polar contra rechazo.

Uso:
    PYTHONPATH=src python scripts/validate_generators.py
    PYTHONPATH=src python scripts/validate_generators.py --config config/base.yaml --n 20000

No corre el motor de simulacion. Los parametros que valida se leen de la
configuracion cuando existe una correspondencia directa (lambda de salidas,
forma y escala de la distancia, mu_flores y search_scale del nivel medio,
p_success de polinizacion); los que no tienen correspondencia exacta en
config/base.yaml (el numero de ensayos de la Binomial de prueba, la forma de
la Binomial Negativa de referencia) se documentan en el propio codigo como
valores de referencia, no como parametros del modelo real.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bee_sim import config as cfgmod
from bee_sim.analysis import comparison as C
from bee_sim.analysis import validation as V
from bee_sim.generators import LCG, poisson_knuth

# Semillas fijas para que esta corrida reproduzca lo que el notebook 01 ya
# valido. Cambiarlas es valido, pero entonces hay que volver a ejecutar y
# revisar el notebook para que ambos cuenten la misma historia.
SEMILLA_UNIFORME = 2026
SEMILLA_CONTINUAS = 11
SEMILLA_DISCRETAS = 23
SEMILLA_ADELGAZAMIENTO = 31


def _con_tiempo(funcion, *args, **kwargs):
    inicio = time.perf_counter()
    resultado = funcion(*args, **kwargs)
    resultado["tiempo_seg"] = time.perf_counter() - inicio
    return resultado


def correr_validaciones(cfg, n):
    """Las nueve validaciones, en el mismo orden y con las mismas semillas
    que el notebook 01. Devuelve la lista de resultados, cada uno con su
    tiempo de ejecucion agregado."""
    lam = cfg["departures"]["lambda_per_min"]
    dist = cfg["foraging"]["distance"]
    nivel_medio = cfg["environment"]["levels"]["media"]
    p_success = cfg["pollination"]["p_success"]

    resultados = []

    resultados.append(_con_tiempo(V.validar_uniforme, LCG(seed=SEMILLA_UNIFORME), n=n))

    r = LCG(seed=SEMILLA_CONTINUAS)
    resultados.append(_con_tiempo(V.validar_exponencial, lam, r, n=n))
    resultados.append(_con_tiempo(V.validar_weibull, dist["shape"], dist["scale"], r, n=n))
    # Gamma del tiempo de busqueda en disponibilidad media: search_shape es
    # fijo en foraging, search_scale lo fija el nivel del entorno.
    resultados.append(_con_tiempo(
        V.validar_gamma, cfg["foraging"]["search_shape"], nivel_medio["search_scale"], r, n=n
    ))

    r = LCG(seed=SEMILLA_DISCRETAS)
    # Flores visitadas en disponibilidad media, Poisson por los dos metodos.
    resultados.append(_con_tiempo(V.validar_poisson, nivel_medio["mu_flowers"], r, n=n))
    resultados.append(_con_tiempo(
        V.validar_poisson, nivel_medio["mu_flowers"], r, n=n, generador=poisson_knuth
    ))
    # F fijo de referencia para la Binomial: en el motor F es aleatorio (no
    # hay un "numero de flores" unico), 10 es solo un valor de prueba para
    # ejercitar el generador con la p_success real de la configuracion.
    resultados.append(_con_tiempo(V.validar_binomial, 10, p_success, r, n=n))
    # La Binomial Negativa no esta activa en base.yaml (flower_count_model
    # es 'poisson', overdispersion es null). forma=3.0 es un valor de
    # referencia para validar el generador de todos modos, no el que usaria
    # un escenario con flower_count_model: negbin.
    resultados.append(_con_tiempo(
        V.validar_binomial_negativa, nivel_medio["mu_flowers"], 3.0, r, n=n
    ))

    resultados.append(_con_tiempo(
        V.validar_adelgazamiento, nivel_medio["mu_flowers"], p_success,
        LCG(seed=SEMILLA_ADELGAZAMIENTO), n=n
    ))

    return resultados


def tabla_para_informe(resultados):
    """Aplana los resultados a la forma que pide el informe:
    generador | n | media y error | prueba de ajuste | p-valor | tiempo."""
    filas = []
    for r in resultados:
        media = r.get("media")
        media_teo = r.get("media_teorica")
        if media is not None and media_teo not in (None, 0):
            error_pct = abs(media - media_teo) / abs(media_teo) * 100.0
        else:
            error_pct = None
        filas.append({
            "generador": r["generador"],
            "n": r["n"],
            "media": media,
            "media_teorica": media_teo,
            "error_relativo_pct": error_pct,
            "prueba": r["prueba"],
            "estadistico": r["estadistico"],
            "p_valor": r["p_valor"],
            "tiempo_seg": r["tiempo_seg"],
        })
    return filas


def imprimir_tabla(filas):
    encabezado = (
        f"{'Generador':<44} {'n':>7} {'Prueba':>7} {'Estadistico':>12} "
        f"{'p-valor':>9} {'Error%':>8} {'t (s)':>8}"
    )
    print(encabezado)
    print("-" * len(encabezado))
    for f in filas:
        err = f"{f['error_relativo_pct']:.3f}" if f["error_relativo_pct"] is not None else "-"
        print(
            f"{f['generador']:<44} {f['n']:7d} {f['prueba']:>7} "
            f"{f['estadistico']:12.4f} {f['p_valor']:9.4f} {err:>8} {f['tiempo_seg']:8.4f}"
        )
    print("-" * len(encabezado))
    malos = [f for f in filas if f["p_valor"] <= 0.05]
    print(f"{len(filas)} generadores validados, {len(malos)} con p <= 0.05")
    if malos:
        print("REVISAR:", ", ".join(f["generador"] for f in malos))


def imprimir_comparacion_salidas(comp):
    print("\n=== Comparacion M-A vs M-B (salidas de la colmena) ===")
    print(f"lambda = {comp['lambda_per_min']} / min, horizonte = {comp['horizonte_min']} min")
    for nombre in ("A", "B"):
        r = comp[nombre]
        print(
            f"  Metodo {nombre}: salidas={r['salidas_media']:.2f} (sd={r['salidas_sd']:.2f}, "
            f"teorica={r['salidas_teorica']:.1f})  KS_p={r['interarribos_ks_pvalor']:.4f}  "
            f"uniformes~{r['uniformes_media']:.1f}  tiempo={r['tiempo_total_seg']:.4f}s"
        )
    c = comp["comparacion"]
    veredicto = "equivalentes" if c["equivalentes"] else "equivalencia no demostrada"
    print(
        f"  Diferencia de medias: {c['diferencia_medias']:+.3f}  "
        f"({c['diferencia_relativa_pct']:+.3f}%)   "
        f"TOST margen={c['margen_relativo_pct']:.1f}% ({veredicto})   "
        f"B tarda {c['razon_tiempo_B_sobre_A']:.2f}x lo que A"
    )
    print(
        "  IC 90% de la diferencia: "
        f"[{c['ic_equivalencia'][0]:.3f}, {c['ic_equivalencia'][1]:.3f}] salidas; "
        f"p diferencia pareada={c['t_pvalor_diferencia_pareada']:.4f}"
    )


def imprimir_comparacion_normal(comp):
    print("\n=== Comparacion polar vs rechazo (Normal(0,1), comparacion secundaria) ===")
    for nombre in ("polar", "rechazo"):
        r = comp[nombre]
        print(
            f"  {nombre:<8} media={r['media']:+.4f}  var={r['varianza']:.4f}  "
            f"uniformes/muestra={r['uniformes_por_muestra']:.2f}  "
            f"KS_p={r['ks_pvalor']:.4f}  tiempo={r['tiempo_seg']:.4f}s"
        )
    c = comp["comparacion"]
    print(
        f"  rechazo tarda {c['razon_tiempo_rechazo_sobre_polar']:.2f}x lo que polar, "
        f"y consume {c['razon_uniformes_rechazo_sobre_polar']:.2f}x los uniformes"
    )


def parsear_argumentos(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", default="config/base.yaml")
    ap.add_argument("--n", type=int, default=20000, help="tamano de muestra por validacion")
    ap.add_argument("--replicas", type=int, default=200,
                     help="replicas para comparar_metodos_salidas y su prueba "
                          "TOST con margen practico de 1%%")
    ap.add_argument("--seed", type=int, default=2026,
                     help="semilla base para generar las semillas dispersas de la comparacion")
    ap.add_argument("--out", default="results/tables")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parsear_argumentos(argv)
    raiz = Path(__file__).resolve().parents[1]

    try:
        cfg = cfgmod.cargar(args.config)
    except (OSError, ValueError, KeyError) as exc:
        print("error cargando %r: %s" % (args.config, exc), file=sys.stderr)
        return 1

    print("=== Validacion de generadores ===")
    print(f"config={cfg['_origen']}  n={args.n}\n")
    resultados = correr_validaciones(cfg, args.n)
    filas = tabla_para_informe(resultados)
    imprimir_tabla(filas)

    # Semillas bien dispersas: ver la advertencia en analysis/comparison.py
    # sobre por que semillas consecutivas sesgan el Metodo B.
    semillas = np.random.default_rng(args.seed).integers(0, 2 ** 31, size=args.replicas).tolist()
    comp_salidas = C.comparar_metodos_salidas(cfg, args.replicas, semillas)
    imprimir_comparacion_salidas(comp_salidas)

    comp_normal = C.comparar_normal_polar_vs_rechazo(50000, args.seed)
    imprimir_comparacion_normal(comp_normal)

    out_dir = raiz / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ruta_csv = out_dir / "validacion_generadores.csv"
    with open(ruta_csv, "w", encoding="utf-8") as f:
        columnas = list(filas[0].keys())
        f.write(",".join(columnas) + "\n")
        for fila in filas:
            f.write(",".join("" if fila[c] is None else str(fila[c]) for c in columnas) + "\n")

    # El detalle completo, incluida la muestra, no va al JSON: es para
    # inspeccion humana de la tabla, no para reconstruir el generador.
    detalle = [{k: v for k, v in r.items() if k != "muestra"} for r in resultados]
    ruta_json = out_dir / "validacion_generadores.json"
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(detalle, f, indent=2, ensure_ascii=False)

    ruta_comp = out_dir / "comparacion_metodos.json"
    with open(ruta_comp, "w", encoding="utf-8") as f:
        json.dump(
            {"salidas_M_A_vs_M_B": comp_salidas, "normal_polar_vs_rechazo": comp_normal},
            f, indent=2, ensure_ascii=False,
        )

    print(f"\nGuardado: {ruta_csv}")
    print(f"Guardado: {ruta_json}")
    print(f"Guardado: {ruta_comp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
