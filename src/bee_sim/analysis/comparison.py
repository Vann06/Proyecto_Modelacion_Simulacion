"""Comparacion de metodos de generacion equivalentes.

Dos comparaciones, ambas bajo la misma regla: los metodos corren con el
mismo parametro, el mismo horizonte o tamano de muestra, y el mismo conjunto
de semillas. Sin esas tres condiciones iguales la comparacion no es justa y
no sirve para el informe (docs/plan_implementacion.md, seccion F7).

La comparacion principal es M-A contra M-B para las salidas de la colmena.
La secundaria es el metodo polar contra aceptacion y rechazo para la Normal,
que el motor no usa pero que sirve para ilustrar el mismo punto con un
segundo par de metodos ya existentes en generators/continuous.py.

ADVERTENCIA sobre las semillas de `comparar_metodos_salidas`: el LCG tiene
estructura de reticula (generators/lcg.py). Semillas consecutivas (2026,
2027, 2028, ...) producen flujos correlacionados que sesgan sistematicamente
el conteo del Metodo B: verificado empiricamente, 200 replicas de semillas
consecutivas dan una media de 1185.6 salidas contra una teorica de 1200
(Metodo A no se ve afectado, da 1204.4). Con semillas dispersas ambos dan
~1200-1202, sin sesgo, y con miles de replicas ambos convergen sin sesgo
detectable. La funcion valida el rango de las semillas recibidas y falla si
luce sospechosamente angosto.
"""

import time

import numpy as np
from scipy import stats

from ..generators.continuous import normal_polar, normal_rechazo
from ..generators.lcg import LCG
from ..simulation.departures import metodo_a_interarribos, metodo_b_conteo


def comparar_metodos_salidas(cfg, n_replicas, semillas):
    """Corre M-A y M-B bajo condiciones identicas y los compara.

    `semillas` debe tener al menos `n_replicas` elementos y estar bien
    dispersas (ver advertencia del modulo); se usa una semilla distinta por
    replica, la misma secuencia para ambos metodos.

    Para cada metodo devuelve, sobre las `n_replicas` corridas: numero de
    salidas (media y desviacion), prueba de Kolmogorov-Smirnov de los
    interarribos contra la Exponencial teorica, uniformes consumidos en
    promedio y tiempo total de ejecucion. Ademas, una prueba t de dos
    muestras sobre el numero de salidas entre A y B: es la comparacion que
    responde si los dos metodos son estadisticamente equivalentes.
    """
    if len(semillas) < n_replicas:
        raise ValueError(
            "se pidieron %d replicas pero solo hay %d semillas" % (n_replicas, len(semillas))
        )
    semillas = list(semillas)[:n_replicas]
    if n_replicas > 1:
        rango = max(semillas) - min(semillas)
        if rango < n_replicas * 100:
            raise ValueError(
                "las semillas estan demasiado juntas (rango=%d para %d replicas). "
                "El LCG tiene estructura de reticula: semillas consecutivas producen "
                "flujos correlacionados que sesgan el Metodo B de forma sistematica "
                "(ver docstring de este modulo). Genere las semillas con "
                "np.random.default_rng(base).integers(0, 2**31, size=n_replicas), no "
                "con un rango consecutivo." % (rango, n_replicas)
            )

    lam = cfg["departures"]["lambda_per_min"]
    horizonte = cfg["simulation"]["day_minutes"]

    metodos = {"A": metodo_a_interarribos, "B": metodo_b_conteo}
    crudo = {}
    resultado = {}

    for nombre, funcion in metodos.items():
        n_salidas, consumidos, interarribos = [], [], []
        inicio = time.perf_counter()
        for semilla in semillas:
            rng = LCG(seed=semilla)
            tiempos = funcion(lam, horizonte, rng)
            n_salidas.append(len(tiempos))
            consumidos.append(rng.consumidos)
            if tiempos:
                interarribos.extend(np.diff([0.0] + list(tiempos)))
        tiempo_total = time.perf_counter() - inicio

        interarribos = np.asarray(interarribos, dtype=float)
        ks = stats.kstest(interarribos, "expon", args=(0, 1.0 / lam))
        n_salidas = np.asarray(n_salidas, dtype=float)

        crudo[nombre] = n_salidas
        resultado[nombre] = {
            "metodo": nombre,
            "n_replicas": n_replicas,
            "salidas_media": float(n_salidas.mean()),
            "salidas_sd": float(n_salidas.std(ddof=1)) if n_replicas > 1 else 0.0,
            "salidas_teorica": lam * horizonte,
            "interarribos_n": int(interarribos.size),
            "interarribos_ks_estadistico": float(ks.statistic),
            "interarribos_ks_pvalor": float(ks.pvalue),
            "uniformes_media": float(np.mean(consumidos)),
            "tiempo_total_seg": tiempo_total,
            "tiempo_por_replica_seg": tiempo_total / n_replicas,
        }

    if n_replicas > 1:
        t_stat, t_pvalor = stats.ttest_ind(crudo["A"], crudo["B"], equal_var=False)
    else:
        t_stat, t_pvalor = float("nan"), float("nan")

    diferencia_medias = resultado["A"]["salidas_media"] - resultado["B"]["salidas_media"]
    diferencia_relativa_pct = diferencia_medias / resultado["A"]["salidas_media"] * 100.0

    return {
        "lambda_per_min": lam,
        "horizonte_min": horizonte,
        "A": resultado["A"],
        "B": resultado["B"],
        "comparacion": {
            "diferencia_medias": diferencia_medias,
            "diferencia_relativa_pct": diferencia_relativa_pct,
            "t_estadistico": float(t_stat),
            "t_pvalor": float(t_pvalor),
            "equivalentes": bool(t_pvalor > 0.05) if n_replicas > 1 else None,
            "nota": (
                "Con n_replicas grande el t-test detecta diferencias formalmente "
                "significativas aunque sean de una fraccion de punto porcentual: "
                "interpretar 'equivalentes' junto con diferencia_relativa_pct, no "
                "solo con t_pvalor."
            ),
            "razon_tiempo_B_sobre_A": (
                resultado["B"]["tiempo_total_seg"] / resultado["A"]["tiempo_total_seg"]
                if resultado["A"]["tiempo_total_seg"] > 0 else float("nan")
            ),
        },
    }


def comparar_normal_polar_vs_rechazo(n, semilla):
    """Compara `normal_polar` contra `normal_rechazo` para Normal(0, 1).

    Misma semilla para ambos, de modo que la diferencia observada viene
    solo del metodo y no de la suerte. Reporta tiempo, uniformes consumidos
    y bondad de ajuste Kolmogorov-Smirnov para cada uno.
    """
    salida = {}
    for nombre, funcion in (("polar", normal_polar), ("rechazo", normal_rechazo)):
        rng = LCG(seed=semilla)
        inicio = time.perf_counter()
        muestra = np.array([funcion(0.0, 1.0, rng) for _ in range(n)])
        tiempo = time.perf_counter() - inicio
        ks = stats.kstest(muestra, "norm")
        salida[nombre] = {
            "metodo": nombre,
            "n": n,
            "media": float(muestra.mean()),
            "varianza": float(muestra.var()),
            "uniformes_consumidos": rng.consumidos,
            "uniformes_por_muestra": rng.consumidos / n,
            "tiempo_seg": tiempo,
            "ks_estadistico": float(ks.statistic),
            "ks_pvalor": float(ks.pvalue),
        }

    salida["comparacion"] = {
        "razon_tiempo_rechazo_sobre_polar": salida["rechazo"]["tiempo_seg"] / salida["polar"]["tiempo_seg"],
        "razon_uniformes_rechazo_sobre_polar": (
            salida["rechazo"]["uniformes_por_muestra"] / salida["polar"]["uniformes_por_muestra"]
        ),
    }
    return salida
