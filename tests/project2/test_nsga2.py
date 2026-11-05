import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config
from bee_sim.project2.metrics import METRIC_NAMES
from bee_sim.project2.strategies import nsga2

DIRECTIONS = {'total_resource_obtained': 'maximize', 'mean_distance_m': 'minimize'}
CATALOG = [f's{i:02d}' for i in range(12)]


def params(**values):
    base = dict(objectives=tuple(DIRECTIONS), population=8, generations=6, crossover_rate=.9,
                mutation_rate=.3, search_replications=2, optimizer_seed=11)
    return nsga2.NSGA2Parameters(**{**base, **values})


class FakeEvaluator:
    """objetivos analiticos; no llama al motor, cuenta evaluaciones como simulate."""

    def __init__(self):
        self.simulations, self.seen = 0, []

    def __call__(self, installations):
        result = {}
        for installation in installations:
            numbers = [int(s[1:]) for s in installation]
            if installation not in self.seen:
                self.seen.append(installation)
                self.simulations += 1
            result[installation] = [{'total_resource_obtained': float(sum(n * n for n in numbers)),
                                     'mean_distance_m': float(sum((n - 3) ** 2 for n in numbers))}]
        return result


def exact_front(K):
    installations = list(itertools.combinations(sorted(CATALOG), K))
    fake = FakeEvaluator()
    x = np.array([nsga2.aggregate(fake(installations)[i], DIRECTIONS)[0] for i in installations])
    return {tuple(row) for row in x[nsga2.nondominated_fronts(x, [0] * len(x))[0]]}


class OperatorTests(unittest.TestCase):
    def rng(self, seed=1):
        return np.random.default_rng(seed)

    def test_repair_handles_duplicates_foreign_and_excess_ids(self):
        for sites in [('s01', 's01'), ('ajeno', 's02'), tuple(CATALOG), ()]:
            fixed = nsga2.repair(sites, CATALOG, 5, self.rng())
            self.assertEqual(len(set(fixed)), 5)
            self.assertLessEqual(set(fixed), set(CATALOG))
            self.assertEqual(list(fixed), sorted(fixed))

    def test_repair_fails_when_catalog_is_too_small(self):
        with self.assertRaises(ValueError):
            nsga2.repair((), CATALOG[:3], 5, self.rng())

    def test_crossover_keeps_common_sites_and_only_uses_parent_sites(self):
        a, b = ('s00', 's01', 's02', 's03', 's04'), ('s00', 's01', 's07', 's08', 's09')
        for seed in range(30):
            child = nsga2.crossover(a, b, 5, self.rng(seed))
            self.assertLessEqual({'s00', 's01'}, set(child))
            self.assertLessEqual(set(child), set(a) | set(b))
            self.assertEqual(len(set(child)), 5)

    def test_identical_parents_are_a_valid_crossover(self):
        a = ('s00', 's01', 's02', 's03', 's04')
        self.assertEqual(nsga2.crossover(a, a, 5, self.rng()), a)

    def test_mutation_never_creates_duplicates(self):
        a = ('s00', 's01', 's02', 's03', 's04')
        for seed in range(30):
            self.assertEqual(len(set(nsga2.mutate(a, CATALOG, 1, self.rng(seed)))), 5)
        self.assertEqual(nsga2.mutate(a, CATALOG, 0, self.rng()), a)

    def test_initial_population_is_unique_and_checks_the_space(self):
        population = nsga2.initial_population(CATALOG, 5, 20, self.rng())
        self.assertEqual(len(set(population)), 20)
        with self.assertRaises(ValueError):
            nsga2.initial_population(CATALOG[:6], 5, 7, self.rng())


class RankingTests(unittest.TestCase):
    def test_fronts_match_hand_example(self):
        x = np.array([[1., 5.], [2., 2.], [5., 1.], [3., 3.], [6., 6.]])
        fronts = nsga2.nondominated_fronts(x, [0] * 5)
        self.assertEqual([f.tolist() for f in fronts], [[0, 1, 2], [3], [4]])

    def test_equal_solutions_do_not_dominate_each_other(self):
        x = np.array([[1., 1.], [1., 1.]])
        self.assertEqual(nsga2.nondominated_fronts(x, [0, 0])[0].tolist(), [0, 1])

    def test_undefined_solution_loses_to_any_defined_one(self):
        good, _ = nsga2.aggregate([{'a': 9., 'b': 9.}], {'a': 'minimize', 'b': 'minimize'})
        empty, violation = nsga2.aggregate([{'a': None, 'b': 1.}], {'a': 'minimize', 'b': 'minimize'})
        self.assertEqual(violation, 1)
        self.assertTrue(np.isinf(empty[0]))
        fronts = nsga2.nondominated_fronts(np.array([good, empty]), [0, violation])
        self.assertEqual([f.tolist() for f in fronts], [[0], [1]])

    def test_maximized_objective_changes_sign(self):
        means, _ = nsga2.aggregate([{'gain': 4., 'cost': 1.}, {'gain': 6., 'cost': 3.}],
                                   {'gain': 'maximize', 'cost': 'minimize'})
        self.assertEqual(means.tolist(), [-5., 2.])

    def test_crowding_favors_extremes_and_handles_constant_objective(self):
        x = np.array([[0., 1.], [1., 1.], [2., 1.], [10., 1.]])
        distance = nsga2.crowding_distance(x)
        self.assertTrue(np.isinf(distance[[0, 3]]).all())
        self.assertGreater(distance[2], distance[1])

    def test_survivors_keep_front_and_exact_size(self):
        x = np.array([[1., 5.], [2., 2.], [5., 1.], [3., 3.], [6., 6.]])
        names = [(str(i),) for i in range(5)]
        self.assertEqual(nsga2.select_survivors(names, x, [0] * 5, 3), [('0',), ('1',), ('2',)])
        self.assertEqual(len(nsga2.select_survivors(names, x, [0] * 5, 4)), 4)


class SearchTests(unittest.TestCase):
    def search(self, p=None, **kwargs):
        return nsga2.run_nsga2(CATALOG, 5, p or params(), DIRECTIONS, FakeEvaluator(), **kwargs)

    def test_individuals_stay_valid_every_run(self):
        result = self.search()
        self.assertEqual(len(set(result['population'])), 8)
        for installation in result['population']:
            self.assertEqual(len(set(installation)), 5)
            self.assertLessEqual(set(installation), set(CATALOG))

    def test_same_seed_reproduces_and_other_seed_differs(self):
        first, second = self.search(), self.search()
        other = self.search(params(optimizer_seed=12))
        self.assertEqual(first['population'], second['population'])
        pd.testing.assert_frame_equal(first['history'].drop(columns='elapsed_s'), second['history'].drop(columns='elapsed_s'))
        self.assertNotEqual(first['population'], other['population'])

    def test_catalog_order_does_not_change_the_search(self):
        shuffled = nsga2.run_nsga2(CATALOG[::-1], 5, params(), DIRECTIONS, FakeEvaluator())
        self.assertEqual(self.search()['population'], shuffled['population'])

    def test_search_reaches_exact_front_on_enumerable_problem(self):
        expected = exact_front(5)
        result = self.search(params(population=60, generations=40))
        found = {tuple(x) for x, _ in result['archive'].values()}
        self.assertLessEqual(found, expected)
        self.assertGreaterEqual(len(found) / len(expected), .95)

    def test_archive_stays_exact_when_front_is_larger_than_population(self):
        expected = exact_front(5)
        for seed in range(5):
            result = self.search(params(population=40, generations=100, optimizer_seed=seed))
            self.assertLessEqual({tuple(x) for x, _ in result['archive'].values()}, expected)

    def test_elitism_never_loses_the_best_objective(self):
        history = self.search(params(generations=15))['history']
        self.assertTrue(history.best_total_resource_obtained.is_monotonic_increasing)
        self.assertTrue(history.best_mean_distance_m.is_monotonic_decreasing)

    def test_resume_equals_uninterrupted_search(self):
        identity = {'id': 'a'}
        with tempfile.TemporaryDirectory() as folder:
            nsga2.run_nsga2(CATALOG, 5, params(), DIRECTIONS, FakeEvaluator(), identity, folder, stop_after=2)
            resumed = nsga2.run_nsga2(CATALOG, 5, params(), DIRECTIONS, FakeEvaluator(), identity, folder)
        straight = self.search()
        self.assertEqual(resumed['population'], straight['population'])
        self.assertEqual(sorted(resumed['archive']), sorted(straight['archive']))
        self.assertTrue(resumed['finished'])

    def test_checkpoint_from_other_experiment_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            nsga2.run_nsga2(CATALOG, 5, params(), DIRECTIONS, FakeEvaluator(), {'id': 'a'}, folder, stop_after=1)
            with self.assertRaises(ValueError):
                nsga2.run_nsga2(CATALOG, 5, params(), DIRECTIONS, FakeEvaluator(), {'id': 'b'}, folder)

    def test_population_cannot_exceed_space_even_near_exhaustion(self):
        result = nsga2.run_nsga2(CATALOG[:6], 5, params(population=6), DIRECTIONS, FakeEvaluator())
        self.assertEqual(len(set(result['population'])), 6)

    def test_front_is_frozen_once_and_only_when_finished(self):
        p, fake = params(), FakeEvaluator()
        partial = nsga2.run_nsga2(CATALOG, 5, p, DIRECTIONS, fake, stop_after=1)
        done = nsga2.run_nsga2(CATALOG, 5, p, DIRECTIONS, fake)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'front.json'
            with self.assertRaises(ValueError):
                nsga2.freeze_front(partial, p, DIRECTIONS, {}, path)
            solutions = nsga2.freeze_front(done, p, DIRECTIONS, {}, path)
            self.assertGreater(solutions[0]['search_means']['total_resource_obtained'], 0)
            with self.assertRaises(ValueError):
                nsga2.freeze_front(done, p, DIRECTIONS, {}, path)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(ROOT / 'config/project2/base.yaml')

    def test_shipped_parameters_are_valid_and_use_contract_directions(self):
        p = nsga2.load_parameters(ROOT / nsga2.PARAMETERS_FILE)
        self.assertEqual(nsga2.objective_directions(self.cfg, p.objectives), {
            'total_resource_obtained': 'maximize', 'mean_distance_m': 'minimize', 'competition_pressure': 'minimize'})

    def test_reserved_replications_and_report_only_objectives_are_rejected(self):
        with self.assertRaises(ValueError):
            params(search_replications=31)
        with self.assertRaises(ValueError):
            nsga2.objective_directions(self.cfg, ('patches_used_count', 'mean_distance_m'))
        with self.assertRaises(ValueError):
            nsga2.evaluate_frozen_front('front.json', self.cfg, 'x.csv', replications=range(30, 40))

    def test_frozen_front_uses_common_schema_and_reserved_seed(self):
        candidates = pd.read_csv(ROOT / 'data/project2/processed/candidate_hive_sites.csv')
        sites = sorted(candidates.site_id)[:self.cfg['K']]
        front = {'optimizer_seed': 11, 'solutions': [{'solution_id': 'pareto_001', 'site_ids': sites}]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'front.json'
            path.write_text(json.dumps(front), encoding='utf-8')
            frame = nsga2.evaluate_frozen_front(path, self.cfg, Path(folder) / 'r.csv', replications=[31], workers=1)
        self.assertEqual(frame.replication_id.tolist(), [31])
        self.assertEqual(frame.method.tolist(), ['NSGA2'])

    def test_evaluator_cache_survives_restart_and_ignores_truncated_line(self):
        candidates = pd.read_csv(ROOT / 'data/project2/processed/candidate_hive_sites.csv')
        installation = tuple(sorted(candidates.site_id)[:self.cfg['K']])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'evaluations.jsonl'
            with nsga2.SimulationEvaluator(self.cfg, 2, 2, path) as evaluate:
                first = evaluate([installation])
                evaluate([installation])
                self.assertEqual(evaluate.simulations, 2)
            with path.open('a', encoding='utf-8') as file:
                file.write('{"incompleta')
            with nsga2.SimulationEvaluator(self.cfg, 2, 2, path) as evaluate:
                self.assertEqual(evaluate([installation]), first)
                self.assertEqual(evaluate.simulations, 0)
        self.assertEqual(set(first[installation][0]), set(METRIC_NAMES))


if __name__ == '__main__':
    unittest.main()
