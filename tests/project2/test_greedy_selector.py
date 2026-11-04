from pathlib import Path
import inspect
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config, with_parameters
from bee_sim.project2.strategies import greedy_baseline as gb
from bee_sim.project2.strategies.greedy_baseline import GreedyParams, greedy_select, select_sites


class GreedyCoreTests(unittest.TestCase):
    def test_k_ids_valid_and_unique_with_all_zero_scores(self):
        ids = [f's{i}' for i in range(6)]
        order, steps = greedy_select(np.zeros((6, 4)), np.zeros((6, 4), bool), ids, 4, 1.0)
        self.assertEqual(len(order), 4)
        self.assertEqual(len(set(order)), 4)
        self.assertTrue(set(order) <= set(ids))
        self.assertEqual(order, ids[:4])            # empate total: menor site_id primero

    def test_ties_stable_by_site_id(self):
        ids = ['a', 'b', 'c', 'd']
        values = np.ones((4, 3))
        cov = np.ones((4, 3), bool)
        first, _ = greedy_select(values, cov, ids, 3, 0.0)
        second, _ = greedy_select(values.copy(), cov.copy(), ids, 3, 0.0)
        self.assertEqual(first, second)
        self.assertEqual(first, ['a', 'b', 'c'])

    def test_overlap_penalty_prefers_new_coverage(self):
        ids = ['a', 'b', 'c']
        values = np.array([[10., 10., 0.], [10., 10., 0.], [0., 0., 12.]])
        cov = values > 0
        no_penalty, _ = greedy_select(values, cov, ids, 2, 0.0)
        penalized, _ = greedy_select(values, cov, ids, 2, 1.0)
        self.assertEqual(no_penalty, ['a', 'b'])
        self.assertEqual(penalized, ['a', 'c'])

    def test_chosen_gains_non_increasing(self):
        rng = np.random.default_rng(3)
        values = rng.random((30, 20))
        cov = values > .3
        values = np.where(cov, values, 0.)
        ids = [f's{i:02d}' for i in range(30)]
        _, steps = greedy_select(values, cov, ids, 8, 1.0)
        gains = steps[steps.chosen_at_step].marginal_gain.to_numpy()
        self.assertTrue((np.diff(gains) <= 1e-12).all())

    def test_invalid_inputs_rejected(self):
        ids = ['a', 'b']
        v = np.ones((2, 2))
        c = np.ones((2, 2), bool)
        for bad_k in [0, 3, True]:
            with self.assertRaises(ValueError):
                greedy_select(v, c, ids, bad_k, 1.0)
        with self.assertRaises(ValueError):
            greedy_select(v, c, ['b', 'a'], 1, 1.0)
        with self.assertRaises(ValueError):
            GreedyParams(overlap_penalty=-1)

    def test_no_future_information_and_no_randomness(self):
        source = inspect.getsource(gb)
        code = '\n'.join(l for l in source.splitlines() if not l.strip().startswith('#'))
        for forbidden in ['simulate(', 'resource_log', 'import random', 'default_rng', 'np.random', 'trips']:
            self.assertNotIn(forbidden, code.split('"""', 2)[2], forbidden)


class GreedyOnCommonLandscapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(ROOT / 'config/project2/base.yaml')

    def test_exact_k_valid_deterministic(self):
        a, b = select_sites(self.cfg), select_sites(self.cfg)
        self.assertEqual(a['site_ids'], b['site_ids'])
        self.assertEqual(len(a['site_ids']), self.cfg['K'])
        self.assertEqual(len(set(a['site_ids'])), self.cfg['K'])
        self.assertTrue(set(a['site_ids']) <= set(a['candidates'].site_id))
        self.assertEqual(a['site_ids'], sorted(a['site_ids']))

    def test_follows_common_k(self):
        cfg = with_parameters(self.cfg, K=3)
        self.assertEqual(len(select_sites(cfg)['site_ids']), 3)

    def test_params_are_separate_from_common_config_hash(self):
        before = self.cfg.config_hash
        select_sites(self.cfg, GreedyParams(distance_exponent=1.0, overlap_penalty=2.0))
        self.assertEqual(before, self.cfg.config_hash)


if __name__ == '__main__':
    unittest.main()
