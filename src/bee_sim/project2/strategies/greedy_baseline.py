"""Selector GREEDY ex ante para K colmenas.

Regla (todas las magnitudes son sintéticas, ver docs/project2/greedy_design.md):

    valor(s, p)        = R0_p * (1 + d_sp / escala) ** (-gamma)   si d_sp <= radio, si no 0
    ganancia(s | S)    = sum_p valor(s, p) / (1 + lambda * n_S(p))
    n_S(p)             = número de sitios ya elegidos en S con d_sp <= radio

En cada paso se agrega el sitio de mayor ganancia marginal. Empates: menor
site_id (orden lexicográfico). No usa azar. Solo lee el catálogo de candidatos,
el recurso inicial declarado por la regla común y la matriz de distancias.
No llama a simulate ni lee resource_log, viajes o rendimientos futuros.

Complejidad: O(N*M) para construir los valores y O(K*N*M) para los K pasos
(N candidatos, M parches), con memoria O(N*M). No se usan cachés adicionales
porque N=375, M=737 y K es pequeño.
"""
from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
import pandas as pd
import yaml

from ..distance import load_landscape

DEFAULT_PARAMS_FILE = 'config/project2/strategies/greedy.yaml'


@dataclass(frozen=True)
class GreedyParams:
    distance_exponent: float = 2.0
    overlap_penalty: float = 1.0

    def __post_init__(self):
        for name in ('distance_exponent', 'overlap_penalty'):
            x = getattr(self, name)
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
                raise ValueError(f'{name} debe ser un número finito no negativo')


def load_params(path=None, root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[4]
    raw = yaml.safe_load((root / (path or DEFAULT_PARAMS_FILE)).read_text(encoding='utf-8-sig'))
    if set(raw) != {'distance_exponent', 'overlap_penalty'}:
        raise ValueError('Parámetros de GREEDY inesperados')
    return GreedyParams(float(raw['distance_exponent']['value']), float(raw['overlap_penalty']['value']))


def coverage_values(distances_m, initial_resource, radius_m, scale_m, gamma):
    """Matriz N x M de valor ex ante y máscara booleana de cobertura."""
    covered = distances_m <= radius_m
    attraction = (1.0 + distances_m / scale_m) ** (-gamma)
    return np.where(covered, attraction * initial_resource[None, :], 0.0), covered


def greedy_select(values, covered, site_ids, K, overlap_penalty):
    """Núcleo puro y determinista. Devuelve (ids en orden de elección, tabla de pasos).

    `site_ids` debe venir ordenado: el desempate es la posición (menor site_id).
    Termina siempre en exactamente K pasos, incluso si las ganancias son cero o empatan.
    """
    n_sites = len(site_ids)
    if not isinstance(K, (int, np.integer)) or isinstance(K, bool) or K < 1 or K > n_sites:
        raise ValueError('K debe ser un entero entre 1 y el número de candidatos')
    if len(set(site_ids)) != n_sites or list(site_ids) != sorted(site_ids):
        raise ValueError('site_ids debe ser único y estar ordenado')
    if values.shape != covered.shape or values.shape[0] != n_sites:
        raise ValueError('Dimensiones inconsistentes')
    shared = np.zeros(values.shape[1])          # n_S(p)
    chosen, rows = [], []
    for step in range(1, K + 1):
        gains = (values / (1.0 + overlap_penalty * shared)[None, :]).sum(axis=1)
        masked = gains.copy()
        masked[chosen] = -np.inf                # evita duplicados
        best = int(np.argmax(masked))           # argmax devuelve el primer máximo: menor site_id
        for i, sid in enumerate(site_ids):
            rows.append({'step': step, 'site_id': sid, 'marginal_gain': float(gains[i]),
                         'already_chosen': i in chosen, 'chosen_at_step': i == best})
        chosen.append(best)
        shared = shared + covered[best]
    return [site_ids[i] for i in chosen], pd.DataFrame(rows)


def select_sites(config, params=None):
    """Selecciona K sitios con la regla GREEDY usando solo información ex ante."""
    params = params or load_params(root=config.root)
    candidates, patches, distances, _ = load_landscape(config)
    areas = patches.exclusive_area_m2.to_numpy(float)
    initial = config['initial_resource_total'] * areas / areas.sum()   # regla común exclusive_area_share
    values, covered = coverage_values(distances, initial, config['max_foraging_distance_m'],
                                      config['distance_scale_m'], params.distance_exponent)
    order, steps = greedy_select(values, covered, candidates.site_id.tolist(), int(config['K']),
                                 params.overlap_penalty)
    return {'site_ids': sorted(order), 'selection_order': order, 'steps': steps,
            'params': params, 'values': values, 'covered': covered, 'candidates': candidates,
            'patches': patches}
