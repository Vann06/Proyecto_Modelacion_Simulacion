"""API safety and frozen-scenario checks; real timing runs use the acceptance script."""
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from fastapi.testclient import TestClient
from backend.main import app, RunRequest, RUN_LOCK
from backend import service
from backend.quick_nsga import QuickJobs, write_json, job_path, selected_run, OUTPUT
from bee_sim.project2.simulation import _engine_hash


class QuickNsgaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.job_id = 'a'*32
        self.path = self.root/OUTPUT/self.job_id
        self.path.mkdir(parents=True)
        self.request = RunRequest(method='NSGA2', K=8, radius_m=1500, resource_factor=1.5).model_dump()
        write_json(self.path/'request.json', self.request)
        self.manager = QuickJobs(self.root, threading.Lock())

    def tearDown(self):
        self.temp.cleanup()

    def test_provisional_front_not_returned_after_restart(self):
        write_json(self.path/'status.json', {'status':'running','generation':2})
        write_json(self.path/'result.json', {'solutions':[{'site_ids':['fake']} ]})
        state = self.manager.status(self.job_id)
        self.assertEqual(state['status'],'interrupted')
        self.assertNotIn('result',state)

    def test_path_traversal_and_unknown_jobs_rejected(self):
        for value in ['../nsga2','x'*32,'a'*31,'b'*32]:
            with self.assertRaises(ValueError):job_path(self.root,value)

    def test_requests_and_concurrency(self):
        client = TestClient(app)
        for request in [{'K':True},{'K':0},{'K':21},{'resource_factor':-1},{'method':'RANDOM'}]:
            self.assertEqual(client.post('/api/quick-nsga2',json=request).status_code,422)
        with RUN_LOCK:
            self.assertEqual(client.post('/api/quick-nsga2',json={'method':'NSGA2','K':8}).status_code,429)
        self.assertEqual(client.get('/api/quick-nsga2/../unknown').status_code,404)
        self.assertEqual(client.post('/api/quick-nsga2/'+self.job_id+'/simulate',json={'solution_id':'quick_001','replication_id':1}).status_code,422)

    def test_timeout_never_publishes_partial_front_and_releases_lock(self):
        write_json(self.path/'status.json', {'status':'running'})
        proc = Mock();proc.poll.return_value=None
        self.manager.active = (self.job_id,proc,0)
        self.manager.run_lock.acquire()
        with patch.object(self.manager,'_stop'),patch('backend.quick_nsga.TIMEOUT_SECONDS',-1):
            self.manager._watch(self.job_id,proc,0)
        self.assertEqual(self.manager.status(self.job_id)['status'],'failed')
        self.assertIsNone(self.manager.active)
        self.assertTrue(self.manager.run_lock.acquire(blocking=False))
        self.manager.run_lock.release()

    def test_incomplete_solution_not_simulated(self):
        write_json(self.path/'status.json',{'status':'failed'})
        with patch.object(service,'ROOT',self.root),patch.object(service,'run') as run:
            with self.assertRaises(ValueError):selected_run(self.job_id,'quick_001',31)
            run.assert_not_called()

    def test_undefined_objectives_publish_an_empty_front_not_infinite_points(self):
        import warnings
        from backend import quick_nsga_worker as worker
        from bee_sim.project2.metrics import METRIC_NAMES
        class EmptyEvaluator:
            def __init__(inner,*args,**kwargs):
                inner.cache={};inner.simulations=0;inner.engine_hash='test';inner.input_hash='test'
                inner.seeds=[(1,1),(2,2)]
            def __enter__(inner):return inner
            def __exit__(inner,*args):pass
            def __call__(inner,installations):
                rows={}
                for sites in installations:
                    key=tuple(sites)
                    if key not in inner.cache:inner.cache[key]=True;inner.simulations+=2
                    rows[key]=[{**dict.fromkeys(METRIC_NAMES,0),'mean_distance_m':None}]*2
                return rows
        with patch.object(worker,'job_path',return_value=self.path),patch.object(worker,'SimulationEvaluator',EmptyEvaluator),warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            worker.execute(self.job_id)
        import json
        final=json.loads((self.path/'result.json').read_text(encoding='utf-8'))
        front=(self.path/'front.json').read_text(encoding='utf-8')
        self.assertEqual(final['solutions'],[])
        self.assertTrue(final['empty_reason'])
        self.assertNotIn('Infinity',front)

    def test_individual_run_uses_frozen_K_sites_and_config(self):
        from types import SimpleNamespace
        cfg = service.scenario_config(SimpleNamespace(**self.request))
        sites = ['site'+str(i) for i in range(8)]
        write_json(self.path/'status.json',{'status':'completed'})
        write_json(self.path/'result.json',{'request':self.request,'identity':{
            'config_hash':cfg.config_hash,'engine_hash':_engine_hash(),'input_hash':'test'},
            'solutions':[{'solution_id':'quick_001','site_ids':sites}]})
        with patch.object(service,'ROOT',self.root),patch.object(service,'scenario_config',return_value=cfg),patch('bee_sim.project2.strategies.nsga2.current_input_hash',return_value='test'),patch.object(service,'run',return_value={'provenance':{}}) as simulate:
            result=selected_run(self.job_id,'quick_001',32)
            options=simulate.call_args.args[0]
            self.assertEqual((options.K,options.radius_m,options.resource_factor),(8,1500,1.5))
            self.assertEqual(options.site_ids,sites)
            self.assertEqual(options.replication_id,32)
            self.assertEqual(result['kind'],'quick_nsga_individual_run')
            with patch('bee_sim.project2.strategies.nsga2.current_input_hash',return_value='changed'):
                with self.assertRaises(ValueError):selected_run(self.job_id,'quick_001',32)


if __name__=='__main__':unittest.main()
