"""Read-only delivery checks against archived files. No new experiments."""
from pathlib import Path
import hashlib
import json
import sys
import unittest
from unittest.mock import patch
import pandas as pd
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from backend.main import app
from backend.service import display_name


class DeliveryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)

    def test_display_labels_repair_encoding_without_changing_source_names(self):
        self.assertEqual(display_name('GjÃ¸rstadgaten'),'Gjørstadgaten')
        self.assertEqual(display_name('Gjørstadgaten'),'Gjørstadgaten')
        landscape=self.client.get('/api/landscape').json()
        source=pd.read_csv(ROOT/'data/project2/processed/spatial_patches.csv').set_index('patch_id')
        for feature in landscape['parks']['features']:
            row=feature['properties']
            expected=source.loc[row['patch_id'],'Navn']
            if isinstance(expected,str):self.assertEqual(row['Navn'],expected)

    def test_read_endpoints_do_not_call_simulator_and_preserve_versions(self):
        with patch('backend.service.simulate',side_effect=AssertionError('No simulation')):
            validation=self.client.get('/api/validation').json()
            sensitivity=self.client.get('/api/sensitivity').json()
            comparison=self.client.get('/api/comparison').json()
        self.assertEqual(sum(r['n_valid_distances'] for r in validation['dietz']),216)
        self.assertEqual(sensitivity['metadata']['engine_version'],'project2-synthetic-1.1.1')
        self.assertEqual(comparison['audit'][0]['engine_version'],'project2-synthetic-1.1.0')
        self.assertFalse(validation['nina']['ecological_ranking_allowed'])
        self.assertEqual(len(validation['correspondence']),9)
        self.assertTrue(all(r['reference']=='No comparable' for r in validation['correspondence'] if 'resource' in r['metric']))

    def test_selected_summary_matches_counts_and_means(self):
        rows=self.client.get('/api/validation').json()['dietz']
        by_colony={r['colony']:r for r in rows}
        for colony,n,mean in [('Bygdoy',87,783.4965517241377),('Ulleval 1',97,629.4711340206186),('Ulleval 2',32,372.2875)]:
            self.assertEqual(by_colony[colony]['n_valid_distances'],n)
            self.assertAlmostEqual(by_colony[colony]['mean_point_distance_m'],mean,places=7)
        sources=self.client.get('/api/validation').json()['sources']
        self.assertEqual(sources['distinct_dates'],10)
        self.assertFalse(sources['independent_bees_known'])

    def test_per_hive_aggregation_matches_existing_replicates(self):
        actual=self.client.get('/api/sensitivity').json()['per_hive_summary']
        raw=pd.read_csv(ROOT/'results/project2/sensitivity_v111/replicates.csv')
        for r in actual:
            group=raw[(raw.experiment_condition==r['condition'])&(raw.method==r['method'])]
            self.assertEqual(r['n'],30)
            self.assertAlmostEqual(r['mean_resource_per_hive'],group.mean_resource_per_hive.mean(),places=8)
            self.assertFalse(r['condition'] in ['K3','K8'] and r['method']=='NSGA2')

    def test_downloads_equal_selected_files(self):
        for name,file in [('dietz','dietz_window_summary.csv'),('correspondence','metric_correspondence.csv')]:
            self.assertEqual(self.client.get('/api/download/'+name).content,(ROOT/'results/project2/selected_validation'/file).read_bytes())
        self.assertEqual(self.client.get('/api/download/nina-raster').status_code,404)


if __name__=='__main__':unittest.main()
