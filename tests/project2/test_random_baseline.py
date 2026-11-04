from collections import Counter
from pathlib import Path
import json
import sys
import tempfile
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config, with_parameters
from bee_sim.project2.distance import load_landscape
from bee_sim.project2.metrics import RESULT_COLUMNS, write_results
from bee_sim.project2.strategies.random_baseline import select_sites, generate_installations, evaluate_installation


class RandomSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidates = load_landscape(load_config(ROOT / 'config/project2/base.yaml'))[0]
        cls.ids = set(cls.candidates.site_id)

    def test_exact_K_unique_sorted_from_catalog(self):
        sites = select_sites(self.candidates, 5, 123)
        self.assertEqual(len(sites), 5)
        self.assertEqual(len(set(sites)), 5)
        self.assertTrue(set(sites).issubset(self.ids))
        self.assertEqual(sites, tuple(sorted(sites)))

    def test_same_seed_same_installation_other_seed_differs(self):
        self.assertEqual(select_sites(self.candidates, 5, 123), select_sites(self.candidates, 5, 123))
        self.assertNotEqual(select_sites(self.candidates, 5, 123), select_sites(self.candidates, 5, 124))

    def test_only_site_id_matters_not_row_order(self):
        expected = select_sites(self.candidates, 5, 123)
        shuffled = self.candidates.sample(frac=1, random_state=0)
        self.assertEqual(select_sites(shuffled, 5, 123), expected)
        self.assertEqual(select_sites(self.candidates[['site_id']], 5, 123), expected)

    def test_invalid_K_or_seed_rejected(self):
        for K, seed in [(0, 1), (True, 1), (2.0, 1), (len(self.ids) + 1, 1), (5, -1), (5, True), (5, 1.5)]:
            with self.assertRaises(ValueError):
                select_sites(self.candidates, K, seed)

    def test_frequencies_cover_catalog_without_favorites(self):
        # seeds fijas: es determinista, no depende de un p-valor
        draws, K = 2000, 5
        counts = Counter(s for seed in range(draws) for s in select_sites(self.candidates, K, seed))
        expected = draws * K / len(self.ids)
        self.assertEqual(set(counts), self.ids)
        self.assertLess(max(counts.values()), 2 * expected)

    def test_installations_reproducible_and_traceable(self):
        first = generate_installations(self.candidates, 5, 3, 123)
        self.assertEqual(first, generate_installations(self.candidates, 5, 3, 123))
        self.assertEqual(list(first), ['random_001', 'random_002', 'random_003'])
        for i, item in enumerate(first.values()):
            self.assertEqual(item['optimizer_seed'], 123 + i)
            self.assertEqual(tuple(item['site_ids']), select_sites(self.candidates, 5, 123 + i))
        for n in [0, True, 1.5]:
            with self.assertRaises(ValueError):
                generate_installations(self.candidates, 5, n, 123)


class RandomEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # perfil reducido como en test_common_engine, solo para que corra rapido
        cls.cfg = with_parameters(load_config(ROOT / 'config/project2/base.yaml'), K=2,
            departures_per_day=4., initial_resource_total=20., day_minutes=60.)
        candidates = load_landscape(cls.cfg)[0]
        cls.installations = generate_installations(candidates, 2, 2, 123)

    def test_rows_follow_common_schema(self):
        rows = []
        for solution_id, item in self.installations.items():
            found, first = evaluate_installation(solution_id, item, self.cfg, 2)
            self.assertEqual(first['provenance']['config_hash'], self.cfg.config_hash)
            rows += found
        with tempfile.TemporaryDirectory() as folder:
            frame = write_results(rows, Path(folder) / 'random_results.csv')
            loaded = pd.read_csv(Path(folder) / 'random_results.csv')
        self.assertEqual(len(frame), 4)
        self.assertEqual(tuple(loaded.columns), RESULT_COLUMNS)
        self.assertTrue(loaded['method'].eq('RANDOM').all())
        self.assertEqual(sorted(loaded.replication_id.unique()), [1, 2])
        for solution_id, item in self.installations.items():
            part = loaded.loc[loaded.solution_id.eq(solution_id)]
            self.assertEqual(len(part), 2)
            self.assertTrue(part.optimizer_seed.eq(item['optimizer_seed']).all())
            self.assertTrue(part.site_ids.map(json.loads).map(lambda s: s == item['site_ids']).all())

    def test_replications_outside_bank_rejected(self):
        solution_id, item = next(iter(self.installations.items()))
        for count in [0, True, self.cfg['replications'] + 1]:
            with self.assertRaises(ValueError):
                evaluate_installation(solution_id, item, self.cfg, count)


if __name__ == '__main__':
    unittest.main()
