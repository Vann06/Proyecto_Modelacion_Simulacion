"""Dietz 2018 feasibility audit. Does not import or alter the simulator.

Kept outside project2/: the core engine hashes every .py in that directory.
An audit module must not change the identity of historical experiments.
"""
from pathlib import Path
import hashlib
import re
import numpy as np
import pandas as pd
from pypdf import PdfReader

SOURCE_URL = 'https://bybi.no/wp-content/uploads/2018/12/Sabrinas-Master-thesis-181210.pdf'
SOURCE_SHA256 = 'f540f7ade82453d54de2a2e94942cca2f64e316941f4f6ba02a01420b662975f'
COLONIES = {'Bygdoy':211,'Ulleval 1':190,'Ulleval 2':105}
PAGE_COUNTS = dict(zip(range(50,60),[50,50,50,61,50,50,50,40,50,55]))
NUMERIC = ['day','month','year','average_length_s','hour','minute','second',
           'average_angle_deg','azimuth_deg','heading_deg','distance_m','heading_rad',
           'easting_source','northing_source','duration_s']
INTEGERS = ['source_page','source_row','day','month','year','hour','minute','second']
ROW = re.compile(r'^\s*(\d+)\s+(\d+)\s+(\S+)\s+(Bygdoy|Ulleval [12])\s+(.+?)\s*$')


class HistoricalFeasibilityError(ValueError):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _row(page, index, movie, dance, colony, values):
    values = values.split()
    if len(values) != len(NUMERIC):
        raise ValueError(f'Página {page}, fila {index}: {len(values)} campos numéricos; revisar PDF')
    return {'source_page':page,'source_row':int(index),'movie_id':movie,'dance_id_source':dance,
            'colony':re.sub(r'\s+',' ',colony),**dict(zip(NUMERIC,map(float,values)))}


def extract_tables(pdf):
    """Independent PDF engines must agree on every cell, not just on row count."""
    import pymupdf
    if sha256(pdf) != SOURCE_SHA256:
        raise ValueError('La huella de la tesis cambió; auditar otra versión antes de extraer.')
    reader=PdfReader(pdf)
    if len(reader.pages)!=62:raise ValueError('Documento distinto de la versión auditada de 62 páginas')
    first=[]
    for page,expected in PAGE_COUNTS.items():
        found=[]
        for line in reader.pages[page-1].extract_text().splitlines():
            m=ROW.fullmatch(line)
            if m:found.append(_row(page,*m.groups()))
        if len(found)!=expected:raise ValueError(f'Tabla incompleta en página {page}: {len(found)} != {expected}')
        first.extend(found)
    # PyMuPDF emits a cell per line rather than pypdf's row per line.
    number=r'[-+]?\d+(?:\.\d+)?'
    pattern=re.compile(r'(?<!\S)(\d+)\s+(\d+)\s+(\d+_\d+)\s+(Bygdoy|Ulleval\s+[12])\s+('
                       +r'\s+'.join([number]*15)+r')(?=\s|$)')
    second=[]
    with pymupdf.open(pdf) as doc:
        for page,expected in PAGE_COUNTS.items():
            found=[_row(page,*m.groups()) for m in pattern.finditer(doc[page-1].get_text('text'))]
            if len(found)!=expected:raise ValueError(f'Extracción alternativa incompleta, página {page}')
            second.extend(found)
    a,b=pd.DataFrame(first),pd.DataFrame(second)
    pd.testing.assert_frame_equal(a,b,check_exact=True)
    for name in INTEGERS:a[name]=a[name].astype(int)
    validate_observations(a)
    return a


def validate_observations(frame):
    if frame.groupby('colony').size().to_dict()!=COLONIES:raise ValueError('Conteos por colonia no coinciden')
    if frame.duplicated(['colony','source_row']).any():raise ValueError('Filas de origen duplicadas')
    for colony,n in COLONIES.items():
        if set(frame.loc[frame.colony.eq(colony),'source_row'])!=set(range(1,n+1)):
            raise ValueError('Faltan índices del anexo')
    if not np.isfinite(frame[NUMERIC].to_numpy(float)).all():raise ValueError('Datos no finitos')
    if not frame.year.eq(2017).all():raise ValueError('Año no esperado; no corregir silenciosamente')
    if pd.to_datetime(frame[['year','month','day']],errors='coerce').isna().any():raise ValueError('Fecha inválida')


def annotate_observations(frame):
    df=frame.copy()
    df['record_id']='dietz2018:'+df.colony.str.replace(' ','',regex=False)+':'+df.source_row.astype(str).str.zfill(3)
    df['record_id_status']='derived_from_colony_and_appendix_row_not_bee_identity'
    df['date']=pd.to_datetime(df[['year','month','day']]).dt.strftime('%Y-%m-%d')
    df['inside_project_window']=df.date.between('2017-07-18','2017-08-04')
    df['distance_valid']=df.distance_m.ge(0)
    df['clock_valid']=df.hour.between(0,23)&df.minute.between(0,59)&df.second.between(0,59)
    df['id_prefix_consistent']=df.dance_id_source.str.split('_').str[0].eq(df.movie_id)
    df['dance_id_duplicated']=df.duplicated(['colony','dance_id_source'],keep=False)
    df['distance_analysis_eligible']=df.inside_project_window&df.distance_valid
    df['timed_analysis_eligible']=df.distance_analysis_eligible&df.clock_valid
    df['source_crs']='UNCONFIRMED'
    df['spatially_verified']=False
    df['distance_exclusion_reason']=np.select([~df.inside_project_window,~df.distance_valid],
                                             ['outside_18_day_window','negative_source_distance'],default='included_for_descriptive_distance_only')
    # Inversion is a consistency diagnostic, NOT a surveyed hive coordinate.
    df['origin_x_implied']=df.easting_source-df.distance_m*np.sin(df.heading_rad)
    df['origin_y_implied']=df.northing_source-df.distance_m*np.cos(df.heading_rad)
    centers=df.groupby('colony')[['origin_x_implied','origin_y_implied']].transform('median')
    df['origin_residual_source_units']=np.hypot(df.origin_x_implied-centers.origin_x_implied,
                                               df.origin_y_implied-centers.origin_y_implied)
    df['origin_consistent_within_0_1_source_unit']=df.origin_residual_source_units.le(.1)
    return df


def implied_hives(frame):
    rows=[]
    for colony,g in frame.groupby('colony',sort=False):
        rows.append({'colony':colony,'origin_x_implied_median':g.origin_x_implied.median(),
          'origin_y_implied_median':g.origin_y_implied.median(),'source_crs':'UNCONFIRMED',
          'coordinate_status':'algebraic_inference_not_verified_historical_location',
          'surveyed_location_available':False,'n_vectors':len(g),
          'n_origin_consistent_0_1':int(g.origin_consistent_within_0_1_source_unit.sum()),
          'max_origin_residual_source_units':g.origin_residual_source_units.max(),
          'source_pages':'14-19,50-59','placement_allowed_for_historical_simulation':False})
    return pd.DataFrame(rows)


def clustered_interval(frame,column,seed=20261108,n_boot=2000):
    """Bootstrap filming dates, never posterior samples as independent dances."""
    rng=np.random.default_rng(seed)
    blocks=[g[column].to_numpy(float) for _,g in frame.groupby('date')]
    if not blocks:return (None,None)
    means=[]
    for _ in range(n_boot):
        sample=np.concatenate([blocks[i] for i in rng.integers(0,len(blocks),len(blocks))])
        means.append(sample.mean())
    return tuple(float(v) for v in np.quantile(means,[.025,.975]))


def distance_inventory(frame,n_boot=2000):
    rows=[]
    for colony,g in frame.groupby('colony',sort=False):
        for scope in ['full_source_period','project_18_day_window']:
            subset=g if scope=='full_source_period' else g.loc[g.inside_project_window]
            valid=subset.loc[subset.distance_valid].copy()
            valid['beyond_3km']=valid.distance_m.gt(3000).astype(float)
            lo,hi=clustered_interval(valid,'distance_m',n_boot=n_boot)
            rows.append({'colony':colony,'scope':scope,'n_source_rows':len(subset),'n_valid_distances':len(valid),
              'n_film_dates':valid.date.nunique(),'n_invalid_clocks':int((~subset.clock_valid).sum()),
              'start_date':valid.date.min(),'end_date':valid.date.max(),'mean_point_distance_m':valid.distance_m.mean(),
              'median_point_distance_m':valid.distance_m.median(),'p05_point_distance_m':valid.distance_m.quantile(.05),
              'p95_point_distance_m':valid.distance_m.quantile(.95),'p99_point_distance_m':valid.distance_m.quantile(.99),
              'max_point_distance_m':valid.distance_m.max(),'n_above_3km':int(valid.beyond_3km.sum()),
              'percent_above_3km':100*valid.beyond_3km.mean(),'mean_cluster_bootstrap_ci95_low_m':lo,
              'mean_cluster_bootstrap_ci95_high_m':hi,'bootstrap_unit':'filming_date','bootstrap_seed':20261108,
              'status':'appendix_point_estimates_not_GPS_not_posterior_distribution'})
    return pd.DataFrame(rows)


def conditional_geography(frame,hives,parks_path):
    """CRS hypothesis diagnostics only. No output is a verified historical location.

    Centre inclusion (boundary counts as covered) and 25 m boundary sensitivity;
    latter is an analyst's tolerance, never a confidence radius for waggle dances.
    """
    import geopandas as gpd
    from pyproj import Transformer
    from shapely.geometry import Point
    from shapely.ops import unary_union
    parks=gpd.read_file(parks_path).to_crs(25833)
    union=unary_union(parks.geometry)
    details=[];summary=[];hive_hypotheses=[]
    selected=frame.loc[frame.distance_analysis_eligible]
    for epsg in [25832,32632]:
        transform=Transformer.from_crs(epsg,25833,always_xy=True)
        to_geo=Transformer.from_crs(epsg,4326,always_xy=True)
        x,y=transform.transform(selected.easting_source.to_numpy(),selected.northing_source.to_numpy())
        points=gpd.GeoSeries(gpd.points_from_xy(x,y),crs=25833)
        covered=points.covered_by(union).to_numpy()
        d=points.distance(union).to_numpy()
        for position,row in enumerate(selected.itertuples()):
            details.append({'record_id':row.record_id,'colony':row.colony,'date':row.date,'assumed_epsg':epsg,
               'project_x_m_conditional':x[position],'project_y_m_conditional':y[position],
               'covered_by_park_conditional':bool(covered[position]),'distance_to_park_m_conditional':float(d[position]),
               'interpretation':'conditional_on_unverified_crs_not_a_geographic_validation'})
        for colony in COLONIES:
            mask=selected.colony.eq(colony).to_numpy();n=int(mask.sum())
            summary.append({'colony':colony,'assumed_epsg':epsg,'n':n,'covered_centers':int(covered[mask].sum()),
              'percent_covered_conditional':100*covered[mask].mean(),'percent_outside_conditional':100*(~covered[mask]).mean(),
              'percent_within_25m_of_park_conditional':100*(d[mask]<=25).mean(),
              'median_distance_to_park_m_conditional':float(np.median(d[mask])),
              'status':'CRS_hypothesis_only; decoded_points_not_posterior_footprints'})
        for row in hives.itertuples():
            a,b=transform.transform(row.origin_x_implied_median,row.origin_y_implied_median)
            lon,lat=to_geo.transform(row.origin_x_implied_median,row.origin_y_implied_median)
            hive_hypotheses.append({'colony':row.colony,'assumed_epsg':epsg,'x_m_conditional':a,'y_m_conditional':b,
                'longitude_conditional':lon,'latitude_conditional':lat,'coordinate_status':'inferred_unverified_not_for_simulation'})
    return pd.DataFrame(details),pd.DataFrame(summary),pd.DataFrame(hive_hypotheses)


def feasibility_report(hives):
    ulleval=hives.set_index('colony').loc[['Ulleval 1','Ulleval 2']]
    separation=float(np.hypot(*np.diff(ulleval[['origin_x_implied_median','origin_y_implied_median']].to_numpy(),axis=0)[0]))
    return {'ready_for_historical_simulation':False,'verified_historical_hive_positions':False,
      'source_crs_verified':False,'appendix_individual_rows_recovered':506,
      'project_window_rows':216,'implied_ulleval_separation_source_units':separation,
      'published_ulleval_separation_approx_m':.2,'posterior_probability_rasters_available':False,
      'decision':'STOP_AFTER_FEASIBILITY_AUDIT',
      'reasons':['No declared source CRS/datum or georeferencing in the supplied PDF',
       'Hive coordinates are algebraically inferred, not a published surveyed coordinate table',
       'Implied Ulleval origins differ by about 3 source units; text reports about 0.2 m',
       'No original posterior distance/direction draws or probability rasters for comparable Jaccard'],
      'simulation_runs_executed':0,'new_simulation_seed_bank_created':False,
      'optimization_validated_in_real_world':False}


def require_historical_feasibility(report):
    if not (report.get('ready_for_historical_simulation') and report.get('verified_historical_hive_positions')
            and report.get('source_crs_verified')):
        raise HistoricalFeasibilityError('Auditoría no habilita simulación histórica: faltan CRS y ubicaciones verificadas. No sustituirlos por hipótesis.')
