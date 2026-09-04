"""Validacion estadistica de los generadores.

El informe pide validar en dos niveles. Este modulo cubre el primero: cada
generador contra las propiedades teoricas de su distribucion. El segundo
nivel, los invariantes del motor, vive en simulation/metrics.py.

Convencion: toda funcion devuelve un dict con la misma forma, para que
scripts/validate_generators.py pueda imprimirlas y exportarlas igual sin
saber cual corrio.
"""

import math

import numpy as np
from scipy import stats

from ..generators.bernoulli import binomial_por_convolucion
from ..generators.continuous import gamma, weibull
from ..generators.exponential import exponencial
from ..generators.poisson import binomial_negativa, poisson_inversa


def _resultado(nombre, n, prueba, estadistico, p_valor, extra=None):
    r = {
        "generador": nombre,
        "n": int(n),
        "prueba": prueba,
        "estadistico": float(estadistico),
        "p_valor": float(p_valor),
    }
    if extra:
        r.update(extra)
    return r


def chi2_agrupada(observadas, esperadas, minimo=5.0):
    """Chi cuadrada agrupando categorias con frecuencia esperada < minimo.

    Sin ese agrupamiento la prueba se desestabiliza en las colas, donde la
    frecuencia esperada es casi cero y una sola observacion inflaria el
    estadistico. Devuelve (estadistico, p_valor, categorias_usadas).
    """
    obs_g, esp_g = [], []
    o_acc = e_acc = 0.0
    for o, e in zip(observadas, esperadas):
        o_acc += o
        e_acc += e
        if e_acc >= minimo:
            obs_g.append(o_acc)
            esp_g.append(e_acc)
            o_acc = e_acc = 0.0
    if e_acc > 0:
        if esp_g:
            obs_g[-1] += o_acc
            esp_g[-1] += e_acc
        else:
            obs_g.append(o_acc)
            esp_g.append(e_acc)
    obs_g = np.asarray(obs_g, dtype=float)
    esp_g = np.asarray(esp_g, dtype=float)
    # scipy exige que ambas sumas coincidan; la cola truncada las separa un poco
    esp_g = esp_g * (obs_g.sum() / esp_g.sum())
    est, p = stats.chisquare(obs_g, f_exp=esp_g)
    return float(est), float(p), int(len(obs_g))


# ----------------------------------------------------------------------
# Fuente uniforme
# ----------------------------------------------------------------------

def validar_uniforme(rng, n=20000, retardos=10):
    """Media, varianza, Kolmogorov-Smirnov y autocorrelacion.

    La autocorrelacion es la prueba que de verdad importa para el LCG: un
    generador puede tener media 0.5 y varianza 1/12 perfectas y aun asi ser
    malo si cada numero depende del anterior.
    """
    m = np.asarray(rng.uniform_array(n), dtype=float)
    ks = stats.kstest(m, "uniform")
    autocorr = [float(np.corrcoef(m[:-k], m[k:])[0, 1]) for k in range(1, retardos + 1)]
    return _resultado(
        getattr(rng, "nombre", "uniforme"), n, "KS", ks.statistic, ks.pvalue,
        {
            "media": float(m.mean()), "media_teorica": 0.5,
            "varianza": float(m.var()), "varianza_teorica": 1.0 / 12.0,
            "autocorrelacion": autocorr,
            "autocorrelacion_max": float(max(abs(a) for a in autocorr)),
            "muestra": m,
        },
    )


# ----------------------------------------------------------------------
# Continuas: Kolmogorov-Smirnov
# ----------------------------------------------------------------------

def validar_exponencial(lam, rng, n=20000):
    m = np.asarray([exponencial(lam, rng) for _ in range(n)], dtype=float)
    ks = stats.kstest(m, "expon", args=(0, 1.0 / lam))
    return _resultado(
        "Exponencial(%g)" % lam, n, "KS", ks.statistic, ks.pvalue,
        {"media": float(m.mean()), "media_teorica": 1.0 / lam,
         "varianza": float(m.var()), "varianza_teorica": 1.0 / lam ** 2,
         "muestra": m},
    )


def validar_weibull(forma, escala, rng, n=20000):
    """KS contra la Weibull teorica.

    Prueba de humo recomendada: correr esta misma funcion con forma = 1 debe
    dar los mismos resultados que el generador exponencial con lambda =
    1/escala, porque Weibull(1, escala) es exactamente esa exponencial.
    """
    m = np.asarray([weibull(forma, escala, rng) for _ in range(n)], dtype=float)
    ks = stats.kstest(m, "weibull_min", args=(forma, 0, escala))
    return _resultado(
        "Weibull(%g, %g)" % (forma, escala), n, "KS", ks.statistic, ks.pvalue,
        {"media": float(m.mean()),
         "media_teorica": escala * math.gamma(1.0 + 1.0 / forma),
         "muestra": m},
    )


def validar_gamma(forma, escala, rng, n=20000):
    m = np.asarray([gamma(forma, escala, rng) for _ in range(n)], dtype=float)
    ks = stats.kstest(m, "gamma", args=(forma, 0, escala))
    return _resultado(
        "Gamma(%g, %g)" % (forma, escala), n, "KS", ks.statistic, ks.pvalue,
        {"media": float(m.mean()), "media_teorica": forma * escala,
         "varianza": float(m.var()), "varianza_teorica": forma * escala ** 2,
         "muestra": m},
    )


# ----------------------------------------------------------------------
# Discretas: chi cuadrada
# ----------------------------------------------------------------------

def validar_poisson(mu, rng, n=20000, generador=poisson_inversa):
    """Chi cuadrada contra la Poisson teorica, con colas agrupadas.

    El argumento `generador` permite validar tambien poisson_knuth con la
    misma prueba, que es lo que exige comparar dos metodos de forma justa.
    """
    m = np.asarray([generador(mu, rng) for _ in range(n)], dtype=float)
    k_max = int(mu + 6 * math.sqrt(mu)) + 1
    obs = [float(np.sum(m == k)) for k in range(k_max)]
    esp = [n * stats.poisson.pmf(k, mu) for k in range(k_max)]
    obs.append(float(np.sum(m >= k_max)))
    esp.append(n * (1.0 - stats.poisson.cdf(k_max - 1, mu)))
    est, p, cat = chi2_agrupada(obs, esp)
    return _resultado(
        "Poisson(%g) via %s" % (mu, generador.__name__), n, "chi2", est, p,
        {"categorias": cat,
         "media": float(m.mean()), "media_teorica": mu,
         "varianza": float(m.var()), "varianza_teorica": mu,
         "muestra": m},
    )


def validar_binomial(ensayos, p, rng, n=20000):
    """Chi cuadrada sobre la Binomial construida por convolucion."""
    m = np.asarray([binomial_por_convolucion(ensayos, p, rng) for _ in range(n)],
                   dtype=float)
    obs = [float(np.sum(m == k)) for k in range(ensayos + 1)]
    esp = [n * stats.binom.pmf(k, ensayos, p) for k in range(ensayos + 1)]
    est, pv, cat = chi2_agrupada(obs, esp)
    return _resultado(
        "Binomial(%d, %g)" % (ensayos, p), n, "chi2", est, pv,
        {"categorias": cat,
         "media": float(m.mean()), "media_teorica": ensayos * p,
         "varianza": float(m.var()), "varianza_teorica": ensayos * p * (1 - p),
         "muestra": m},
    )


def validar_binomial_negativa(mu, forma, rng, n=20000):
    """Chi cuadrada sobre la mezcla Gamma-Poisson.

    Lo que hay que ver aqui no es solo el ajuste, sino que la varianza
    empirica se acerque a mu + mu^2/forma y no a mu: si diera mu, la
    composicion no esta produciendo sobredispersion y algo esta mal.
    """
    m = np.asarray([binomial_negativa(mu, forma, rng) for _ in range(n)], dtype=float)
    p = forma / (forma + mu)
    k_max = int(stats.nbinom.ppf(0.999, forma, p)) + 1
    obs = [float(np.sum(m == k)) for k in range(k_max)]
    esp = [n * stats.nbinom.pmf(k, forma, p) for k in range(k_max)]
    obs.append(float(np.sum(m >= k_max)))
    esp.append(n * (1.0 - stats.nbinom.cdf(k_max - 1, forma, p)))
    est, pv, cat = chi2_agrupada(obs, esp)
    return _resultado(
        "BinNeg(mu=%g, forma=%g)" % (mu, forma), n, "chi2", est, pv,
        {"categorias": cat,
         "media": float(m.mean()), "media_teorica": mu,
         "varianza": float(m.var()), "varianza_teorica": mu + mu ** 2 / forma,
         "muestra": m},
    )


def validar_adelgazamiento(mu, p, rng, n=20000):
    """Verificacion cruzada del par flores visitadas y flores polinizadas.

    Si F ~ Poisson(mu) y cada visita poliniza con probabilidad p, entonces
    la marginal de X es exactamente Poisson(mu * p). Es la propiedad de
    adelgazamiento, y es la unica validacion del proyecto contra un valor
    teorico exacto que no depende de calibrar ningun parametro: si esta
    prueba pasa, el generador Poisson y el Bernoulli estan bien y ademas
    estan bien encadenados.
    """
    x = np.asarray(
        [binomial_por_convolucion(poisson_inversa(mu, rng), p, rng) for _ in range(n)],
        dtype=float,
    )
    mu_teorica = mu * p
    k_max = int(mu_teorica + 6 * math.sqrt(mu_teorica)) + 1
    obs = [float(np.sum(x == k)) for k in range(k_max)]
    esp = [n * stats.poisson.pmf(k, mu_teorica) for k in range(k_max)]
    obs.append(float(np.sum(x >= k_max)))
    esp.append(n * (1.0 - stats.poisson.cdf(k_max - 1, mu_teorica)))
    est, pv, cat = chi2_agrupada(obs, esp)
    return _resultado(
        "Adelgazamiento: Poisson(%g) filtrada con p=%g" % (mu, p), n, "chi2", est, pv,
        {"categorias": cat,
         "media": float(x.mean()), "media_teorica": mu_teorica,
         "varianza": float(x.var()), "varianza_teorica": mu_teorica,
         "muestra": x},
    )
