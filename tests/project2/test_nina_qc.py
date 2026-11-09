"""Offline checks for the bounded NINA investigation, not ecological validation."""
from pathlib import Path
import hashlib
import importlib.util
import json
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/project2/nina_quality_control'
spec = importlib.util.spec_from_file_location('nina_qc', ROOT/'scripts/project2_nina_qc.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class NinaQualityControlTests(unittest.TestCase):
    def test_stats_preserves_outliers_and_excludes_nodata(self):
        values=np.ma.masked_equal(np.array([-9999.,-.1,.4,1.1,np.nan]),-9999.)
        result=audit.stats(values)
        self.assertEqual(result['n_valid'],3)
        self.assertEqual(result['n_below_0'],1)
        self.assertEqual(result['n_above_1'],1)
        self.assertEqual(result['min'],-.1)

    def test_sample_design_and_aggregated_ranges(self):
        manifest=pd.read_csv(OUT/'sample_manifest.csv')
        self.assertEqual(len(manifest),24)
        self.assertTrue(manifest.sample_id.is_unique)
        self.assertEqual(manifest.design.value_counts().to_dict(),
                         {'systematic_4x4':16,'targeted_overview_extreme':8})
        ranges=json.loads((OUT/'sample_range_summary.json').read_text())
        self.assertEqual(ranges['original']['n_below_0']+ranges['original']['n_above_1'],0)
        self.assertGreater(ranges['cog']['n_below_0'],0)
        self.assertGreater(ranges['overview']['n_above_1'],0)
        rows=pd.read_csv(OUT/'sample_ranges.csv')
        for name,g in rows.groupby('dataset'):
            self.assertEqual(int(g.n_valid.sum()),ranges[name]['n_valid'])

    def test_resampling_comparisons_use_same_valid_pixels(self):
        rows=pd.read_csv(OUT/'native_to_cog_checks.csv')
        self.assertTrue(rows.groupby('sample_id').n_pairs.nunique().eq(1).all())
        summary=pd.read_csv(OUT/'resampling_summary.csv').set_index('resampling_test')
        self.assertLess(summary.loc['cubic','mae_direct'],summary.loc['nearest','mae_direct'])
        self.assertGreater(summary.loc['cubic','mae_one_minus_source'],100*summary.loc['cubic','mae_direct'])
        rows=pd.read_csv(OUT/'cog_to_overview_checks.csv')
        self.assertTrue(rows.groupby('sample_id').n_pairs.nunique().eq(1).all())
        self.assertTrue(rows.n_pairs.le(16).all())

    def test_all_missing_parks_accounted_for_without_imputation(self):
        old=pd.read_csv(ROOT/'results/project2/historical_validation/nina_park_index_approximate.csv')
        current=pd.read_csv(OUT/'missing_51_parks.csv')
        self.assertEqual(set(old.loc[old.n_valid_overview_cells.eq(0),'patch_id']),set(current.patch_id))
        self.assertEqual(len(current),51)
        self.assertTrue(current.patch_id.is_unique)
        self.assertEqual(int(current.native_valid_centers.gt(0).sum()),30)
        self.assertEqual(int(current.native_valid_touched.gt(0).sum()),49)
        tiny=current[current.cause.eq('native_valid_touched_only_no_centers')]
        self.assertEqual(len(tiny),19)
        self.assertTrue(tiny.area_m2.lt(1).all())
        self.assertTrue(tiny.native_mean.isna().all())

    def test_georeferencing_and_source_identity(self):
        source=json.loads((OUT/'original_metadata.json').read_text())
        cog=json.loads((OUT/'cog_metadata.json').read_text())
        self.assertEqual(source['profile']['crs'],'EPSG:25832')
        self.assertEqual(cog['profile']['crs'],'EPSG:3857')
        self.assertEqual(source['profile']['nodata'],cog['profile']['nodata'])
        self.assertEqual(source['transform'][0],1.)
        identity=json.loads((OUT/'source_identity.json').read_text())
        self.assertTrue(identity['cog']['url'].endswith('.tif.cog'))
        self.assertTrue(identity['original']['etag'])

    def test_decision_does_not_enable_ranking_or_simulation(self):
        decision=json.loads((OUT/'decision.json').read_text())
        self.assertEqual(decision['decision'],'NO APTO')
        self.assertFalse(decision['direction_confirmed'])
        self.assertFalse(decision['exact_2017_to_2022_processing_lineage_confirmed'])
        self.assertEqual(decision['simulations_run'],0)
        self.assertEqual(decision['installations_classified'],0)
        hypotheses=pd.read_csv(OUT/'scale_hypotheses_not_proof.csv')
        self.assertFalse(hypotheses.identifies_transform.any())

    def test_cached_samples_have_recorded_hashes(self):
        manifest=pd.read_csv(OUT/'sample_cache_manifest.csv')
        if not all((ROOT/p).exists() for p in manifest.file):
            self.skipTest('Ignored raster cache absent; no fresh sample verification claimed')
        for row in manifest.itertuples():
            path=ROOT/row.file
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row.sha256)


if __name__ == '__main__':
    unittest.main()
