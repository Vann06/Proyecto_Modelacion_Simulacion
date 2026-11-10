"""Comparación descriptiva de la cohorte archivada, sin volver a optimizar."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from bee_sim.project2.contract import bootstrap_ci
from bee_sim.project2.metrics import METRIC_NAMES

IDENTITY = ['config_hash', 'engine_hash', 'input_hash', 'metric_contract_hash', 'engine_version', 'K', 'scenario', 'mode', 'resource_unit']
FILES = {'RANDOM': 'random_results.csv', 'GREEDY': 'greedy_results.csv', 'NSGA2': 'nsga2_results.csv'}


def load_archived(root):
    root = Path(root)
    frames, audit = {}, []
    bank = pd.read_csv(root / 'data/project2/processed/experiment_seeds.csv').set_index('replication_id').seed
    expected = set(range(31, 101))
    for method, filename in FILES.items():
        path = root / 'results/project2' / filename
        frame = pd.read_csv(path)
        required = set(IDENTITY + list(METRIC_NAMES) + ['method', 'replication_id', 'seed', 'site_ids', 'solution_id'])
        if not required.issubset(frame.columns) or not frame.method.eq(method).all():
            raise ValueError(f'Esquema o método inválido: {filename}')
        if any(frame[col].nunique(dropna=False) != 1 for col in IDENTITY):
            raise ValueError(f'{filename}: mezcla identidades incompatibles')
        if not frame.seed.eq(frame.replication_id.map(bank)).all():
            raise ValueError(f'{filename}: seed y réplica no coinciden con el banco')
        if frame.duplicated(['solution_id', 'replication_id']).any():
            raise ValueError(f'{filename}: réplicas duplicadas')
        test = frame.loc[frame.replication_id.isin(expected)].copy()
        for solution, group in test.groupby('solution_id'):
            if set(group.replication_id) != expected or group.site_ids.nunique() != 1:
                raise ValueError(f'{method}/{solution}: evaluación reservada incompleta o instalación cambiante')
        if test.empty:
            raise ValueError(f'{method}: no hay réplicas reservadas 31–100')
        frames[method] = test
        audit.append({'method': method, 'file': filename, 'original_rows': len(frame), 'holdout_rows': len(test),
                      'solutions': test.solution_id.nunique(), 'holdout_replications': 70,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **{c: frame[c].iloc[0] for c in IDENTITY}})
    first = frames['RANDOM'].iloc[0]
    if any(any(frame[col].iloc[0] != first[col] for col in IDENTITY) for frame in frames.values()):
        raise ValueError('Los métodos pertenecen a cohortes distintas; reevaluar juntos, no mezclar hashes')
    return frames, pd.DataFrame(audit)


def representative_front(root):
    """Elección ilustrativa solo por medias de búsqueda congeladas, sin usar holdout."""
    front = json.loads((Path(root) / 'results/project2/nsga2/front.json').read_text())
    solutions = front['solutions']
    objectives = ['total_resource_obtained', 'mean_distance_m', 'competition_pressure']
    x = np.array([[s['search_means'][m] for m in objectives] for s in solutions], dtype=float)
    x[:, 0] *= -1
    span = np.ptp(x, axis=0)
    normalized = (x - x.min(axis=0)) / np.where(span > 0, span, 1)
    distance = np.linalg.norm(normalized, axis=1)
    index = min(range(len(solutions)), key=lambda i: (distance[i], solutions[i]['solution_id']))
    return solutions[index], front


def physical_signature(site_ids, candidates):
    rows = candidates.set_index('site_id').loc[sorted(site_ids)]
    # Multiconjunto: dos colmenas colocalizadas siguen contando dos veces.
    return json.dumps(sorted(tuple(x) for x in rows[['x_m', 'y_m']].to_numpy(float)), separators=(',', ':'))


def build_comparison(root, n_boot=2000):
    root = Path(root)
    frames, audit = load_archived(root)
    selected, front = representative_front(root)
    if selected['solution_id'] not in set(frames['NSGA2'].solution_id):
        raise ValueError('La solución congelada no tiene evaluación reservada')
    identity = front.get('identity', {})
    if any(identity.get(col) != frames['NSGA2'][col].iloc[0] for col in ['config_hash', 'engine_hash']):
        raise ValueError('El frente y sus resultados tienen identidades distintas')
    per_seed = {
        'RANDOM': frames['RANDOM'].groupby('replication_id')[list(METRIC_NAMES)].mean(),
        'GREEDY': frames['GREEDY'].set_index('replication_id')[list(METRIC_NAMES)].sort_index(),
        'NSGA2': frames['NSGA2'].loc[frames['NSGA2'].solution_id.eq(selected['solution_id'])].set_index('replication_id')[list(METRIC_NAMES)].sort_index()}
    summary, differences = [], []
    for method, values in per_seed.items():
        for metric in METRIC_NAMES:
            finite = values[metric].dropna().to_numpy(float)
            ci = bootstrap_ci(finite, seed=2017, n_boot=n_boot) if len(finite) >= 2 else {}
            summary.append({'method': method, 'metric': metric, 'mean': finite.mean() if len(finite) else np.nan,
                            'ci95_low': ci.get('ci_lower', np.nan), 'ci95_high': ci.get('ci_upper', np.nan),
                            'n_seeds': len(finite), 'undefined_seeds': len(values) - len(finite),
                            'solution': 'mean_of_30_installations' if method == 'RANDOM' else selected['solution_id'] if method == 'NSGA2' else frames['GREEDY'].solution_id.iloc[0],
                            'interval_scope': 'conditional_on_fixed_installations_common_seed_variation'})
    for left, right in [('GREEDY', 'RANDOM'), ('NSGA2', 'RANDOM'), ('NSGA2', 'GREEDY')]:
        for metric in METRIC_NAMES:
            paired = (per_seed[left][metric] - per_seed[right][metric]).dropna().to_numpy(float)
            ci = bootstrap_ci(paired, seed=2017, n_boot=n_boot) if len(paired) >= 2 else {}
            differences.append({'contrast': f'{left}-{right}', 'metric': metric, 'difference': ci.get('estimate', np.nan),
                                'ci95_low': ci.get('ci_lower', np.nan), 'ci95_high': ci.get('ci_upper', np.nan),
                                'n_pairs': len(paired), 'undefined_pairs': 70 - len(paired), 'bootstrap_seed': 2017})
    candidates = pd.read_csv(root / 'data/project2/processed/candidate_hive_sites.csv')
    installations = frames['NSGA2'].groupby('solution_id')[list(METRIC_NAMES)].mean().reset_index()
    sites_by_id = {s['solution_id']: s['site_ids'] for s in front['solutions']}
    installations['physical_signature'] = installations.solution_id.map(lambda s: physical_signature(sites_by_id[s], candidates))
    installations['physical_duplicate'] = installations.physical_signature.duplicated()
    history = pd.read_csv(root / 'results/project2/nsga2/history.csv')
    metadata = {'selected_nsga_solution': selected['solution_id'],
                'selection_rule': 'Equal-weight normalized distance to ideal using frozen SEARCH means only; illustrative choice',
                'holdout_already_inspected': True, 'interpretation': 'descriptive synthetic comparison, not ecological validation or preregistered confirmatory test',
                'original_front_solutions': len(installations), 'physical_front_installations': installations.physical_signature.nunique(),
                'candidate_ids': len(candidates), 'unique_candidate_coordinates': len(candidates[['x_m', 'y_m']].drop_duplicates()),
                'search_simulations': int(history.new_simulations.sum()), 'search_recorded_hours': float(history.elapsed_s.sum() / 3600),
                'random_ci_limitation': 'Intervals condition on the 30 saved RANDOM installations; between-placement variability is shown separately, not 2100 independent replicates',
                'multiple_metrics': '95% intervals are pointwise, not simultaneous; no p-value-based winner declaration'}
    return {'summary': pd.DataFrame(summary), 'paired': pd.DataFrame(differences), 'audit': audit,
            'nsga_installations': installations, 'metadata': metadata, 'frames': frames, 'per_seed': per_seed}
