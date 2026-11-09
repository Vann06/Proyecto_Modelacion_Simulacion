"""Feasibility/data tests; not a claim of historical simulation validation."""
from pathlib import Path
import hashlib,json,sys,unittest
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from bee_sim.analysis.project2_historical_audit import (COLONIES,SOURCE_SHA256,extract_tables,
    annotate_observations,implied_hives,clustered_interval,require_historical_feasibility,HistoricalFeasibilityError)


class HistoricalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'results/project2/historical_validation'
        cls.records=pd.read_csv(ROOT/'data/project2/processed/historical_foraging.csv',dtype={'movie_id':str})
        cls.hives=pd.read_csv(ROOT/'data/project2/processed/historical_hives.csv')
        cls.report=json.loads((cls.out/'feasibility.json').read_text())

    def test_counts_ids_dates_and_flags_preserve_source_errors(self):
        d=self.records
        self.assertEqual(d.groupby('colony').size().to_dict(),COLONIES)
        self.assertTrue(d.record_id.is_unique);self.assertEqual(d.inside_project_window.sum(),216)
        self.assertEqual(d.distance_analysis_eligible.sum(),216);self.assertEqual(d.timed_analysis_eligible.sum(),215)
        self.assertEqual(d.year.unique().tolist(),[2017])
        self.assertEqual((~d.distance_valid).sum(),1);self.assertEqual((~d.clock_valid).sum(),2)
        self.assertEqual((~d.id_prefix_consistent).sum(),5);self.assertEqual(d.dance_id_duplicated.sum(),4)
        negative=d.loc[d.distance_m.lt(0)].iloc[0]
        self.assertEqual((negative.colony,int(negative.source_row),negative.distance_m),('Bygdoy',31,-2.9))
        self.assertEqual(d.date.min(),'2017-07-01');self.assertEqual(d.date.max(),'2017-08-14')

    def test_visual_fixture_matches_selected_cells(self):
        checks=json.loads((ROOT/'data/project2/historical_manual_checks.json').read_text(encoding='utf-8'))
        self.assertEqual(len(checks['checks']),20);self.assertEqual(checks['source_sha256'],SOURCE_SHA256)
        for expected in checks['checks']:
            row=self.records.loc[self.records.colony.eq(expected['colony'])&self.records.source_row.eq(expected['source_row'])].iloc[0]
            for key,value in expected.items():
                if isinstance(value,(int,float)):self.assertAlmostEqual(float(row[key]),value,places=7)
                else:self.assertEqual(row[key],value)

    @unittest.skipUnless((ROOT/'.build/historical/dietz_2018.pdf').exists(),'PDF no redistribuido: ejecutar --download-source para verificar extracción')
    def test_both_pdf_engines_agree_with_exported_cells(self):
        raw=extract_tables(ROOT/'.build/historical/dietz_2018.pdf')
        again=annotate_observations(raw)
        np.testing.assert_allclose(again.distance_m,self.records.distance_m,rtol=0,atol=0)
        self.assertEqual(again.record_id.tolist(),self.records.record_id.tolist())
        self.assertEqual(again.dance_id_source.tolist(),self.records.dance_id_source.tolist())

    def test_crs_and_hive_origins_remain_unverified_and_gate_blocks(self):
        self.assertTrue(self.records.source_crs.eq('UNCONFIRMED').all())
        self.assertFalse(self.records.spatially_verified.any())
        self.assertFalse(self.hives.placement_allowed_for_historical_simulation.any())
        self.assertFalse(self.report['ready_for_historical_simulation'])
        self.assertAlmostEqual(self.report['implied_ulleval_separation_source_units'],3.0101466,places=5)
        with self.assertRaises(HistoricalFeasibilityError):require_historical_feasibility(self.report)
        with self.assertRaises(HistoricalFeasibilityError):require_historical_feasibility({'ready_for_historical_simulation':True})

    def test_vector_inversion_and_nonnegative_distance_statistics(self):
        r=self.records.iloc[0]
        self.assertAlmostEqual(r.origin_x_implied,r.easting_source-r.distance_m*np.sin(r.heading_rad),places=7)
        self.assertAlmostEqual(r.origin_y_implied,r.northing_source-r.distance_m*np.cos(r.heading_rad),places=7)
        stats=pd.read_csv(self.out/'observed_distances.csv')
        a=stats.query("colony == 'Bygdoy' and scope == 'project_18_day_window'").iloc[0]
        self.assertAlmostEqual(a.mean_point_distance_m,783.4965517241377,places=8)
        self.assertTrue((stats.mean_cluster_bootstrap_ci95_high_m>=stats.mean_cluster_bootstrap_ci95_low_m).all())
        ulleval=stats.query("colony == 'Ulleval 1' and scope == 'project_18_day_window'").iloc[0]
        self.assertEqual(ulleval.n_above_3km,3);self.assertEqual(ulleval.n_valid_distances,97)

    def test_descriptive_bootstrap_repeats_and_is_not_a_new_simulation_bank(self):
        d=self.records.query("colony == 'Bygdoy' and distance_analysis_eligible")
        self.assertEqual(clustered_interval(d,'distance_m',n_boot=100),clustered_interval(d,'distance_m',n_boot=100))
        self.assertEqual(self.report['simulation_runs_executed'],0)
        self.assertFalse(self.report['new_simulation_seed_bank_created'])

    def test_conditional_coverage_has_explicit_hypotheses_and_preserves_rows(self):
        d=pd.read_csv(self.out/'destinations_crs_hypotheses.csv')
        self.assertEqual(len(d),432);self.assertEqual(set(d.assumed_epsg),{25832,32632})
        self.assertTrue(d.groupby('assumed_epsg').record_id.nunique().eq(216).all())
        a=d.query('assumed_epsg == 25832').set_index('record_id')
        b=d.query('assumed_epsg == 32632').set_index('record_id').loc[a.index]
        self.assertLess(np.hypot(a.project_x_m_conditional-b.project_x_m_conditional,
                                 a.project_y_m_conditional-b.project_y_m_conditional).max(),.01)
        coverage=pd.read_csv(self.out/'park_coverage_conditional.csv')
        self.assertTrue(coverage.percent_covered_conditional.between(0,100).all())
        self.assertTrue(coverage.status.str.contains('hypothesis').all())
        overlap=pd.read_csv(self.out/'overlap_comparability.csv')
        self.assertTrue(overlap.reproduced_value.isna().all())

    def test_published_posterior_summaries_not_claimed_as_point_summary_replication(self):
        d=pd.read_csv(self.out/'published_summary_check.csv')
        self.assertTrue(d.published_n.eq(d.recovered_n).all())
        self.assertTrue(d.comparison_status.str.contains('not_simulator_error').all())
        self.assertFalse(np.allclose(d.published_posterior_mean_m,d.appendix_mean_nonnegative_m))

    def test_nina_numeric_provenance_and_no_imputed_park_values(self):
        metadata=json.loads((self.out/'nina_numeric_audit.json').read_text(encoding='utf-8'))
        self.assertEqual(metadata['original_raster']['crs'],'EPSG:25832')
        self.assertEqual(metadata['original_raster']['resolution_projected_units'],[1.,1.])
        self.assertEqual(metadata['analysis_overview']['crs'],'EPSG:3857')
        self.assertFalse(metadata['full_tiff_downloaded']);self.assertFalse(metadata['out_of_range_values_clipped'])
        d=pd.read_csv(self.out/'nina_park_index_approximate.csv')
        self.assertEqual(len(d),737);self.assertEqual(d.raw_index_mean_approx.notna().sum(),686)
        self.assertTrue(d.loc[d.n_valid_overview_cells.eq(0),'raw_index_mean_approx'].isna().all())
        self.assertLess(d.raw_index_min_approx.min(),0);self.assertGreater(d.raw_index_max_approx.max(),1)
        self.assertTrue(d.semantic_direction.str.startswith('UNCONFIRMED').all())
        correlation=d[['raw_index_mean_approx','synthetic_initial_resource_share']].corr(method='spearman').iloc[0,1]
        self.assertAlmostEqual(correlation,metadata['spearman_rho_raw_index_vs_area_share'],places=12)

    def test_main_engine_identity_and_candidate_restrictions_are_unchanged(self):
        from bee_sim.project2.simulation import _engine_hash
        from bee_sim.project2 import load_config,simulate,with_parameters
        expected=json.loads((ROOT/'results/project2/react_demo/greedy.json').read_text(encoding='utf-8'))['provenance']['engine_hash']
        self.assertEqual(_engine_hash(),expected)
        cfg=with_parameters(load_config(ROOT/'config/project2/base.yaml'),K=3)
        with self.assertRaises(ValueError):simulate(['Bygdoy','Ulleval 1','Ulleval 2'],int(pd.read_csv(ROOT/'data/project2/processed/experiment_seeds.csv').seed.iloc[0]),cfg)
        with self.assertRaises(ValueError):with_parameters(cfg,seed_bank_file='historical_seeds.csv')
