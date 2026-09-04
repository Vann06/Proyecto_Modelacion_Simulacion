"""Carga, fusion y validacion de la configuracion de escenarios.

Los parametros experimentales viven fuera del codigo: cambiar una condicion
no debe obligar a tocar el motor. Cada escenario declara `extends: base.yaml`
y escribe solamente lo que cambia, de modo que la diferencia entre dos
escenarios se lee de un vistazo en el propio archivo.
"""

import copy
import os

import yaml

NIVELES = ("baja", "media", "alta")

LLAVES_REQUERIDAS = (
    "simulation.seed", "simulation.day_minutes", "simulation.replications",
    "simulation.rng_source",
    "colony.active_bees",
    "departures.generation_method", "departures.lambda_per_min",
    "environment.flower_availability", "environment.availability_probs",
    "environment.levels",
    "foraging.distance.model", "foraging.distance.shape", "foraging.distance.scale",
    "foraging.velocity_km_min", "foraging.flower_count_model",
    "foraging.search_shape", "foraging.time_per_flower_mean",
    "pollination.p_success",
    "nectar.shape",
    "return.model", "return.sensitivity", "return.midpoint_km",
)


def obtener(cfg, ruta, defecto=KeyError):
    """Lee una llave anidada con notacion de puntos: obtener(cfg, 'colony.active_bees')."""
    nodo = cfg
    for parte in ruta.split("."):
        if not isinstance(nodo, dict) or parte not in nodo:
            if defecto is KeyError:
                raise KeyError("falta la llave de configuracion %r" % ruta)
            return defecto
        nodo = nodo[parte]
    return nodo


def fusionar(base, encima):
    """Mezcla profunda. Lo que el escenario no menciona se hereda de la base."""
    salida = copy.deepcopy(base)
    for llave, valor in encima.items():
        if isinstance(valor, dict) and isinstance(salida.get(llave), dict):
            salida[llave] = fusionar(salida[llave], valor)
        else:
            salida[llave] = copy.deepcopy(valor)
    return salida


def cargar(ruta, _vistos=None):
    """Carga un YAML resolviendo la cadena de `extends` y validando el resultado."""
    ruta = os.path.abspath(ruta)
    _vistos = _vistos or []
    if ruta in _vistos:
        raise ValueError("herencia circular en la configuracion: %s" % ruta)
    with open(ruta, "r", encoding="utf-8") as f:
        crudo = yaml.safe_load(f) or {}

    padre = crudo.pop("extends", None)
    if padre:
        base = cargar(os.path.join(os.path.dirname(ruta), padre), _vistos + [ruta])
        cfg = fusionar(base, crudo)
    else:
        cfg = crudo

    cfg["_origen"] = os.path.basename(ruta)
    validar(cfg)
    return cfg


def validar(cfg):
    """Falla temprano y con un mensaje que dice exactamente que falta."""
    faltantes = []
    for llave in LLAVES_REQUERIDAS:
        try:
            obtener(cfg, llave)
        except KeyError:
            faltantes.append(llave)
    if faltantes:
        raise KeyError("configuracion incompleta, faltan: %s" % ", ".join(faltantes))

    probs = obtener(cfg, "environment.availability_probs")
    if len(probs) != 3 or abs(sum(probs) - 1.0) > 1e-9:
        raise ValueError("availability_probs debe tener 3 valores que sumen 1, tiene %r" % probs)

    for nivel in NIVELES:
        for campo in ("mu_flowers", "search_scale", "nectar_scale"):
            obtener(cfg, "environment.levels.%s.%s" % (nivel, campo))

    disp = obtener(cfg, "environment.flower_availability")
    if disp != "sample" and disp not in NIVELES:
        raise ValueError("flower_availability debe ser 'sample' o uno de %s, es %r" % (NIVELES, disp))

    metodo = obtener(cfg, "departures.generation_method")
    if metodo not in ("A", "B"):
        raise ValueError("generation_method debe ser 'A' o 'B', es %r" % metodo)

    fuente = obtener(cfg, "simulation.rng_source")
    if fuente not in ("lcg", "numpy"):
        raise ValueError("rng_source debe ser 'lcg' o 'numpy', es %r" % fuente)

    return cfg


def resumen(cfg):
    """Una linea por parametro que define el escenario. Util en notebooks."""
    disp = obtener(cfg, "environment.flower_availability")
    return "\n".join([
        "escenario           %s" % cfg.get("_origen", "?"),
        "semilla             %s" % obtener(cfg, "simulation.seed"),
        "jornada             %.0f min" % obtener(cfg, "simulation.day_minutes"),
        "abejas activas      %d" % obtener(cfg, "colony.active_bees"),
        "metodo de salidas   %s   (lambda = %.2f / min)" % (
            obtener(cfg, "departures.generation_method"),
            obtener(cfg, "departures.lambda_per_min")),
        "disponibilidad      %s" % ("sorteada por viaje" if disp == "sample" else "fija en '%s'" % disp),
        "distancia           Weibull(forma=%.1f, escala=%.2f km)" % (
            obtener(cfg, "foraging.distance.shape"),
            obtener(cfg, "foraging.distance.scale")),
        "fuente de uniformes %s" % obtener(cfg, "simulation.rng_source"),
    ])
