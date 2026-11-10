import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config
from bee_sim.project2.simulation import _engine_hash
from bee_sim.project2.strategies import nsga2_pilot as pilot


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(ROOT / 'config/project2/base.yaml')
        cls.candidates = pd.read_csv(ROOT / 'data/project2/processed/candidate_hive_sites.csv')

    def test_sampling_is_valid_unique_and_reproducible(self):
        first = pilot.sample_installations(self.candidates, 5, 20, 10, 7)
        second = pilot.sample_installations(self.candidates.sample(frac=1, random_state=1), 5, 20, 10, 7)
        self.assertEqual(first.site_ids.tolist(), second.site_ids.tolist())
        self.assertEqual(first.family.value_counts().to_dict(), {'uniform': 20, 'clustered': 10})
        catalog = set(self.candidates.site_id)
        self.assertTrue(all(len(set(s)) == 5 and set(s) <= catalog for s in first.site_ids))
        self.assertEqual(len({tuple(s) for s in first.site_ids}), 30)

    def test_clustered_installations_are_tighter(self):
        xy = self.candidates.set_index('site_id')[['x_m', 'y_m']]
        table = pilot.sample_installations(self.candidates, 5, 30, 30, 7)
        spread = table.site_ids.map(lambda s: xy.loc[s].std().sum())
        self.assertLess(spread[table.family == 'clustered'].median(), spread[table.family == 'uniform'].median())

    def test_impossible_sampling_fails_instead_of_looping(self):
        with self.assertRaises(ValueError):
            pilot.sample_installations(self.candidates.head(5), 5, 2, 0, 7)

    def test_reserved_replications_are_rejected(self):
        with self.assertRaises(ValueError):
            pilot.run_pilot(pd.DataFrame(), self.cfg, replications=31)

    def test_variance_components_recover_signal_and_ignore_common_seed_effect(self):
        rng = np.random.default_rng(1)
        n, r = 400, 30
        x = rng.normal(0, 2, (n, 1)) + rng.normal(0, 50, (1, r)) + rng.normal(0, 1, (n, r))
        frame = pd.DataFrame({'solution_id': np.repeat(np.arange(n), r), 'replication_id': np.tile(np.arange(r), n),
                              'm': x.ravel()})
        c = pilot.variance_components(frame, 'm')
        self.assertAlmostEqual(c['sd_between'], 2, delta=.25)
        self.assertAlmostEqual(c['sd_noise'], 1, delta=.05)

    def test_pure_noise_has_no_reliability(self):
        rng = np.random.default_rng(2)
        frame = pd.DataFrame({'solution_id': np.repeat(np.arange(300), 30), 'replication_id': np.tile(np.arange(30), 300),
                              'm': rng.normal(size=9000)})
        self.assertLess(pilot.variance_components(frame, 'm')['reliability'], .3)

    def test_nondominated_mask_respects_directions(self):
        means = pd.DataFrame({'gain': [10., 8., 5., 10.], 'cost': [5., 2., 6., 5.]})
        mask = pilot.nondominated_mask(means, {'gain': 'maximize', 'cost': 'minimize'})
        self.assertEqual(mask.tolist(), [True, True, False, True])

    def test_nondominated_mask_rejects_undefined_objectives(self):
        with self.assertRaises(ValueError):
            pilot.nondominated_mask(pd.DataFrame({'a': [1., None]}), {'a': 'minimize'})

    def test_front_stability_detects_identical_and_disjoint_halves(self):
        directions = {'m': 'minimize'}
        same = pd.DataFrame({'solution_id': ['a', 'a', 'b', 'b'], 'replication_id': [1, 2, 1, 2], 'm': [1., 1., 2., 2.]})
        swapped = same.assign(m=[1., 2., 2., 1.])
        self.assertEqual(pilot.front_stability(same, directions)['jaccard'], 1)
        self.assertEqual(pilot.front_stability(swapped, directions)['jaccard'], 0)

    def test_small_pilot_runs_and_roundtrips(self):
        import tempfile
        table = pilot.sample_installations(self.candidates, self.cfg['K'], 1, 1, 7)
        frame, meta = pilot.run_pilot(table, self.cfg, replications=2, workers=2)
        self.assertEqual(len(frame), 4)
        self.assertEqual(frame.seed.nunique(), 2)
        with tempfile.TemporaryDirectory() as folder:
            pilot.save_pilot(folder, table, frame, meta)
            loaded, again, _ = pilot.load_pilot(folder, self.cfg)
        self.assertEqual(loaded.site_ids.tolist(), table.site_ids.tolist())
        self.assertEqual(again.total_resource_obtained.tolist(), frame.total_resource_obtained.tolist())

    def test_strategy_package_does_not_change_engine_hash(self):
        original = _engine_hash()
        with tempfile.TemporaryDirectory(dir=Path(pilot.__file__).parent) as directory:
            Path(directory, 'new_strategy.py').write_text('VALUE = 123', encoding='utf-8')
            self.assertEqual(_engine_hash(), original)



if __name__ == '__main__':
    unittest.main()
