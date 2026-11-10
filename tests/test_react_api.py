import json
from pathlib import Path
import sys,unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from fastapi.testclient import TestClient
from backend.main import app,RUN_LOCK
from bee_sim.analysis.project2_validation import prepare_observations,benchmark,percentage_change


class ReactApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=TestClient(app)

    def test_read_only_endpoints_and_archive_identity(self):
        for name in ['health','overview','comparison','validation','sensitivity','landscape']:
            with self.subTest(name=name):self.assertEqual(self.client.get('/api/'+name).status_code,200)
        if (ROOT/'frontend/dist/index.html').exists():
            self.assertEqual(self.client.get('/').status_code,200)
            self.assertIn('id="root"',self.client.get('/').text)
        comparison=self.client.get('/api/comparison').json()
        self.assertEqual(comparison['audit'][0]['engine_version'],'project2-synthetic-1.1.0')
        self.assertEqual(comparison['metadata']['physical_front_installations'],32)
        self.assertEqual(len(self.client.get('/api/landscape').json()['parks']['features']),737)

    def test_archived_demo_never_runs_the_engine(self):
        with patch('backend.service.simulate',side_effect=AssertionError('must not simulate')):
            result=self.client.get('/api/demo/GREEDY')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['kind'],'archived_demo_v111')
        self.assertEqual(result.json()['provenance']['engine_version'],'project2-synthetic-1.1.1')

    def test_bad_parameters_and_foreign_sites_are_rejected(self):
        for request in [{'K':0},{'K':True},{'K':1.5},{'radius_m':-1},{'method':'NSGA2','K':3},
                        {'method':'NSGA2','solution_id':'pareto_999'},{'replication_id':101},
                        {'arbitrary_callback':'x'},{'method':'MANUAL','site_ids':['foreign']},
                        {'method':'MANUAL','K':2,'site_ids':['a','a']}]:
            with self.subTest(request=request):self.assertEqual(self.client.post('/api/runs',json=request).status_code,422)

    def test_seed_repeats_zero_resource_and_conservation(self):
        request={'method':'GREEDY','resource_factor':0,'replication_id':31}
        a=self.client.post('/api/runs',json=request).json()
        b=self.client.post('/api/runs',json=request).json()
        self.assertEqual(a,b)
        self.assertEqual(a['metrics']['total_resource_obtained'],0)
        self.assertEqual(a['trips'],[])
        self.assertTrue(all(min(d['initial'])>=0 and min(d['final'])>=0 for d in a['days']))

    def test_busy_run_and_download_allowlist(self):
        with RUN_LOCK:self.assertEqual(self.client.post('/api/runs',json={}).status_code,429)
        self.assertEqual(self.client.get('/api/download/comparison').status_code,200)
        self.assertEqual(self.client.get('/api/download/unknown').status_code,404)


class EmpiricalEvidenceTests(unittest.TestCase):
    def test_site_split_no_leakage_bootstrap_seeds_and_units(self):
        flowers,sessions,meta=prepare_observations(ROOT)
        self.assertEqual(meta['floral_rows'],593);self.assertEqual(meta['visitation_rows'],1297)
        self.assertEqual(int(flowers.eligible.sum()),99);self.assertEqual(int(sessions.eligible.sum()),216)
        bank=pd.read_csv(ROOT/'data/project2/processed/experiment_seeds.csv').iloc[30:60]
        seeds=[(int(r.replication_id),int(r.seed)) for r in bank.itertuples()]
        split,test,replicates,errors=benchmark(flowers,'flowers','flores/m²',seeds,n_boot=100)
        self.assertFalse(set(split.query("split == 'calibration'").trap_number)&set(test.trap_number))
        self.assertEqual(replicates.replication_id.nunique(),30)
        self.assertTrue(np.isfinite(errors.estimate).all())
        self.assertTrue((errors.ci95_high>=errors.ci95_low).all())
        self.assertIsNone(percentage_change(1,0));self.assertEqual(percentage_change(110,100),10)

    def test_sensitivity_keeps_30_common_seeds_per_condition_and_no_fake_K_nsga(self):
        df=pd.read_csv(ROOT/'results/project2/sensitivity_v111/replicates.csv')
        self.assertEqual(len(df),1200)
        self.assertEqual(df.engine_version.unique().tolist(),['project2-synthetic-1.1.1'])
        self.assertEqual(df.engine_hash.nunique(),1)
        for _,group in df.groupby(['experiment_condition','method']):
            self.assertEqual(set(group.replication_id),set(range(31,61)))
            self.assertFalse(group.seed.duplicated().any())
        self.assertFalse(df.query("experiment_condition in ['K3','K8']").method.eq('NSGA2').any())
