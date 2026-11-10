import numpy as np
import unittest
from bee_sim.project2.contract import validate_hive_sites, event_rng, resource_step, bootstrap_ci


class Project2ContractTests(unittest.TestCase):
    def test_sites_require_exact_valid_unique_K(self):
        self.assertEqual(validate_hive_sites(["b", "a"], ["a", "b", "c"], 2), ("a", "b"))
        for sites, k in [(["a", "a"], 2), (["x"], 1), (["a"], 2), (["a"], True), ("a", 1)]:
            with self.assertRaises(ValueError):
                validate_hive_sites(sites, ["a", "b"], k)


    def test_event_streams_reproduce_and_do_not_desynchronize_other_processes(self):
        expected = event_rng(2017, 0, 0, 0, "nectar").random(12)
        event_rng(2017, 0, 0, 0, "flowers").random(1000)
        self.assertTrue(np.array_equal(expected, event_rng(2017, 0, 0, 0, "nectar").random(12)))
        self.assertFalse(np.array_equal(expected, event_rng(2017, 0, 0, 1, "nectar").random(12)))
        self.assertFalse(np.array_equal(expected, event_rng(2018, 0, 0, 0, "nectar").random(12)))
        with self.assertRaises(ValueError):
            event_rng(2017, -1, 0, 0, "nectar")


    def test_resource_balance_and_invalid_overdraft(self):
        self.assertTrue(np.array_equal(resource_step([0, 2, 10], [0, 1, 4], [1, 0, 2]), [1, 1, 8]))
        for r, c, g in [([1], [2], [0]), ([1], [-1], [0]), ([np.nan], [0], [0]),
                        ([1, 2], [0], [0, 0]), ([1], [0], [-1])]:
            with self.assertRaises(ValueError):
                resource_step(r, c, g)


    def test_bootstrap_reproducible_and_paired_identical_results_have_zero_difference(self):
        result = bootstrap_ci([1, 2, 3, 4], seed=2017, n_boot=500)
        self.assertEqual(result, bootstrap_ci([1, 2, 3, 4], seed=2017, n_boot=500))
        self.assertTrue(result["estimate"] == 2.5 and result["ci_lower"] <= 2.5 <= result["ci_upper"])
        paired = bootstrap_ci(np.zeros(30), seed=2017, n_boot=100)
        self.assertTrue(paired["estimate"] == paired["ci_lower"] == paired["ci_upper"] == 0)
        with self.assertRaises(ValueError):
            bootstrap_ci([1, np.nan], seed=2017)
