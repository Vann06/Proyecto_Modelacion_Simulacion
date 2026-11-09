"""Bounded, read-only source investigation; exports only to a new QC directory."""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone

import certifi
import numpy as np
import pandas as pd
import requests
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.features import geometry_window, geometry_mask
from rasterio.errors import WindowError
import geopandas as gpd
from shapely.geometry import box, mapping

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/project2/nina_quality_control'
CACHE = ROOT / '.build/historical/nina_qc'
BASE = 'https://s3-ext-1.nina.no/dms/maps/sources/192/pollinator_potentential_0301.tif'
CONFIG = 'https://s3-ext-1.nina.no/dms/maps/main/localEA/config.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(data):
    values = np.ma.asarray(data).compressed()
    values = values[np.isfinite(values)]
    return {'n_valid': int(values.size), 'min': float(values.min()) if values.size else None,
            'max': float(values.max()) if values.size else None,
            'mean': float(values.mean()) if values.size else None,
            'n_below_0': int((values < 0).sum()), 'n_above_1': int((values > 1).sum())}


def finalize():
    """Derive the report tables from exported observations without further network reads."""
    ranges=json.loads((OUT/'sample_range_summary.json').read_text())
    checks=pd.read_csv(OUT/'native_to_cog_checks.csv')
    summaries=[]
    for name,group in checks.groupby('resampling_test'):
        weights=group.n_pairs
        summaries.append({'resampling_test':name,'n_pairs':int(weights.sum()),
                          'mae_direct':float(np.average(group.mae_direct,weights=weights)),
                          'rmse_direct':float(np.sqrt(np.average(group.rmse_direct**2,weights=weights))),
                          'mae_one_minus_source':float(np.average(group.mae_one_minus_source,weights=weights))})
    pd.DataFrame(summaries).to_csv(OUT/'resampling_summary.csv',index=False)
    aggregation=pd.read_csv(OUT/'cog_to_overview_checks.csv')
    pd.DataFrame([{'aggregation_test':name,'n_pairs':int(g.n_pairs.sum()),
                   'mae':float(np.average(g.mae,weights=g.n_pairs)),
                   'rmse':float(np.sqrt(np.average(g.rmse**2,weights=g.n_pairs)))}
                  for name,g in aggregation.groupby('aggregation_test')]).to_csv(OUT/'aggregation_summary.csv',index=False)
    missing=pd.read_csv(OUT/'missing_51_parks.csv')
    missing.groupby(['old_status','cause']).size().rename('n_parks').reset_index().to_csv(OUT/'missing_parks_summary.csv',index=False)
    # Test lattice compatibility only. It CANNOT identify a historical transformation.
    native=np.concatenate([np.load(p)['data'].ravel() for p in sorted(CACHE.glob('*_original.npz'))])
    native=native[(native!=-9999)&np.isfinite(native)]
    scores=np.array([0.,.05,.1,.2,.25,.3,.35,.4,.45,.5,.55,.6,.7,.8,.9,1.])
    hypotheses=[]
    for label,values in [('raw_equal_ESTIMAP_table_scores',native),
                         ('hypothesis_reversed_minmax_0_05_1',1-.95*native)]:
        gap=np.min(abs(values[:,None]-scores),axis=1)
        hypotheses.append({'hypothesis':label,'n_native_sample_values':len(native),
                           'fraction_on_table_score_lattice_at_1e_6':float((gap<=1e-6).mean()),
                           'identifies_transform':False})
    pd.DataFrame(hypotheses).to_csv(OUT/'scale_hypotheses_not_proof.csv',index=False)
    conclusion={'decision':'NO APTO',
        'scope':'ranking installations as higher/lower ecological suitability; not a judgment that all raw data are unusable',
        'numeric_access':'APTO CON LIMITACIONES',
        'direction_confirmed':False,'exact_2017_to_2022_processing_lineage_confirmed':False,
        'original_sample_range':[ranges['original']['min'],ranges['original']['max']],
        'cog_sample_range':[ranges['cog']['min'],ranges['cog']['max']],
        'overview_sample_range':[ranges['overview']['min'],ranges['overview']['max']],
        'sample_design':'16 systematic windows plus 8 targeted overview extremes; not global exhaustive statistics',
        'recommendation':'close as complementary reference until publisher provides the numeric lineage/direction; no installation ranking',
        'simulations_run':0,'installations_classified':0,
        'checked_at_utc':datetime.now(timezone.utc).isoformat()}
    (OUT/'decision.json').write_text(json.dumps(conclusion,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(conclusion,ensure_ascii=False,indent=2))


def cached_read(ds, window, key):
    path = CACHE / (key + '.npz')
    window = window.round_offsets().round_lengths()
    if path.exists():
        archive = np.load(path)
        array = archive['data']
        if array.shape != (int(window.height), int(window.width)):
            raise ValueError('Cache window shape mismatch: ' + key)
    else:
        array = ds.read(1, window=window)
        np.savez_compressed(path, data=array)
    return np.ma.masked_equal(array, ds.nodata), ds.window_transform(window)


def sample_windows(coarse, cog):
    result = []
    # Predeclared systematic 4x4 grid, plus eight targeted extreme-value windows.
    for r in range(4):
        for c in range(4):
            result.append((f'grid_{r}_{c}', int((c+.5)*cog.width/4), int((r+.5)*cog.height/4), 'systematic_4x4'))
    a = coarse.read(1, masked=True)
    for label, order in [('low', np.argsort(a.filled(np.inf), axis=None)),
                         ('high', np.argsort(-a.filled(-np.inf), axis=None))]:
        selected = []
        for flat in order:
            r,c = np.unravel_index(flat, a.shape)
            if a.mask[r,c] or any(abs(r-x)+abs(c-y)<32 for x,y in selected):
                continue
            selected.append((r,c))
            result.append((f'{label}_{len(selected)}', c*8+4, r*8+4, 'targeted_overview_extreme'))
            if len(selected)==4:
                break
    return result


def compare_samples(original, cog, coarse):
    summaries, comparisons, manifest, overview_checks = [], [], [], []
    arrays_for_summary = {'original': [], 'cog': [], 'overview': []}
    for key, col, row, design in sample_windows(coarse, cog):
        # Align to the published factor-8 grid so no extra resampling is needed for overview extraction.
        col = min(max(0, (col//8-4)*8), cog.width-64)
        row = min(max(0, (row//8-4)*8), cog.height-64)
        cw = Window(col,row,64,64)
        target, ct = cached_read(cog,cw,key+'_cog')
        bounds = rasterio.windows.bounds(cw,cog.transform)
        native_bounds = transform_bounds(cog.crs,original.crs,*bounds,densify_pts=21)
        nw = rasterio.windows.from_bounds(*native_bounds, original.transform)
        c0 = max(0,int(np.floor(nw.col_off))-8);r0=max(0,int(np.floor(nw.row_off))-8)
        c1=min(original.width,int(np.ceil(nw.col_off+nw.width))+8)
        r1=min(original.height,int(np.ceil(nw.row_off+nw.height))+8)
        if c1<=c0 or r1<=r0:
            continue
        nw=Window(c0,r0,c1-c0,r1-r0)
        source, st = cached_read(original,nw,key+'_original')
        ow=Window(col//8,row//8,8,8)
        low=coarse.read(1,window=ow,masked=True)
        for label,data in [('original',source),('cog',target),('overview',low)]:
            summaries.append({'sample_id':key,'design':design,'dataset':label,**stats(data)})
            arrays_for_summary[label].append(data.compressed())
        manifest.append({'sample_id':key,'design':design,'cog_col':col,'cog_row':row,
                         'cog_width':64,'cog_height':64,'original_col':c0,'original_row':r0,
                         'original_width':c1-c0,'original_height':r1-r0})
        reconstructed={}
        for name in ['nearest','bilinear','cubic','cubic_spline','lanczos']:
            dest=np.full(target.shape,-9999.,dtype=np.float32)
            reproject(source.filled(-9999.), dest, src_transform=st,src_crs=original.crs,
                      src_nodata=-9999.,dst_transform=ct,dst_crs=cog.crs,dst_nodata=-9999.,
                      resampling=getattr(Resampling,name))
            reconstructed[name]=dest
        valid=~np.ma.getmaskarray(target)
        for dest in reconstructed.values():
            valid &= (dest!=-9999.)&np.isfinite(dest)
        for name,dest in reconstructed.items():
            if valid.any():
                x=dest[valid].astype(float);y=target.data[valid].astype(float)
                comparisons.append({'sample_id':key,'resampling_test':name,'n_pairs':len(x),
                    'mae_direct':float(np.mean(abs(y-x))), 'rmse_direct':float(np.sqrt(np.mean((y-x)**2))),
                    'mae_one_minus_source':float(np.mean(abs(y-(1-x)))),
                    'fraction_equal_at_1e_6':float(np.mean(abs(y-x)<=1e-6))})
        # Test aggregation hypotheses from full COG pixels, not from native UTM pixels.
        reconstructed={}
        for name in ['nearest','average','bilinear','cubic','lanczos']:
            dest=np.full((8,8),-9999.,dtype=np.float32)
            reproject(target.filled(-9999.),dest,src_transform=ct,src_crs=cog.crs,src_nodata=-9999.,
                      dst_transform=coarse.window_transform(ow),dst_crs=coarse.crs,dst_nodata=-9999.,
                      resampling=getattr(Resampling,name))
            reconstructed[name]=dest
        valid=~np.ma.getmaskarray(low)
        # Exclude boundary cells whose interpolation support leaves this local window.
        interior=np.zeros((8,8),dtype=bool);interior[2:-2,2:-2]=True
        valid &= interior
        for dest in reconstructed.values():
            valid &= (dest!=-9999.)&np.isfinite(dest)
        for name,dest in reconstructed.items():
            if valid.any():
                delta=dest[valid].astype(float)-low.data[valid]
                overview_checks.append({'sample_id':key,'aggregation_test':name,'n_pairs':int(valid.sum()),
                                        'mae':float(abs(delta).mean()),'rmse':float(np.sqrt((delta**2).mean()))})
        print('sample',key,flush=True)
    for name,rows in [('sample_manifest',manifest),('sample_ranges',summaries),
                      ('native_to_cog_checks',comparisons),('cog_to_overview_checks',overview_checks)]:
        pd.DataFrame(rows).to_csv(OUT/(name+'.csv'),index=False)
    aggregate={label:stats(np.ma.masked_invalid(np.concatenate(values))) for label,values in arrays_for_summary.items()}
    (OUT/'sample_range_summary.json').write_text(json.dumps(aggregate,indent=2),encoding='utf-8')


def missing_parks(original, coarse):
    old=pd.read_csv(ROOT/'results/project2/historical_validation/nina_park_index_approximate.csv')
    missing=old[old.n_valid_overview_cells.eq(0)]
    parks=gpd.read_file(ROOT/'data/project2/processed/oslo_parks.geojson').to_crs(original.crs)
    parks=parks[parks.patch_id.isin(missing.patch_id)].sort_values('patch_id')
    rows=[]
    for park in parks.itertuples():
        geom=park.geometry; inside_fraction=geom.intersection(box(*original.bounds)).area/geom.area
        prev=missing.set_index('patch_id').loc[park.patch_id]
        try:
            nw=geometry_window(original,[mapping(geom)])
            data,transform=cached_read(original,nw,'missing_'+park.patch_id)
            center=geometry_mask([mapping(geom)],data.shape,transform,invert=True,all_touched=False)
            touched=geometry_mask([mapping(geom)],data.shape,transform,invert=True,all_touched=True)
            center_stats=stats(data[center]);touch_stats=stats(data[touched])
            cause=('valid_native_pixels_lost_at_coarse_grid' if center_stats['n_valid'] else
                   'native_valid_touched_only_no_centers' if touch_stats['n_valid'] else
                   'inside_extent_but_native_nodata_or_no_pixel_intersection')
            ncenter=int(center.sum())
        except WindowError:
            center_stats=stats(np.array([]));touch_stats=stats(np.array([]));ncenter=0
            cause='outside_native_raster_extent'
        rows.append({'patch_id':park.patch_id,'old_status':prev.status,
                     'old_centers':int(prev.n_pixel_centers_in_polygon),'area_m2':geom.area,
                     'fraction_area_in_native_extent':inside_fraction,'native_centers':ncenter,
                     'native_valid_centers':center_stats['n_valid'],'native_valid_touched':touch_stats['n_valid'],
                     'native_min':center_stats['min'],'native_max':center_stats['max'],
                     'native_mean':center_stats['mean'],'cause':cause})
        print('missing park',len(rows),cause,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'missing_51_parks.csv',index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--summarize-cached', action='store_true',
                        help='Rebuild summary tables from cached samples and CSVs, without network access')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    if args.summarize_cached:
        finalize()
        return
    response = requests.get(CONFIG, timeout=45)
    response.raise_for_status()
    (CACHE / 'catalog.json').write_bytes(response.content)
    config = response.json()
    item = config['items']['15216100_pollinator_potentential_0301']
    (OUT / 'catalog_item.json').write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')
    # Preserve source response identity. Original HTML remains in ignored cache.
    source_checks=[]
    for name,url in [('catalog',CONFIG),
                     ('portal','https://ninanor.github.io/SPARE_project/layers.html'),
                     ('article','https://oneecosystem.pensoft.net/article/14014/'),
                     ('article_methods','https://oneecosystem.pensoft.net/article/14014/instance/3642699/'),
                     ('article_pdf','https://oneecosystem.pensoft.net/article/14014/download/pdf'),
                     ('jrc','https://publications.jrc.ec.europa.eu/repository/handle/JRC107786')]:
        try:
            r=response if name=='catalog' else requests.get(url,timeout=45)
            suffix='.pdf' if name=='article_pdf' and r.content.startswith(b'%PDF') else '.txt'
            (CACHE/(name+'_response'+suffix)).write_bytes(r.content)
            source_checks.append({'source':name,'url':url,'http_status':r.status_code,
                                  'sha256':hashlib.sha256(r.content).hexdigest()})
        except requests.RequestException as error:
            source_checks.append({'source':name,'url':url,'http_status':None,'error':type(error).__name__})
    (OUT/'source_access.json').write_text(json.dumps(source_checks,indent=2),encoding='utf-8')
    identity={}
    for label,url in [('original',BASE),('cog',BASE+'.cog')]:
        head=requests.head(url,timeout=45);head.raise_for_status()
        identity[label]={'url':url,'etag':head.headers.get('ETag'),
                         'content_length':head.headers.get('Content-Length'),
                         'last_modified':head.headers.get('Last-Modified')}
    identity_path=CACHE/'source_identity.json'
    if identity_path.exists() and json.loads(identity_path.read_text())!=identity:
        raise ValueError('Source changed; do not reuse cached samples under a different identity')
    identity_path.write_text(json.dumps(identity,indent=2),encoding='utf-8')
    (OUT/'source_identity.json').write_text(json.dumps(identity,indent=2),encoding='utf-8')
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif,.cog', GDAL_HTTP_TIMEOUT='45',
                      GDAL_HTTP_CA_BUNDLE=certifi.where()):
        for label, url in [('original', BASE), ('cog', BASE + '.cog')]:
            with rasterio.open(url) as ds:
                meta = {'profile': {k: str(v) for k,v in ds.profile.items()},
                        'block_shapes': ds.block_shapes, 'overviews': ds.overviews(1),
                        'tags': ds.tags(), 'band_tags': ds.tags(1),
                        'bounds': list(ds.bounds), 'transform': list(ds.transform)}
                print(label, json.dumps(meta), flush=True)
                (OUT / f'{label}_metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        if not args.probe:
            local=ROOT/'.build/historical/nina/nina_published_overview_factor8.tif'
            previous=json.loads((ROOT/'.build/historical/nina/overview_identity.json').read_text())
            if any(previous[k]['etag']!=identity[k]['etag'] for k in identity):
                raise ValueError('Old overview no longer matches source ETag')
            with rasterio.open(BASE) as original, rasterio.open(BASE+'.cog') as cog, rasterio.open(local) as coarse:
                compare_samples(original,cog,coarse)
                missing_parks(original,coarse)
            paths=sorted(CACHE.glob('*.npz'))
            pd.DataFrame([{'file':str(p.relative_to(ROOT)),'sha256':digest(p),
                           'bytes':p.stat().st_size} for p in paths]).to_csv(OUT/'sample_cache_manifest.csv',index=False)
            finalize()


if __name__ == '__main__':
    try:
        main()
    except (requests.RequestException, rasterio.errors.RasterioIOError) as error:
        raise SystemExit('NINA QC stopped: source unavailable; no replacement or imputation was used. '
                         + str(error)) from error
