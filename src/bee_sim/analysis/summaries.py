"""Agregacion estadistica sobre replicas y sobre escenarios.

No sabe nada de abejas ni de configuracion: recibe diccionarios de numeros y
devuelve media, desviacion estandar, percentiles e intervalo de confianza al
95%. Consume la forma que ya devuelve `experiments.runner.correr_escenario`
(lista de resumenes de `simulation.metrics.resumir`) y
`experiments.runner.correr_campana` (nombre de escenario -> esa lista).
"""

import numpy as np
from scipy import stats


def resumir_replicas(resumenes):
    """Agrega una lista de diccionarios con las mismas llaves numericas.

    Las llaves no numericas o booleanas se ignoran en silencio, para poder
    recibir directamente lo que devuelve `metrics.resumir` sin filtrarlo a
    mano primero.

    Devuelve, por llave: n, media, sd, percentiles 5/50/95 e intervalo de
    confianza al 95%. Con una sola replica, sd es 0.0 y el intervalo
    colapsa al valor observado, porque no hay variabilidad que estimar.
    Una llave cuyo valor es None en todas las replicas (una tasa sin
    denominador, por ejemplo) se omite en vez de fallar.
    """
    if not resumenes:
        raise ValueError("resumenes no puede estar vacio")

    llaves = resumenes[0].keys()
    salida = {}
    for llave in llaves:
        valores = np.array(
            [r[llave] for r in resumenes
             if isinstance(r.get(llave), (int, float)) and not isinstance(r.get(llave), bool)],
            dtype=float,
        )
        if valores.size == 0:
            continue
        n = valores.size
        media = float(valores.mean())
        sd = float(valores.std(ddof=1)) if n > 1 else 0.0
        if n > 1 and sd > 0:
            ic_bajo, ic_alto = stats.t.interval(0.95, n - 1, loc=media, scale=sd / np.sqrt(n))
        else:
            ic_bajo, ic_alto = media, media
        salida[llave] = {
            "n": int(n),
            "media": media,
            "sd": sd,
            "p5": float(np.percentile(valores, 5)),
            "p50": float(np.percentile(valores, 50)),
            "p95": float(np.percentile(valores, 95)),
            "ic95_bajo": float(ic_bajo),
            "ic95_alto": float(ic_alto),
        }
    return salida


def resumir_escenarios(por_escenario):
    """Aplica `resumir_replicas` a cada escenario de un diccionario.

    `por_escenario` es lo que devuelve `experiments.runner.correr_campana`:
    nombre_escenario -> lista de resumenes de replica. Un escenario con la
    lista vacia se omite en vez de fallar, para que un escenario que
    todavia no ha corrido no tumbe el resumen de los demas.
    """
    salida = {}
    for nombre, resumenes in por_escenario.items():
        if not resumenes:
            continue
        salida[nombre] = resumir_replicas(resumenes)
    return salida
