from pathlib import Path
import json
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import simulate, load_config, with_parameters
from bee_sim.project2.distance import load_landscape
from bee_sim.project2.metrics import METRIC_NAMES, validate_metrics_contract, result_row, write_results


class CommonEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = with_parameters(load_config(ROOT / 'config/project2/base.yaml'), K=2,
            departures_per_day=4., initial_resource_total=20., day_minutes=60.)
        cls.candidates, cls.patches, cls.distances, cls.manifest = load_landscape(cls.cfg)
        cls.sites = cls.candidates.site_id.iloc[:2].tolist()
        cls.seed = int(pd.read_csv(ROOT / cls.cfg['seed_bank_file']).seed.iloc[0])
        cls.result = simulate(cls.sites, cls.seed, cls.cfg)

    def test_repeat_and_permutation_same_seed(self):
        again = simulate(self.sites[::-1], self.seed, self.cfg)
        self.assertEqual(self.result['metrics'], again['metrics'])
        self.assertEqual(self.result['provenance'], again['provenance'])
        for key in ['trips', 'events', 'resource_log', 'per_hive']:
            pd.testing.assert_frame_equal(self.result[key], again[key], check_exact=True)

    def test_exact_K_valid_unique_and_invalid_inputs_rejected(self):
        hives = self.result['per_hive']
        self.assertEqual(len(hives), self.cfg['K'])
        self.assertTrue(hives.site_id.is_unique)
        self.assertTrue(set(hives.site_id).issubset(set(self.candidates.site_id)))
        for ids in [[self.sites[0]] * 2, ['invalid', self.sites[0]], self.sites[:1]]:
            with self.assertRaises(ValueError):
                simulate(ids, self.seed, self.cfg)

    def test_nonnegative_and_balance_and_continuity(self):
        log = self.result['resource_log']
        self.assertTrue((log[['R_before', 'consumption', 'regeneration', 'R_after']] >= 0).all().all())
        self.assertTrue(log.consumption.le(log.R_before).all())
        np.testing.assert_allclose(log.R_after, log.R_before - log.consumption + log.regeneration)
        for _, group in log.groupby('patch_id', sort=False):
            np.testing.assert_array_equal(group.R_before.iloc[1:], group.R_after.iloc[:-1])
        self.assertAlmostEqual(log.consumption.sum(), self.result['trips'].resource_consumed.sum())
        self.assertAlmostEqual(self.result['per_hive'].resource_delivered.sum(), self.result['trips'].resource_delivered.sum())
        self.assertTrue(self.result['trips'].resource_delivered.le(self.result['trips'].resource_consumed).all())

    def test_distances_and_return_horizon(self):
        self.assertTrue(np.isfinite(self.distances).all() and (self.distances >= 0).all())
        trips = self.result['trips']
        self.assertTrue(trips.one_way_distance_m.between(0, self.cfg['max_foraging_distance_m']).all())
        self.assertTrue(trips.loc[trips.returned, 'return_min'].le(self.cfg['day_minutes']).all())
        self.assertTrue(trips.loc[trips.foraging_attempt, 'foraging_end_min'].le(self.cfg['day_minutes']).all())

    def test_all_metrics_fixed_and_strategy_cannot_supply_rules(self):
        self.assertEqual(tuple(self.result['metrics']), METRIC_NAMES)
        for name in ['metrics', 'metric_function', 'selection_rule', 'engine_version', 'overlap_policy']:
            with self.assertRaises(ValueError):
                with_parameters(self.cfg, **{name: 'override'})
        with self.assertRaises(TypeError):
            simulate(self.sites, self.seed, self.cfg.parameters)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dest = root / 'data/project2/processed'
            dest.mkdir(parents=True)
            frame = pd.read_csv(ROOT / 'data/project2/processed/simulation_metrics_contract.csv')
            frame.loc[0, 'direction'] = 'minimize'
            frame.to_csv(dest / 'simulation_metrics_contract.csv', index=False)
            with self.assertRaises(ValueError):
                validate_metrics_contract(root)

    def test_no_resources_no_fake_trips_or_undefined_metrics(self):
        result = simulate(self.sites, self.seed, with_parameters(self.cfg, initial_resource_total=0., regeneration_rate=0.))
        self.assertEqual(len(result['trips']), 0)
        self.assertEqual(result['metrics']['total_resource_obtained'], 0)
        self.assertIsNone(result['metrics']['mean_distance_m'])
        self.assertIsNone(result['metrics']['competition_pressure'])
        self.assertIsNone(result['metrics']['hive_balance_jain'])
        self.assertTrue(result['events'].event.eq('no_available_patch').all())

    def test_CRN_opportunities_do_not_shift_when_resource_branch_changes(self):
        empty = simulate(self.sites, self.seed, with_parameters(self.cfg, initial_resource_total=0.))
        def opportunities(result):
            e = result['events']
            return e.loc[e.event.isin(['departure', 'no_available_patch']),
                         ['date', 'time_min', 'hive_slot', 'trip_slot']].sort_values(
                             ['date', 'hive_slot', 'trip_slot']).reset_index(drop=True)
        pd.testing.assert_frame_equal(opportunities(self.result), opportunities(empty), check_exact=True)

    def test_overlap_policy_conserves_union_area_without_double_count(self):
        self.assertAlmostEqual(self.patches.exclusive_area_m2.sum(), self.manifest['union_area_m2'], places=3)
        self.assertLess(self.patches.exclusive_area_m2.sum(), self.manifest['sum_original_areas_m2'])
        positive = self.patches.exclusive_area_m2.gt(0)
        log = self.result['resource_log'].groupby('patch_id').first().reindex(self.patches.patch_id)
        self.assertTrue(log.loc[~positive.to_numpy(), 'R_before'].eq(0).all())

    def test_same_config_hash_and_common_result_schema(self):
        before = self.cfg.config_hash
        row = result_row('RANDOM', 1, self.result, self.cfg)
        alternate = result_row('GREEDY', 1, self.result, self.cfg)
        self.assertEqual({k: v for k, v in row.items() if k != 'method'}, {k: v for k, v in alternate.items() if k != 'method'})
        self.assertEqual(before, self.cfg.config_hash)
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / 'results.csv'
            write_results([row], dest)
            loaded = pd.read_csv(dest)
            self.assertEqual(json.loads(loaded.site_ids.iloc[0]), sorted(self.sites))
            self.assertEqual(loaded['mode'].iloc[0], 'synthetic')
            changed = dict(row, replication_id=2, seed=123, input_hash='different_input')
            with self.assertRaises(ValueError):
                write_results([row, changed], dest)

    def test_reject_calibrated_mode_and_wrong_horizon(self):
        with self.assertRaises(ValueError):
            with_parameters(self.cfg, simulation_end='2017-09-30')
        with tempfile.TemporaryDirectory() as folder:
            import yaml
            content = yaml.safe_load((ROOT / 'config/project2/base.yaml').read_text(encoding='utf-8'))
            content['mode'] = 'calibrated'
            path = Path(folder) / 'config.yaml'
            path.write_text(yaml.safe_dump(content), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_config(path, root=ROOT)


if __name__ == '__main__':
    unittest.main()
