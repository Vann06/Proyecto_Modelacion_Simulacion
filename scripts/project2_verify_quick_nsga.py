"""Explicit real-engine acceptance run for the quick UI mode, never historical evaluation.

Run from the repository root. Creates 5 bounded searches (K3/5/8, repeat K3,
changed K3), individual runs and a small verification report. No holdout campaign.
"""
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from fastapi.testclient import TestClient
from backend.main import app, QUICK_JOBS


def protected():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in ['src', 'config', 'data', 'results/project2']
            for p in (ROOT / directory).rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and 'quick_nsga2' not in p.parts}


def main():
    before = protected()
    report = {'label': 'Acceptance tests of exploratory quick NSGA-II', 'searches': [], 'checks': {}}
    client = TestClient(app)
    def search(K, **overrides):
        request = {'method': 'NSGA2', 'K': K, **overrides}
        start = time.perf_counter()
        response = client.post('/api/quick-nsga2', json=request)
        assert response.status_code == 202, response.text
        job_id = response.json()['job_id']
        assert client.post('/api/quick-nsga2', json=request).status_code == 429
        while True:
            state = client.get('/api/quick-nsga2/' + job_id).json()
            if state['status'] in ('completed', 'failed', 'interrupted'):
                break
            time.sleep(.5)
        assert state['status'] == 'completed', state
        while QUICK_JOBS.active:
            time.sleep(.1)
        result = state['result']
        valid = set(__import__('pandas').read_csv(ROOT / 'data/project2/processed/candidate_hive_sites.csv').site_id)
        for solution in result['solutions']:
            assert len(solution['site_ids']) == len(set(solution['site_ids'])) == K
            assert set(solution['site_ids']) <= valid
        assert result['solutions'], state
        assert state['simulations'] <= 96
        record = dict(K=K, overrides=overrides, job_id=job_id, wall_s=time.perf_counter()-start,
            worker_s=state['elapsed_s'], installations=state['installations'], simulations=state['simulations'],
            solutions=len(result['solutions']), result_hash=hashlib.sha256(json.dumps(result['solutions'],sort_keys=True).encode()).hexdigest())
        report['searches'].append(record)
        print(json.dumps(record), flush=True)
        return result
    try:
        a = search(3)
        b = search(5)
        c = search(8)
        repeat = search(3)
        assert a['solutions'] == repeat['solutions']
        report['checks']['reproducible_K3'] = True
        changed = search(3, resource_factor=1.5, radius_m=1500)
        meta = json.loads((ROOT / 'results/project2/quick_nsga2' / changed['job_id'] / 'metadata.json').read_text(encoding='utf-8'))
        assert meta['parameters']['initial_resource_total'] == 1500
        assert meta['parameters']['max_foraging_distance_m'] == 1500
        assert meta['search_seeds'][0][0] == 1 and meta['search_seeds'][1][0] == 2
        assert a['identity']['config_hash'] != changed['identity']['config_hash']
        report['checks']['modified_resource_and_radius_used'] = True
        for result in [a, c]:
            for solution in result['solutions'][:2]:
                response = client.post('/api/quick-nsga2/'+result['job_id']+'/simulate',
                    json={'solution_id': solution['solution_id'], 'replication_id': 31})
                assert response.status_code == 200, response.text
                run = response.json()
                assert set(run['sites']) == set(solution['site_ids']) and len(run['sites']) == result['K']
                assert run['provenance']['individual_replication_id'] == 31
                assert run['kind'] == 'quick_nsga_individual_run'
        report['checks']['different_solutions_individual_runs_K3_K8'] = True
        for method,K in [('RANDOM',3), ('GREEDY',8), ('NSGA2',5)]:
            response = client.post('/api/runs',json={'method':method,'K':K})
            assert response.status_code == 200, response.text
            assert len(response.json()['sites']) == K
            if method == 'NSGA2':
                front = json.loads((ROOT / 'results/project2/nsga2/front.json').read_text())
                sites = next(s['site_ids'] for s in front['solutions'] if s['solution_id']=='pareto_047')
                assert response.json()['sites'] == sites
        report['checks']['RANDOM_K3_GREEDY_K8_historical_pareto047_K5'] = True
    finally:
        after = protected()
        report['protected_files_checked'] = len(before)
        report['protected_changes'] = [p for p in before.keys() | after.keys() if before.get(p) != after.get(p)]
        dest = ROOT / 'docs/project2/QUICK_NSGA_VERIFICATION.json'
        dest.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        QUICK_JOBS.close()
    assert not report['protected_changes'], report['protected_changes']


if __name__ == '__main__':
    main()
