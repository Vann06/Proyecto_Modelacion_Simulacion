"""Helpers deterministas del contrato de Oslo, sin simulador ni optimizadores.

Las cantidades usadas en pruebas son fixtures abstractas, no recursos de Oslo.
"""
from numbers import Integral
import numpy as np

PROCESS_CODES = {
    "departures": 0, "patch_selection": 1, "flowers": 2, "nectar": 3,
    "pollination": 4, "search": 5, "foraging": 6, "return": 7,
    "climate": 8, "regeneration": 9,
}


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} debe ser entero >= {minimum}")
    return int(value)


def validate_hive_sites(hive_sites, candidate_ids, K):
    """Valida exactamente K IDs distintos y devuelve orden canónico estable."""
    K = _integer(K, "K", 1)
    if isinstance(hive_sites, (str, bytes)):
        raise ValueError("hive_sites debe ser una secuencia de IDs, no un texto")
    sites = tuple(hive_sites)
    if not all(isinstance(s, str) and s for s in sites):
        raise ValueError("Cada site_id debe ser un texto no vacío")
    if len(sites) != K or len(set(sites)) != K:
        raise ValueError("Se requieren exactamente K sitios sin duplicados")
    if not set(sites).issubset(set(candidate_ids)):
        raise ValueError("Hay un sitio fuera del catálogo de candidatos válidos")
    return tuple(sorted(sites))


def event_rng(seed, day, hive_slot, trip_slot, process, draw_slot=0):
    """Bloque PCG64 por clave estable; no incluye algoritmo ni hash de Python.

    Crear una vez por bloque de evento. Repetir la misma clave reinicia el
    mismo bloque: el futuro motor debe usar draw_slot/eventos estables.
    """
    if process not in PROCESS_CODES:
        raise ValueError(f"Proceso desconocido: {process}")
    key = [_integer(v, k) for k, v in [
        ("seed", seed), ("day", day), ("hive_slot", hive_slot),
        ("trip_slot", trip_slot), ("draw_slot", draw_slot)]]
    sequence = np.random.SeedSequence([*key, PROCESS_CODES[process]])
    return np.random.Generator(np.random.PCG64(sequence))


def resource_step(resource, consumption, regeneration):
    """Una identidad de balance para validar logs; no ejecuta dinámica ecológica.

    Regeneración al cierre del día; consumo no puede superar el stock inicial.
    Se exige forma idéntica para evitar broadcasting accidental y sobreconsumo.
    """
    arrays = [np.asarray(x, dtype=float) for x in [resource, consumption, regeneration]]
    if any(a.shape != arrays[0].shape for a in arrays):
        raise ValueError("Los tres estados deben tener la misma forma")
    if any(not np.isfinite(a).all() or (a < 0).any() for a in arrays):
        raise ValueError("Recursos, consumo y regeneración deben ser finitos y no negativos")
    r, c, g = arrays
    if (c > r).any():
        raise ValueError("Consumo superior al recurso disponible; no ocultarlo con un clamp")
    result = np.maximum(0.0, r - c + g)
    if not np.isfinite(result).all():
        raise ValueError("Desbordamiento en el balance de recurso")
    return result


def bootstrap_ci(values, seed, statistic=np.mean, n_boot=5000, confidence=0.95):
    """IC percentil; unidad de remuestreo: réplica independiente, no viaje.

    Para CRN pasar diferencias emparejadas por seed, escenario y K. No elimina
    ausencias silenciosamente. No proporciona IC simultáneos de varias métricas.
    """
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Se requieren al menos dos réplicas finitas en un vector")
    n_boot = _integer(n_boot, "n_boot", 2)
    seed = _integer(seed, "seed")
    if not 0 < confidence < 1 or not callable(statistic):
        raise ValueError("confidence debe estar en (0,1) y statistic debe ser callable")
    rng = np.random.Generator(np.random.PCG64(seed))
    samples = np.empty(n_boot)
    for i in range(n_boot):
        samples[i] = statistic(x[rng.integers(0, len(x), size=len(x))])
    estimate = float(statistic(x))
    if not np.isfinite(samples).all() or not np.isfinite(estimate):
        raise ValueError("El estadístico debe producir escalares finitos")
    tail = (1 - confidence) / 2
    lower, upper = np.quantile(samples, [tail, 1 - tail], method="linear")
    return {"estimate": estimate, "ci_lower": float(lower), "ci_upper": float(upper),
            "confidence": float(confidence), "n": len(x), "n_boot": n_boot, "seed": seed}
