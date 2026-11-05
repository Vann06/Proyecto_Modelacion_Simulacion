"""piloto de objetivos de nsga-ii: senal, correlacion y costo antes de la busqueda.

las instalaciones del piloto no son soluciones de nsga-ii ni un baseline comparable.
solo usa replicas de busqueda (1-30); las reservadas 31-100 no se tocan.
"""
from concurrent.futures import ProcessPoolExecutor
from math import ceil
from pathlib import Path
import json
import os
import time
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from ..contract import _integer, validate_hive_sites
from ..metrics import METRIC_NAMES
from ..simulation import _engine_hash, simulate

SEARCH_REPLICATIONS = 30
OBJECTIVES = {'total_resource_obtained': 'maximize', 'mean_distance_m': 'minimize',
              'competition_pressure': 'minimize'}
ALTERNATIVE_OBJECTIVES = {'min_resource_per_hive': 'maximize'}
PILOT_SEED, PILOT_UNIFORM, PILOT_CLUSTERED = 2026, 150, 50
PILOT_DIRECTORY = 'results/project2/nsga2_pilot'


def sample_installations(candidates, K, n_uniform, n_clustered, pilot_seed):
    """instalaciones unicas: uniformes y agrupadas (un ancla y sus K-1 vecinos mas cercanos).

    las agrupadas existen porque el muestreo uniforme casi nunca junta colmenas,
    y nsga-ii si puede explorar esa zona del espacio.
    """
    K, n_uniform, n_clustered = _integer(K, 'K', 1), _integer(n_uniform, 'n_uniform'), _integer(n_clustered, 'n_clustered')
    table = candidates.sort_values('site_id').reset_index(drop=True)
    ids = table.site_id.tolist()
    if K > len(ids):
        raise ValueError('K supera el numero de candidatos')
    rng = np.random.Generator(np.random.PCG64(_integer(pilot_seed, 'pilot_seed')))
    seen, rows = set(), []

    def add(family, indices):
        sites = validate_hive_sites([ids[i] for i in indices], ids, K)
        if tuple(sites) in seen:
            return False
        seen.add(tuple(sites))
        rows.append({'solution_id': f'pilot_{len(rows) + 1:03d}', 'family': family, 'site_ids': list(sites)})
        return True

    xy = table[['x_m', 'y_m']].to_numpy(float)
    found = 0
    for anchor in rng.permutation(len(ids)):
        if found == n_clustered:
            break
        distance = np.linalg.norm(xy - xy[anchor], axis=1)
        found += add('clustered', np.argsort(distance, kind='stable')[:K])
    if found < n_clustered:
        raise ValueError('No hay suficientes instalaciones agrupadas distintas')
    found = 0
    for _ in range(100 * max(n_uniform, 1)):
        if found == n_uniform:
            break
        found += add('uniform', rng.choice(len(ids), size=K, replace=False))
    if found < n_uniform:
        raise ValueError('No hay suficientes instalaciones uniformes distintas')
    return pd.DataFrame(rows)


def _evaluate(task):
    solution_id, sites, replication_id, seed, config = task
    start = time.perf_counter()
    result = simulate(sites, seed, config)
    return {'solution_id': solution_id, 'replication_id': replication_id, 'seed': seed,
            **result['metrics'], 'elapsed_s': time.perf_counter() - start,
            'config_hash': result['provenance']['config_hash'], 'engine_hash': result['provenance']['engine_hash'],
            'input_hash': result['provenance']['input_hash']}


def run_pilot(installations, config, replications=SEARCH_REPLICATIONS, workers=None):
    """evalua cada instalacion con las mismas seeds; devuelve filas y metadatos de costo."""
    replications = _integer(replications, 'replications', 1)
    if replications > SEARCH_REPLICATIONS:
        raise ValueError('El piloto no puede usar replicas reservadas (31-100)')
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    bank = pd.read_csv(config.root / config['seed_bank_file']).head(replications)
    tasks = [(row.solution_id, row.site_ids, int(seed.replication_id), int(seed.seed), config)
             for row in installations.itertuples() for seed in bank.itertuples()]
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(_evaluate, tasks, chunksize=5))
    wall = time.perf_counter() - start
    frame = pd.DataFrame(rows)
    return frame, {'workers': workers, 'wall_s': wall, 'simulations': len(frame), 'replications': replications,
                   'wall_s_per_simulation': wall / len(frame), 'cpu_s_per_simulation': float(frame.elapsed_s.mean())}


def save_pilot(directory, installations, frame, meta):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stored = installations.assign(site_ids=installations.site_ids.map(lambda s: json.dumps(s, separators=(',', ':'))))
    stored.to_csv(directory / 'pilot_installations.csv', index=False, lineterminator='\n')
    frame.to_csv(directory / 'pilot_metrics.csv', index=False, lineterminator='\n', na_rep='')
    (directory / 'pilot_meta.json').write_text(json.dumps(meta, indent=2, sort_keys=True), encoding='utf-8')


def load_pilot(directory, config):
    """lee un piloto guardado; rechaza resultados de otra configuracion o motor."""
    directory = Path(directory)
    installations = pd.read_csv(directory / 'pilot_installations.csv')
    installations['site_ids'] = installations.site_ids.map(json.loads)
    frame = pd.read_csv(directory / 'pilot_metrics.csv')
    meta = json.loads((directory / 'pilot_meta.json').read_text(encoding='utf-8'))
    if set(frame.config_hash) != {config.config_hash} or set(frame.engine_hash) != {_engine_hash()}:
        raise ValueError('Piloto de otra configuracion o motor; hay que repetirlo')
    if frame.replication_id.max() > SEARCH_REPLICATIONS:
        raise ValueError('El piloto contiene replicas reservadas')
    return installations, frame, meta


def installation_means(frame, installations, metrics=METRIC_NAMES):
    """una fila por instalacion; la media por replica es la que veria nsga-ii como fitness."""
    means = frame.groupby('solution_id')[list(metrics)].mean()
    return means.join(installations.set_index('solution_id').family)


def variance_components(frame, metric):
    """anova de dos vias instalacion x seed: las seeds son comunes, su efecto no separa soluciones."""
    table = frame.pivot(index='solution_id', columns='replication_id', values=metric).dropna()
    n, r = table.shape
    if n < 2 or r < 2:
        raise ValueError('Se requieren al menos dos instalaciones y dos replicas completas')
    x = table.to_numpy(float)
    row, col, grand = x.mean(1, keepdims=True), x.mean(0, keepdims=True), x.mean()
    ms_between = r * ((row - grand) ** 2).sum() / (n - 1)
    ms_noise = ((x - row - col + grand) ** 2).sum() / ((n - 1) * (r - 1))
    signal = max(0., (ms_between - ms_noise) / r)
    return {'sd_between': signal ** .5, 'sd_noise': ms_noise ** .5, 'n_installations': n, 'replications': r,
            'reliability': signal / (signal + ms_noise / r) if signal + ms_noise > 0 else 0.}


def signal_table(frame, metrics):
    """fiabilidad de la media por replica y replicas necesarias para llegar a 0.9."""
    rows = []
    for metric in metrics:
        c = variance_components(frame, metric)
        need = ceil(9 * c['sd_noise'] ** 2 / c['sd_between'] ** 2) if c['sd_between'] > 0 else np.inf
        rows.append({'metric': metric, 'mean': frame[metric].mean(), **c, 'replications_for_0.9': need,
                     'undefined_runs': int(frame[metric].isna().sum()), 'zero_run_share': float(frame[metric].eq(0).mean())})
    return pd.DataFrame(rows).set_index('metric')


def correlation_table(means, metrics, n_boot=2000, seed=2026):
    """spearman entre medias, con ic percentil 95% remuestreando instalaciones."""
    metrics = list(metrics)
    rng = np.random.Generator(np.random.PCG64(seed))
    values = means[metrics].to_numpy(float)
    samples = rng.integers(0, len(values), size=(n_boot, len(values)))
    rows = []
    for i, a in enumerate(metrics):
        for j in range(i + 1, len(metrics)):
            boot = [spearmanr(values[s, i], values[s, j]).statistic for s in samples]
            low, high = np.nanquantile(boot, [.025, .975])
            rows.append({'metric_a': a, 'metric_b': metrics[j], 'n': len(values),
                         'spearman': spearmanr(values[:, i], values[:, j]).statistic, 'ci95_low': low, 'ci95_high': high})
    return pd.DataFrame(rows)


def nondominated_mask(means, directions):
    """true si ninguna otra fila es igual o mejor en todo y estrictamente mejor en algo."""
    signs = np.array([1. if d == 'minimize' else -1. for d in directions.values()])
    x = means[list(directions)].to_numpy(float) * signs
    if np.isnan(x).any():
        raise ValueError('Objetivos indefinidos; no sustituir vacios por cero')
    better_or_equal = (x[:, None, :] <= x[None, :, :]).all(2)
    strictly_better = (x[:, None, :] < x[None, :, :]).any(2)
    return ~(better_or_equal & strictly_better).any(0)


def front_stability(frame, directions):
    """jaccard del frente entre replicas impares y pares; 1 = misma seleccion en ambas mitades."""
    fronts = []
    for parity in (0, 1):
        half = frame[frame.replication_id % 2 == parity].groupby('solution_id')[list(directions)].mean()
        fronts.append(set(half.index[nondominated_mask(half, directions)]))
    return {'front_odd': len(fronts[1]), 'front_even': len(fronts[0]), 'shared': len(fronts[0] & fronts[1]),
            'jaccard': len(fronts[0] & fronts[1]) / len(fronts[0] | fronts[1])}


def compare_objective_sets(frame, means, objective_sets):
    """tamano y estabilidad del frente, y mayor |spearman| entre objetivos dentro de uniformes."""
    rows = []
    uniform = means[means.family == 'uniform']
    for name, directions in objective_sets.items():
        spearman = correlation_table(uniform, directions, n_boot=1).spearman.abs().max()
        front = means[nondominated_mask(means, directions)]
        rows.append({'objectives': name, 'front_size': len(front), 'front_clustered': int(front.family.eq('clustered').sum()),
                     **front_stability(frame, directions), 'max_abs_spearman': spearman})
    return pd.DataFrame(rows).set_index('objectives')


def budget_table(wall_s_per_simulation, populations, generations, replications=SEARCH_REPLICATIONS):
    """cota superior sin cache: la poblacion inicial mas una descendencia por generacion."""
    rows = [{'population': p, 'generations': g, 'replications': replications, 'simulations': p * (g + 1) * replications,
             'hours': p * (g + 1) * replications * wall_s_per_simulation / 3600}
            for p in populations for g in generations]
    return pd.DataFrame(rows)


def main():
    from ..config import load_config
    root = Path(__file__).resolve().parents[4]
    config = load_config(root / 'config/project2/base.yaml')
    candidates = pd.read_csv(root / 'data/project2/processed/candidate_hive_sites.csv')
    table = sample_installations(candidates, config['K'], PILOT_UNIFORM, PILOT_CLUSTERED, PILOT_SEED)
    frame, meta = run_pilot(table, config)
    meta.update(pilot_seed=PILOT_SEED, n_uniform=PILOT_UNIFORM, n_clustered=PILOT_CLUSTERED)
    save_pilot(root / PILOT_DIRECTORY, table, frame, meta)
    print(meta)


if __name__ == '__main__':
    main()
