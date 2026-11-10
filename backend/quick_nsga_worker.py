"""Spawn-safe entry point; uses the unmodified NSGA-II and common simulator."""
import argparse
from dataclasses import asdict
import time
from types import SimpleNamespace
import numpy as np
import pandas as pd
from . import service
from .quick_nsga import LABEL, MAX_SIMULATIONS, job_path, read_json, write_json
from bee_sim.project2.strategies.nsga2 import (NSGA2Parameters, SimulationEvaluator,
    run_nsga2, freeze_front, objective_directions)
from bee_sim.project2.contract import validate_hive_sites
from bee_sim.project2.config import ENGINE_VERSION


def execute(job_id):
    path = job_path(service.ROOT, job_id)
    begun = time.perf_counter()
    try:
        request = read_json(path / 'request.json')
        config = service.scenario_config(SimpleNamespace(**request))
        params = NSGA2Parameters(('total_resource_obtained', 'mean_distance_m'), 8, 5, .90, .20, 2, 2026)
        catalog = pd.read_csv(service.ROOT / 'data/project2/processed/candidate_hive_sites.csv').site_id.tolist()
        directions = objective_directions(config, params.objectives)
        class ProgressEvaluator(SimulationEvaluator):
            def __call__(self, installations):
                rows = super().__call__(installations)
                saved = read_json(path / 'checkpoint.json') if (path / 'checkpoint.json').exists() else {}
                write_json(path / 'status.json', {'status': 'running', 'simulations': self.simulations,
                    'installations': len(self.cache), 'elapsed_s': time.perf_counter() - begun,
                    'generation': saved.get('generation', 0), 'front_size': len(saved.get('archive', []))})
                return rows
        with ProgressEvaluator(config, 2, workers=2, path=path / 'evaluations.jsonl',
                               simulation_budget=MAX_SIMULATIONS) as evaluate:
            identity = dict(config_hash=config.config_hash, engine_hash=evaluate.engine_hash,
                input_hash=evaluate.input_hash, parameters_hash=params.parameters_hash)
            write_json(path / 'metadata.json', {'label': LABEL, 'request': request,
                'parameters': dict(config.parameters), 'parameter_provenance': config.records,
                'optimizer': asdict(params), 'identity': identity, 'engine_version': ENGINE_VERSION,
                'search_seeds': evaluate.seeds, 'max_simulations': MAX_SIMULATIONS,
                'interpretation': 'synthetic_RU; search averages over two seeds; not historical evaluation or a global optimum'})
            result = run_nsga2(catalog, request['K'], params, directions, evaluate, identity, path)
            if not result['finished']:
                raise ValueError('Búsqueda incompleta; no se publica el frente')
            publish = {**result, 'archive': {sites: score for sites, score in result['archive'].items()
                       if score[1] == 0 and np.isfinite(score[0]).all()}}
            frozen = freeze_front(publish, params, directions, identity, path / 'front.json')
            solutions = []
            for index, item in enumerate(frozen, 1):
                sites = validate_hive_sites(item['site_ids'], catalog, request['K'])
                means = item['search_means']
                # Undefined objectives are not valid final points (e.g. no trips with radius/resource zero).
                if not all(np.isfinite(v) for v in means.values()):
                    continue
                rows = evaluate([tuple(sites)])[tuple(sites)]
                metric_means = {key: float(np.mean([r[key] for r in rows]))
                    if all(r[key] is not None and np.isfinite(r[key]) for r in rows) else None for key in rows[0]}
                solutions.append({**item, 'solution_id': f'quick_{index:03d}', 'K': len(sites),
                    'search_metrics': metric_means})
            result['history'].to_csv(path / 'history.csv', index=False)
            write_json(path / 'result.json', {'label': LABEL, 'job_id': job_id, 'K': request['K'],
                'request': request, 'parameters': dict(config.parameters), 'identity': identity, 'engine_version': ENGINE_VERSION,
                'solutions': solutions, 'search_replication_ids': [1, 2],
                'empty_reason': None if solutions else 'Ninguna instalación tiene ambos objetivos definidos. Revisa recursos, radio y viajes.'})
            write_json(path / 'status.json', {'status': 'completed', 'generation': 5,
                'simulations': evaluate.simulations, 'installations': len(evaluate.cache),
                'elapsed_s': time.perf_counter() - begun, 'front_size': len(solutions)})
    except Exception as exc:
        write_json(path / 'status.json', {'status': 'failed', 'elapsed_s': time.perf_counter() - begun,
            'error': f'{type(exc).__name__}: {exc}. No se publica un frente definitivo.'})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-id', required=True)
    execute(parser.parse_args().job_id)
