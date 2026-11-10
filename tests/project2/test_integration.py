"""Regresiones de integraciÃ³n: referencia histÃ³rica, cache y cohortes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config, simulate
from bee_sim.project2.strategies import nsga2
from bee_sim.analysis.project2_comparison import build_comparison, physical_signature


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(ROOT / 'config/project2/base.yaml')
        cls.reference = json.loads((Path(__file__).parent / 'fixtures/engine_110_reference.json').read_text())

    def test_optimized_engine_exactly_matches_preoptimization_reference(self):
        r = self.reference
        result = simulate(r['sites'], r['seed'], self.cfg)
        self.assertEqual(result['metrics'], r['metrics'])
        for name, expected in r['tables'].items():
            actual = hashlib.sha256(result[name].to_csv(index=False, lineterminator='\n').encode()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_cache_adds_missing_seeds_and_canonicalizes_site_order(self):
        sites = tuple(self.reference['sites'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cache.jsonl'
            # Exercise production scheduling/persistence without worker startup cost.
            class SequentialPool:
                def __init__(self, **kwargs): pass
                def map(self, fn, tasks, **kwargs): return map(fn, tasks)
                def shutdown(self): pass
            with patch.object(nsga2, 'ProcessPoolExecutor', SequentialPool):
                with nsga2.SimulationEvaluator(self.cfg, 1, path=path) as first:
                    first([sites, sites[::-1]])
                    self.assertEqual(first.simulations, 1)
                with path.open('a', encoding='utf-8') as f:
                    f.write('{"interrupted')
                with nsga2.SimulationEvaluator(self.cfg, 2, path=path) as second:
                    rows = second([sites])
                    self.assertEqual(second.simulations, 1)
                    self.assertEqual(len(rows[sites]), 2)
                self.assertEqual(len(list(Path(folder).glob('*.interrupted-*.jsonl'))), 1)
                with nsga2.SimulationEvaluator(self.cfg, 2, path=path) as third:
                    self.assertEqual(third([sites]), rows)
                    self.assertEqual(third.simulations, 0)

    def test_budget_stops_before_starting_workers(self):
        with nsga2.SimulationEvaluator(self.cfg, 2, simulation_budget=1) as evaluator:
            with self.assertRaises(nsga2.EvaluationBudgetExceeded):
                evaluator([tuple(self.reference['sites'])])
            self.assertIsNone(evaluator.pool)
            self.assertEqual(evaluator.simulations, 0)

    def test_front_with_stale_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'front.json'
            path.write_text(json.dumps({'identity': {'engine_hash': 'stale'}}))
            with self.assertRaises(ValueError):
                nsga2.evaluate_frozen_front(path, self.cfg, Path(folder) / 'out.csv')
            self.assertFalse((Path(folder) / 'out.csv').exists())

    def test_archived_comparison_uses_only_common_seeds_and_compatible_identity(self):
        data = build_comparison(ROOT, n_boot=100)
        for frame in data['frames'].values():
            self.assertEqual(set(frame.replication_id), set(range(31, 101)))
        self.assertTrue(data['summary'].n_seeds.eq(70).all())
        self.assertTrue(data['paired'].n_pairs.eq(70).all())
        self.assertEqual(data['metadata']['physical_front_installations'], 32)
        original = pd.read_csv
        with patch('bee_sim.analysis.project2_comparison.pd.read_csv', wraps=original) as reader:
            def incompatible(path, *args, **kwargs):
                frame = original(path, *args, **kwargs)
                if str(path).endswith('greedy_results.csv'):
                    frame['engine_hash'] = 'other-engine'
                return frame
            reader.side_effect = incompatible
            with self.assertRaises(ValueError):
                build_comparison(ROOT, n_boot=10)

    def test_physical_signature_preserves_colocated_multiplicity(self):
        candidates = pd.DataFrame({'site_id': ['a','b','c'], 'x_m': [1.,1.,2.], 'y_m': [0.,0.,0.]})
        self.assertEqual(physical_signature(['a','c'], candidates), physical_signature(['c','b'], candidates))
        self.assertNotEqual(physical_signature(['a','b'], candidates), physical_signature(['a'], candidates))
