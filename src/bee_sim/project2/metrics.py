"""Única implementación de las nueve métricas; sin callbacks por estrategia."""
import hashlib
import json
import numpy as np
import pandas as pd

METRIC_NAMES = ('total_resource_obtained', 'mean_resource_per_hive', 'min_resource_per_hive',
                'mean_distance_m', 'total_distance_m', 'p95_distance_m', 'competition_pressure',
                'hive_balance_jain', 'patches_used_count')
CONTRACT_DIGEST = '290ae72c96171b1ab6055b939488527f02d4eab04cfd52082f8394b18730706b'


def validate_metrics_contract(root):
    path = root / 'data/project2/processed/simulation_metrics_contract.csv'
    frame = pd.read_csv(path)
    digest = hashlib.sha256(json.dumps(frame.to_dict('records'), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if tuple(frame.metric) != METRIC_NAMES or digest != CONTRACT_DIGEST:
        raise ValueError('El contrato de métricas cambió; no se permite una definición por estrategia')
    return digest


def summarize(trips, per_hive):
    values = per_hive.resource_delivered.to_numpy(float)
    if not len(values) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Se requiere una fila válida por cada colmena')
    distances = trips.one_way_distance_m.to_numpy(float)
    attempts = trips.loc[trips.foraging_attempt]
    total = float(values.sum())
    result = {
        'total_resource_obtained': total,
        'mean_resource_per_hive': float(values.mean()),
        'min_resource_per_hive': float(values.min()),
        'mean_distance_m': float(distances.mean()) if len(distances) else None,
        'total_distance_m': float(distances.sum()),
        'p95_distance_m': float(np.quantile(distances, .95, method='linear')) if len(distances) else None,
        'competition_pressure': float(attempts.other_colonies_active_at_foraging_start.gt(0).mean()) if len(attempts) else None,
        'hive_balance_jain': float(np.clip(total**2 / (len(values) * np.square(values).sum()), 1 / len(values), 1)) if total else None,
        'patches_used_count': int(trips.loc[trips.resource_consumed.gt(0), 'patch_id'].nunique()),
    }
    if tuple(result) != METRIC_NAMES:
        raise ValueError('Esquema de métricas incorrecto')
    return result


RESULT_COLUMNS = ('method', 'scenario', 'K', 'replication_id', 'seed', 'site_ids', *METRIC_NAMES,
                  'config_hash', 'engine_version', 'engine_hash', 'input_hash', 'mode', 'resource_unit',
                  'solution_id', 'optimizer_seed', 'metric_contract_hash', 'rng')
METHODS = ('RANDOM', 'GREEDY', 'NSGA2', 'SMOKE_FIXED_SITES')


def result_row(method, replication_id, result, config, solution_id='solution_001', optimizer_seed=None):
    """Formato único; el método es etiqueta, nunca altera el motor."""
    if method not in METHODS or tuple(result['metrics']) != METRIC_NAMES:
        raise ValueError('Método o conjunto de métricas no contractual')
    p = result['provenance']
    if p['config_hash'] != config.config_hash or len(result['per_hive']) != config['K']:
        raise ValueError('El resultado no corresponde a la configuración')
    bank = pd.read_csv(config.root / config['seed_bank_file']).set_index('replication_id')
    if replication_id not in bank.index or int(bank.loc[replication_id, 'seed']) != p['seed']:
        raise ValueError('replication_id y seed no corresponden al banco compartido')
    sites = sorted(result['per_hive'].site_id.tolist())
    row = {'method': method, 'scenario': config.scenario, 'K': config['K'],
           'replication_id': int(replication_id), 'seed': p['seed'],
           'site_ids': json.dumps(sites, separators=(',', ':')), **result['metrics'],
           'config_hash': p['config_hash'], 'engine_version': p['engine_version'],
           'engine_hash': p['engine_hash'], 'input_hash': p['input_hash'], 'mode': p['mode'], 'resource_unit': p['resource_unit'],
           'solution_id': solution_id, 'optimizer_seed': optimizer_seed,
           'metric_contract_hash': p['metric_contract_hash'], 'rng': p['rng']}
    return {key: row[key] for key in RESULT_COLUMNS}


def write_results(rows, path):
    from pathlib import Path
    frame = pd.DataFrame(rows)
    if not len(frame) or tuple(frame.columns) != RESULT_COLUMNS:
        raise ValueError('Resultados vacíos o esquema distinto del común')
    if frame.duplicated(['method', 'scenario', 'K', 'replication_id', 'seed', 'solution_id']).any():
        raise ValueError('Réplicas duplicadas; use un solution_id distinto por instalación')
    for col in ['config_hash', 'engine_hash', 'input_hash', 'metric_contract_hash', 'mode']:
        if frame[col].nunique() != 1:
            raise ValueError('No mezclar contratos/configuraciones diferentes en un archivo comparable')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    frame.to_csv(temp, index=False, lineterminator='\n', na_rep='')
    temp.replace(path)
    return frame
