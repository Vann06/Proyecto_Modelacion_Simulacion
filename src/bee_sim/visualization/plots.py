"""Figuras del informe (F8).

Regla del paquete: estas funciones consumen resultados ya guardados y nunca
vuelven a simular. Cada una recibe un DataFrame o un diccionario -tipicamente
un CSV de resultados leido con pandas, o un resumen de metrics.resumir()- y
devuelve una figura de matplotlib. Ninguna importa generators/ ni
simulation/: si una figura necesita una curva teorica (la logistica de
retorno, por ejemplo), la formula se reescribe aqui en terminos de los
parametros que recibe como numeros, no llamando al modulo del motor.

Todas las funciones son deterministas: mismos datos, misma figura. Ninguna
consume aleatoriedad ni acepta un rng.
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats 

AMBAR = "#B87813"
SALVIA = "#4F6B4A"
TINTA = "#43463C"
GRIS_CLARO = "#B5B5AA"
NIVELES_ORDEN = ("baja", "media", "alta")


def _figura(ancho=7.0, alto=4.5):
    fig, ax = plt.subplots(figsize=(ancho, alto))
    return fig, ax


# Fig 1: interarribos de M-A contra la exponencial teorica

def fig01_interarribos(interarribos_min, lam):
    """Histograma de tiempos entre salidas de M-A contra la Exponencial(lam).

    `interarribos_min` es cualquier arreglo de tiempos entre salidas en
    minutos (por ejemplo, np.diff de los departure_time de una o varias
    replicas de M-A). `lam` es la intensidad configurada, departures.lambda_per_min.
    """
    m = np.asarray(interarribos_min, dtype=float)
    m = m[m >= 0]
    fig, ax = _figura()
    ax.hist(m, bins=40, density=True, color=AMBAR, edgecolor="white", alpha=0.85,
            label="M-A observado")
    x = np.linspace(0, m.max() if m.size else 1.0, 200)
    ax.plot(x, lam * np.exp(-lam * x), color=TINTA, linewidth=2,
            label="Exponencial(%.2f) teorica" % lam)
    ax.set_xlabel("tiempo entre salidas, min")
    ax.set_ylabel("densidad")
    ax.set_title("Interarribos del Metodo A contra la Exponencial teorica")
    ax.legend()
    fig.tight_layout()
    return fig


# Fig 2: salidas por intervalo, M-A y M-B, contra la Poisson teorica

def fig02_salidas_por_intervalo(conteos_a, conteos_b, mu_intervalo):
    """Compara la distribucion de conteos por intervalo de M-A y M-B.

    `conteos_a` y `conteos_b` son arreglos con el numero de salidas
    observadas en intervalos de igual longitud (por ejemplo, particionar la
    jornada en ventanas de 1 minuto y contar salidas por ventana, sobre
    varias replicas). `mu_intervalo` es lambda * duracion_del_intervalo, la
    media Poisson teorica de esos conteos. Es la figura que muestra que
    ambos metodos son la misma variable aleatoria vista de dos maneras.
    """
    a = np.asarray(conteos_a, dtype=int)
    b = np.asarray(conteos_b, dtype=int)
    k_max = int(max(a.max() if a.size else 0, b.max() if b.size else 0,
                     mu_intervalo + 4 * math.sqrt(max(mu_intervalo, 1e-9)))) + 1
    ks = np.arange(0, k_max + 1)

    fig, ax = _figura(8.5, 4.5)
    ancho = 0.3
    ax.bar(ks - ancho, [np.mean(a == k) for k in ks], width=ancho, color=AMBAR, label="M-A")
    ax.bar(ks, [np.mean(b == k) for k in ks], width=ancho, color=SALVIA, label="M-B")
    ax.bar(ks + ancho, stats.poisson.pmf(ks, mu_intervalo), width=ancho, color=TINTA,
           alpha=0.9, label="Poisson(%.2f) teorica" % mu_intervalo)
    ax.set_xlabel("salidas por intervalo")
    ax.set_ylabel("probabilidad")
    ax.set_title("Salidas por intervalo: M-A y M-B contra la Poisson teorica")
    ax.legend()
    fig.tight_layout()
    return fig


# Fig 3: saturacion por poblacion activa

def fig03_saturacion(df_poblacion):
    """Salidas atendidas y viajes completos segun la poblacion activa.

    `df_poblacion` necesita una fila por nivel de poblacion (tipicamente el
    promedio entre replicas de los escenarios bees_low, base y bees_high)
    con columnas: active_bees, salidas_atendidas, viajes_completos,
    salidas_totales. La meseta en salidas_atendidas cuando active_bees
    sigue creciendo es la saturacion: a partir de ahi el limite ya no es la
    fuerza de forrajeo, es la disponibilidad floral.
    """
    df = df_poblacion.sort_values("active_bees")
    fig, ax = _figura(7.5, 4.5)
    ax.plot(df["active_bees"], df["salidas_atendidas"], "o-", color=AMBAR,
            linewidth=2, markersize=7, label="salidas atendidas")
    ax.plot(df["active_bees"], df["viajes_completos"], "o--", color=SALVIA,
            linewidth=2, markersize=7, label="viajes completos")
    if "salidas_totales" in df.columns:
        ax.plot(df["active_bees"], df["salidas_totales"], ":", color=GRIS_CLARO,
                linewidth=2, label="salidas totales (demanda)")
    ax.set_xlabel("abejas activas")
    ax.set_ylabel("promedio por jornada")
    ax.set_title("Saturacion: la fuerza de forrajeo deja de ser el limite")
    ax.legend()
    fig.tight_layout()
    return fig


# Fig 4: flores visitadas por viaje en los tres niveles de disponibilidad

def fig04_flores_por_disponibilidad(df_viajes):
    """Distribucion de flores visitadas por viaje segun flower_availability.

    `df_viajes` es un CSV de viajes (o la concatenacion de varios) con las
    columnas flower_availability y flowers_visited. Tipicamente viene del
    escenario BASE, donde el nivel se sortea por viaje y aparecen los tres.
    """
    niveles = [n for n in NIVELES_ORDEN if n in df_viajes["flower_availability"].unique()]
    datos = [df_viajes.loc[df_viajes["flower_availability"] == n, "flowers_visited"] for n in niveles]
    fig, ax = _figura()
    caja = ax.boxplot(datos, tick_labels=niveles, patch_artist=True, showfliers=False)
    for parche, color in zip(caja["boxes"], (AMBAR, SALVIA, TINTA)):
        parche.set_facecolor(color)
        parche.set_alpha(0.7)
    ax.set_xlabel("disponibilidad floral")
    ax.set_ylabel("flores visitadas por viaje")
    ax.set_title("Flores visitadas segun disponibilidad (efecto de mu_F)")
    fig.tight_layout()
    return fig


# Fig 5: distancia contra duracion del viaje, con banda entre replicas

def fig05_distancia_duracion(df_viajes, n_bins=12):
    """Distancia contra duracion del viaje, agrupada en bins con banda de sd.

    `df_viajes` necesita distance_km y trip_duration_min. Puede combinar
    varias replicas o varios escenarios de distancia (near/base/far) para
    cubrir un rango amplio de D.
    """
    df = df_viajes.copy()
    df["bin"] = pd.cut(df["distance_km"], bins=n_bins)
    agg = df.groupby("bin", observed=True)["trip_duration_min"].agg(["mean", "std", "count"])
    agg = agg[agg["count"] >= 5]
    centros = np.array([intervalo.mid for intervalo in agg.index])

    fig, ax = _figura()
    ax.scatter(df["distance_km"], df["trip_duration_min"], s=6, alpha=0.15, color=GRIS_CLARO,
               label="viajes individuales")
    ax.plot(centros, agg["mean"], "-", color=AMBAR, linewidth=2, label="media por bin")
    ax.fill_between(centros, agg["mean"] - agg["std"], agg["mean"] + agg["std"],
                     color=AMBAR, alpha=0.25, label="+/- 1 sd")
    ax.set_xlabel("distancia, km")
    ax.set_ylabel("duracion del viaje, min")
    ax.set_title("El costo temporal de la distancia")
    ax.legend()
    fig.tight_layout()
    return fig


# Fig 6: tasa de polinizacion observada contra p_pol configurado

def fig06_tasa_polinizacion_vs_p(df_escenarios):
    """Tasa de polinizacion observada convergiendo al p_success configurado.

    AVISO (docs/plan_implementacion.md, F8): graficar flores visitadas
    contra flores polinizadas da una recta casi perfecta y no dice nada
    (F y X correlacionan ~0.90 solo porque X depende de F). Esta figura
    grafica en cambio la TASA observada (polinizadas/visitadas) contra el
    p_success con el que se configuro cada corrida, que es la comparacion
    que de verdad valida el modelo.

    `df_escenarios` necesita una fila por corrida con columnas
    p_success_configurado y tasa_polinizacion (metrics.resumir la llama
    'tasa_polinizacion'). Usa los escenarios oficiales de probabilidad baja,
    base y probabilidad alta guardados en la campaña.
    """
    df = df_escenarios.sort_values("p_success_configurado")
    resumen = df.groupby("p_success_configurado")["tasa_polinizacion"].agg(["mean", "std"])

    fig, ax = _figura()
    ax.scatter(df["p_success_configurado"], df["tasa_polinizacion"], s=18, alpha=0.35,
               color=GRIS_CLARO, label="corridas individuales")
    ax.errorbar(resumen.index, resumen["mean"], yerr=resumen["std"].fillna(0.0),
                fmt="o-", color=AMBAR, linewidth=2, capsize=4, label="media por p configurado")
    lims = [df["p_success_configurado"].min(), df["p_success_configurado"].max()]
    ax.plot(lims, lims, "--", color=TINTA, linewidth=1.5, label="identidad (tasa = p)")
    ax.set_xlabel("p_success configurado")
    ax.set_ylabel("tasa de polinizacion observada")
    ax.set_title("La tasa observada converge al parametro configurado")
    ax.legend()
    fig.tight_layout()
    return fig


# Fig 7: nectar por minuto segun disponibilidad y distancia

def fig07_nectar_por_minuto(df_escenarios):
    """Nectar por minuto planificado, agrupado por escenario.

    AVISO (F8): el nectar TOTAL por escenario es casi la misma figura que
    las flores polinizadas, porque ambos crecen con mu_F. Por minuto de
    actividad es una medida de EFICIENCIA, no de volumen, y es la que
    separa disponibilidad de distancia como causas distintas.

    `df_escenarios` es la tabla consolidada de export_results.py, con
    columnas escenario y nectar_por_minuto_planificado_ml.
    """
    resumen = (df_escenarios.groupby("escenario")["nectar_por_minuto_planificado_ml"]
               .agg(["mean", "std"]).sort_values("mean"))
    fig, ax = _figura(8.0, 4.5)
    colores = [AMBAR if "flower" in e or "flor" in e else SALVIA if "distance" in e or "dist" in e
               else TINTA for e in resumen.index]
    ax.barh(resumen.index, resumen["mean"], xerr=resumen["std"].fillna(0.0), color=colores)
    ax.set_xlabel("nectar por minuto planificado, ml/min")
    ax.set_title("Eficiencia de recoleccion segun disponibilidad y distancia")
    fig.tight_layout()
    return fig


# Fig 8: distancia contra tasa de retorno

def fig08_distancia_retorno(df_viajes, sensitivity=None, midpoint_km=None, n_bins=15):
    """Distancia contra tasa de retorno observada, con la logistica teorica.

    `df_viajes` necesita distance_km y returned. `sensitivity` y
    `midpoint_km` son los DOS NUMEROS de return.sensitivity y
    return.midpoint_km en la configuracion (no una llamada al motor): con
    ellos se traza la curva teorica p_ret(D) = 1 / (1 + e^(a(D-d0))) para
    comparar contra la tasa empirica.
    """
    df = df_viajes.copy()
    df["bin"] = pd.cut(df["distance_km"], bins=n_bins)
    agg = df.groupby("bin", observed=True)["returned"].agg(["mean", "count"])
    agg = agg[agg["count"] >= 5]
    centros = np.array([intervalo.mid for intervalo in agg.index])

    fig, ax = _figura()
    ax.plot(centros, agg["mean"], "o-", color=AMBAR, linewidth=2, markersize=6,
            label="tasa de retorno observada")
    if sensitivity is not None and midpoint_km is not None:
        x = np.linspace(df["distance_km"].min(), df["distance_km"].max(), 200)
        p_teorica = 1.0 / (1.0 + np.exp(sensitivity * (x - midpoint_km)))
        ax.plot(x, p_teorica, "--", color=TINTA, linewidth=2, label="p_ret(D) teorica")
    ax.set_xlabel("distancia, km")
    ax.set_ylabel("tasa de retorno")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("El modelo logistico de retorno y su cola")
    ax.legend()
    fig.tight_layout()
    return fig


# Fig 9: distancia contra flores polinizadas y viajes completos

def fig09_distancia_polinizadas_viajes(df_viajes, n_bins=15):
    """El costo de oportunidad de volar lejos: dos ejes, la misma distancia.

    `df_viajes` necesita distance_km, flowers_pollinated y returned.
    """
    df = df_viajes.copy()
    df["bin"] = pd.cut(df["distance_km"], bins=n_bins)
    agg = df.groupby("bin", observed=True).agg(
        polinizadas=("flowers_pollinated", "mean"),
        retorno=("returned", "mean"),
        n=("distance_km", "count"),
    )
    agg = agg[agg["n"] >= 5]
    centros = np.array([intervalo.mid for intervalo in agg.index])

    fig, ax1 = _figura(7.5, 4.5)
    ax1.plot(centros, agg["polinizadas"], "o-", color=AMBAR, linewidth=2, label="flores polinizadas/viaje")
    ax1.set_xlabel("distancia, km")
    ax1.set_ylabel("flores polinizadas por viaje", color=AMBAR)
    ax1.tick_params(axis="y", labelcolor=AMBAR)

    ax2 = ax1.twinx()
    ax2.plot(centros, agg["retorno"], "o--", color=SALVIA, linewidth=2, label="tasa de retorno")
    ax2.set_ylabel("tasa de retorno", color=SALVIA)
    ax2.tick_params(axis="y", labelcolor=SALVIA)
    ax2.set_ylim(-0.05, 1.05)

    ax1.set_title("El costo de oportunidad de volar lejos")
    fig.tight_layout()
    return fig


# Fig 10: comparativo de disponibilidad floral, la joroba invertida

def fig10_disponibilidad_comparativo(df_viajes):
    """Visitas, polinizacion y duracion del viaje por nivel de disponibilidad.

    `df_viajes` necesita flower_availability, flowers_visited,
    flowers_pollinated y trip_duration_min. La duracion media suele ser MAS
    CORTA en 'media' que en 'baja' o 'alta': el parche pobre pierde tiempo
    buscando, el parche rico lo pierde forrajeando, y el punto intermedio
    minimiza ambos costos a la vez (la 'joroba invertida').
    """
    niveles = [n for n in NIVELES_ORDEN if n in df_viajes["flower_availability"].unique()]
    resumen = df_viajes.groupby("flower_availability").agg(
        visitadas=("flowers_visited", "mean"),
        polinizadas=("flowers_pollinated", "mean"),
        duracion=("trip_duration_min", "mean"),
    ).reindex(niveles)

    fig, ax1 = _figura(8.0, 4.5)
    x = np.arange(len(niveles))
    ancho = 0.35
    ax1.bar(x - ancho / 2, resumen["visitadas"], width=ancho, color=AMBAR, label="visitadas")
    ax1.bar(x + ancho / 2, resumen["polinizadas"], width=ancho, color=SALVIA, label="polinizadas")
    ax1.set_xticks(x)
    ax1.set_xticklabels(niveles)
    ax1.set_ylabel("flores por viaje")
    ax1.set_xlabel("disponibilidad floral")

    ax2 = ax1.twinx()
    ax2.plot(x, resumen["duracion"], "o-", color=TINTA, linewidth=2.5, markersize=8,
             label="duracion media del viaje")
    ax2.set_ylabel("duracion del viaje, min", color=TINTA)
    ax2.tick_params(axis="y", labelcolor=TINTA)

    lineas1, etiquetas1 = ax1.get_legend_handles_labels()
    lineas2, etiquetas2 = ax2.get_legend_handles_labels()
    ax1.legend(lineas1 + lineas2, etiquetas1 + etiquetas2, loc="upper center")
    ax1.set_title("Disponibilidad floral: la joroba invertida en la duracion")
    fig.tight_layout()
    return fig


# Fig 11: indicadores normalizados por escenario

def fig11_indicadores_normalizados(df_escenarios, escenario_base="base.yaml",
                                    columnas=None):
    """Indicadores por escenario, normalizados contra el escenario base = 1.0.

    `df_escenarios` es la tabla consolidada de export_results.py (una fila
    por corrida, columna 'escenario'). `columnas` por defecto compara
    flores polinizadas, nectar recolectado, tasa de retorno y duracion
    media del viaje.
    """
    if columnas is None:
        columnas = ["flores_polinizadas", "nectar_recolectado_ml", "tasa_retorno", "duracion_media_min"]
    medias = df_escenarios.groupby("escenario")[columnas].mean()
    if escenario_base not in medias.index:
        raise ValueError("escenario_base %r no esta en los datos" % escenario_base)
    normalizado = medias.div(medias.loc[escenario_base])
    normalizado = normalizado.drop(index=escenario_base)

    fig, ax = _figura(9.0, 5.0)
    x = np.arange(len(normalizado.index))
    ancho = 0.8 / len(columnas)
    colores = [AMBAR, SALVIA, TINTA, GRIS_CLARO, "#8C5E2A"]
    for i, columna in enumerate(columnas):
        ax.bar(x + i * ancho, normalizado[columna], width=ancho,
               color=colores[i % len(colores)], label=columna)
    ax.axhline(1.0, color="black", linewidth=1, linestyle="--")
    ax.set_xticks(x + ancho * (len(columnas) - 1) / 2)
    ax.set_xticklabels(normalizado.index, rotation=20, ha="right")
    ax.set_ylabel("indicador / indicador en %s" % escenario_base)
    ax.set_title("Comparacion global de escenarios (normalizado contra BASE)")
    ax.legend()
    fig.tight_layout()
    return fig


# Extra 1: ocupacion de forrajeras a lo largo de la jornada

def fig_extra_ocupacion_jornada(df_viajes, day_minutes, n_puntos=200):
    """Cuantas abejas estan en vuelo en cada instante de la jornada.

    `df_viajes` necesita departure_time y trip_duration_min. Cada viaje
    aporta un intervalo [salida, salida + duracion); se cuenta cuantos
    intervalos cubren cada instante de una grilla fina. `day_minutes` es
    simulation.day_minutes, el largo de la jornada.
    """
    salidas = df_viajes["departure_time"].to_numpy()
    llegadas = salidas + df_viajes["trip_duration_min"].to_numpy()
    t = np.linspace(0, day_minutes, n_puntos)
    ocupadas = np.array([np.sum((salidas <= ti) & (ti < llegadas)) for ti in t])

    fig, ax = _figura(8.5, 4.0)
    ax.fill_between(t, ocupadas, color=AMBAR, alpha=0.6)
    ax.plot(t, ocupadas, color=TINTA, linewidth=1.2)
    ax.set_xlabel("minutos desde el inicio de la jornada")
    ax.set_ylabel("abejas en vuelo")
    ax.set_title("Ocupacion de forrajeras a lo largo de la jornada")
    fig.tight_layout()
    return fig


# Extra 2: tiras de puntos de las replicas, ambos ejes desde cero

def fig_extra_tiras_replicas(resumenes_por_escenario, metrica):
    """Una tira de puntos por escenario para una metrica, ejes desde cero.

    `resumenes_por_escenario` es {nombre_escenario: [resumenes...]}, lo que
    devuelve experiments.runner.correr_campana. `metrica` es la llave de
    metrics.resumir a graficar (por ejemplo 'flores_polinizadas'). Muestra
    de un vistazo por que una sola corrida no basta: la dispersion entre
    puntos de una misma fila es, literalmente, el motivo para correr
    replicas.
    """
    nombres = list(resumenes_por_escenario.keys())
    fig, ax = _figura(8.5, max(3.0, 0.5 * len(nombres) + 1.5))
    maximo = 0.0
    for i, nombre in enumerate(nombres):
        valores = [r[metrica] for r in resumenes_por_escenario[nombre] if r.get(metrica) is not None]
        if not valores:
            continue
        maximo = max(maximo, max(valores))
        y = np.full(len(valores), i) + np.random.default_rng(0).uniform(-0.15, 0.15, len(valores))
        ax.scatter(valores, y, s=14, alpha=0.5, color=AMBAR)
        ax.scatter([np.mean(valores)], [i], s=90, color=TINTA, marker="D", zorder=5)
    ax.set_yticks(range(len(nombres)))
    ax.set_yticklabels(nombres)
    ax.set_xlim(0, maximo * 1.1 if maximo > 0 else 1.0)
    ax.set_xlabel(metrica)
    ax.set_title("Dispersion entre replicas por escenario: " + metrica)
    fig.tight_layout()
    return fig
