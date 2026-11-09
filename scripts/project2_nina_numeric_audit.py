"""Inspect official NINA numeric data without downloading the full 1.6 GB TIFF.

Uses the publisher-provided factor-8 COG overview for APPROXIMATE park summaries.
Does not convert the raw index to nectar/RU or modify any model input.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import pandas as pd
import requests,certifi
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask,geometry_window
from rasterio.errors import WindowError
import geopandas as gpd
from shapely.geometry import mapping
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
CONFIG='https://s3-ext-1.nina.no/dms/maps/main/localEA/config.json'
ITEM='15216100_pollinator_potentential_0301'


def raster_metadata(dataset):
    return {'crs':str(dataset.crs),'shape':list(dataset.shape),'resolution_projected_units':list(dataset.res),
      'bounds':list(dataset.bounds),'transform':list(dataset.transform),'nodata':dataset.nodata,
      'dtypes':list(dataset.dtypes),'count':dataset.count,'overviews':dataset.overviews(1),
      'tags':dataset.tags(),'band_tags':dataset.tags(1)}


def main():
    out=ROOT/'results/project2/historical_validation';out.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'.build/historical/nina';cache.mkdir(parents=True,exist_ok=True)
    response=requests.get(CONFIG,timeout=35);response.raise_for_status();config=response.json()
    item=config['items'][ITEM];download=item['download_url'];cog=item['layer']['titiler']['url']
    identity={}
    for label,url in [('original',download),('cog',cog)]:
        head=requests.head(url,timeout=35);head.raise_for_status()
        identity[label]={'url':url,'content_length':int(head.headers['Content-Length']),
                         'etag':head.headers.get('ETag'),'last_modified':head.headers.get('Last-Modified')}
    local=cache/'nina_published_overview_factor8.tif';local_meta=cache/'overview_identity.json'
    factor=8
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif,.cog',
                      GDAL_HTTP_TIMEOUT='45',GDAL_HTTP_CA_BUNDLE=certifi.where()):
        with rasterio.open(download) as source:original_metadata=raster_metadata(source)
        with rasterio.open(cog) as ds:
            cog_metadata=raster_metadata(ds)
            if factor not in ds.overviews(1):raise ValueError('No está el nivel reducido auditado; no inventar un reemplazo')
            profile=ds.profile.copy()
            width,height=ds.width//factor,ds.height//factor
            # Reuse cached numeric overview only if the publisher identity matches.
            reuse=local.exists() and local_meta.exists() and json.loads(local_meta.read_text())==identity
            if not reuse:
                data=ds.read(1,out_shape=(height,width),resampling=Resampling.nearest)
                transform=ds.transform*rasterio.Affine.scale(ds.width/width,ds.height/height)
                profile.update(driver='GTiff',width=width,height=height,transform=transform,compress='deflate')
                with rasterio.open(local,'w',**profile) as target:target.write(data,1)
                local_meta.write_text(json.dumps(identity,sort_keys=True),encoding='utf-8')
    parks=gpd.read_file(ROOT/'data/project2/processed/oslo_parks.geojson')
    stats=[]
    with rasterio.open(local) as ds:
        analysis_metadata=raster_metadata(ds);park_geo=parks.to_crs(ds.crs)
        for row in park_geo.itertuples():
            geometry=mapping(row.geometry)
            try:
                window=geometry_window(ds,[geometry])
                values=ds.read(1,window=window,masked=True)
                inside=geometry_mask([geometry],values.shape,ds.window_transform(window),invert=True,all_touched=False)
                valid=values[inside].compressed();valid=valid[np.isfinite(valid)]
                n_inside=int(inside.sum())
                status='approximate_numeric_summary' if len(valid) else 'no_valid_overview_pixel_centers'
            except WindowError:
                valid=np.array([]);n_inside=0;status='outside_published_raster_extent'
            stats.append({'patch_id':row.patch_id,'n_valid_overview_cells':len(valid),'n_pixel_centers_in_polygon':n_inside,
              'raw_index_mean_approx':float(valid.mean()) if len(valid) else None,
              'raw_index_median_approx':float(np.median(valid)) if len(valid) else None,
              'raw_index_min_approx':float(valid.min()) if len(valid) else None,
              'raw_index_max_approx':float(valid.max()) if len(valid) else None,'overview_factor':factor,
              'status':status,'semantic_direction':'UNCONFIRMED_metadata_description_and_legend_require_review'})
    frame=pd.DataFrame(stats)
    resources=pd.read_csv(ROOT/'data/project2/processed/resource_patches.csv')
    frame=frame.merge(resources[['patch_id','exclusive_area_m2']],on='patch_id',validate='one_to_one')
    frame['synthetic_initial_resource_share']=frame.exclusive_area_m2/frame.exclusive_area_m2.sum()
    frame['has_values_outside_legend_0_1']=frame.raw_index_min_approx.lt(0)|frame.raw_index_max_approx.gt(1)
    frame.to_csv(out/'nina_park_index_approximate.csv',index=False,lineterminator='\n')
    usable=frame.dropna(subset=['raw_index_mean_approx'])
    correlation=usable[['raw_index_mean_approx','synthetic_initial_resource_share']].corr(method='spearman').iloc[0,1]
    pd.DataFrame([{'comparison':'raw_NINA_index_vs_synthetic_area_share','n_parks':len(usable),
      'spearman_rho_descriptive':correlation,'p_value':None,'status':'overlapping_parks_not_independent; raw_index_direction_unconfirmed; no_RU_calibration'}]).to_csv(out/'nina_resource_relation.csv',index=False,lineterminator='\n')
    meta={'catalog_url':CONFIG,'catalog_sha256':hashlib.sha256(response.content).hexdigest(),'catalog_item':ITEM,
      'name':item['name'],'attribution':'NINA, pollinator_potentential_0301, CC-BY 4.0, official localEA catalog',
      'license':'CC-BY 4.0 according to official catalog','catalog_acquisition_period':2022,
      'catalog_spatial_resolution_field':1,'unit':'raw modeled index, not flowers/nectar/RU',
      'source_identity':identity,'original_raster':original_metadata,'cog_raster':cog_metadata,
      'analysis_overview':analysis_metadata,'analysis_overview_factor':factor,
      'derived_overview_sha256':hashlib.sha256(local.read_bytes()).hexdigest(),
      'full_tiff_downloaded':False,'large_raster_committed':False,
      'source_overview_resampling_lineage':'not specified by provider; do not interpret as exact full-resolution zonal averages',
      'zonal_rule':'existing overview pixels whose centers fall in original park polygon; no imputation if no centers',
      'n_original_parks':len(frame),'n_parks_with_numeric_overview_values':len(usable),
      'spearman_rho_raw_index_vs_area_share':float(correlation),
      'n_parks_with_values_outside_legend_0_1':int(frame.has_values_outside_legend_0_1.sum()),
      'range_in_park_overview_samples':[float(frame.raw_index_min_approx.min()),float(frame.raw_index_max_approx.max())],
      'out_of_range_values_clipped':False,
      'semantic_limitation':'description associates high values with low pollinator potential/tree-planting demand; title/legend suggest suitability; retain raw direction until confirmed',
      'temporal_limitation':'2022 catalog context is not a historical 2017 resource measurement',
      'historical_destinations_joined':False,'reason_no_historical_join':'Dietz source CRS/hive coordinates unverified',
      'network_method':'HTTP range reads through GDAL COG overview, no bulk tile scraping'}
    (out/'nina_numeric_audit.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    # Save the one relevant catalog item for transparent attribution and semantics.
    (out/'nina_catalog_item.json').write_text(json.dumps({'catalog_url':CONFIG,'item_id':ITEM,
        'name':item['name'],'description':item['description'],'download_url':download,'cog_url':cog,
        'legend':item['layer']['legend']},ensure_ascii=False,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(8,5))
    ax.scatter(usable.synthetic_initial_resource_share,usable.raw_index_mean_approx,s=12,color='#287c68',alpha=.5)
    ax.set(xlabel='Fracción del área exclusiva (recurso sintético inicial)',ylabel='Índice NINA bruto: media aproximada',
        title='Comparación descriptiva de parques, no calibración\nDirección del índice pendiente de confirmar')
    fig.tight_layout();fig.savefig(out/'nina_resource_relation.png',dpi=150);plt.close(fig)
    print(json.dumps({k:meta[k] for k in ['n_original_parks','n_parks_with_numeric_overview_values',
       'spearman_rho_raw_index_vs_area_share','analysis_overview_factor','full_tiff_downloaded']},indent=2))

if __name__=='__main__':main()
