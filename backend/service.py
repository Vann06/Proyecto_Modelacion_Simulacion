"""Read-only archives and a bounded adapter to the existing Python simulator."""
from pathlib import Path
from functools import lru_cache
import json,sys
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bee_sim.project2 import load_config,with_parameters,simulate
from bee_sim.project2.strategies.random_baseline import select_sites as random_select
from bee_sim.project2.strategies.greedy_baseline import select_sites as greedy_select
from bee_sim.analysis.project2_comparison import build_comparison

GEO=Transformer.from_crs(25833,4326,always_xy=True)


def records(df):
    return json.loads(df.to_json(orient='records',date_format='iso'))


def file_records(path):
    return records(pd.read_csv(ROOT/path))


@lru_cache(maxsize=1)
def comparison():
    d=build_comparison(ROOT)
    return {k:(records(v) if isinstance(v,pd.DataFrame) else v) for k,v in d.items() if k not in ['frames','per_seed']}


@lru_cache(maxsize=1)
def landscape():
    folder=ROOT/'data/project2/processed'
    parks=gpd.read_file(folder/'oslo_parks.geojson').to_crs(25833)
    parks=parks[['patch_id','geometry']]
    parks.geometry=parks.geometry.simplify(6,preserve_topology=True)
    table=pd.read_csv(folder/'spatial_patches.csv')
    parks=parks.merge(table[['patch_id','Navn','area_m2','intersects_restricted_zone','is_initial_candidate']],on='patch_id')
    zones=gpd.read_file(folder/'bee_free_zones.geojson').to_crs(25833)[['geometry']]
    zones.geometry=zones.geometry.simplify(6,preserve_topology=True)
    candidates=pd.read_csv(folder/'candidate_hive_sites.csv')
    candidates['longitude'],candidates['latitude']=GEO.transform(candidates.x_m,candidates.y_m)
    candidates=candidates.merge(table[['patch_id','Navn']],on='patch_id')
    resources=pd.read_csv(folder/'resource_patches.csv')
    resources['longitude'],resources['latitude']=GEO.transform(resources.resource_x_m,resources.resource_y_m)
    exclusive=gpd.read_file(folder/'resource_patches.geojson').to_crs(25833)[['patch_id','geometry']]
    exclusive.geometry=exclusive.geometry.simplify(6,preserve_topology=True)
    return {'parks':json.loads(parks.to_crs(4326).to_json()),'zones':json.loads(zones.to_crs(4326).to_json()),
        'resource_geometry':json.loads(exclusive.to_crs(4326).to_json()),
        'candidates':records(candidates),'resources':records(resources)}


def payload(result,sites,method,kind,config):
    # Daily patch stocks + actual trip intervals; browser only interpolates drawing.
    resource=result['resource_log'].copy()
    daily=[]
    for date,group in resource.groupby('date',sort=True):
        daily.append({'date':date,'patch_ids':group.patch_id.tolist(),'initial':group.R_before.tolist(),
                      'final':group.R_after.tolist(),'consumption':float(group.consumption.sum()),
                      'regeneration':float(group.regeneration.sum()),'stock':float(group.R_after.sum())})
    return {'kind':kind,'method':method,'sites':sites,'metrics':result['metrics'],'per_hive':records(result['per_hive']),
        'trips':records(result['trips']),'days':daily,'events':records(result['events']),
        'provenance':result['provenance'],'parameters':dict(config.parameters),
        'interpretation':'synthetic_RU; locations from chosen method; linear travel interpolation is visual only'}


def run(request):
    base=load_config(ROOT/'config/project2/base.yaml')
    cfg=with_parameters(base,K=request.K,initial_resource_total=base['initial_resource_total']*request.resource_factor,
        alpha=request.alpha,beta=request.beta,max_foraging_distance_m=request.radius_m,
        regeneration_rate=request.regeneration,departures_per_day=request.departures,
        demand_mean_ru=request.demand_mean,flight_speed_m_s=request.speed_m_s)
    candidates=pd.read_csv(ROOT/'data/project2/processed/candidate_hive_sites.csv')
    if request.method=='RANDOM':sites=list(random_select(candidates,request.K,request.optimizer_seed))
    elif request.method=='GREEDY':sites=greedy_select(cfg)['site_ids']
    elif request.method=='NSGA2':
        if request.K!=5:raise ValueError('El frente guardado solo contiene K=5; no truncar ni completar soluciones.')
        front=json.loads((ROOT/'results/project2/nsga2/front.json').read_text())
        solution=next((s for s in front['solutions'] if s['solution_id']==request.solution_id),None)
        if solution is None:raise ValueError('Solución del frente no encontrada')
        sites=solution['site_ids']
    else:sites=request.site_ids
    bank=pd.read_csv(ROOT/base['seed_bank_file'])
    seed=int(bank.loc[bank.replication_id.eq(request.replication_id),'seed'].iloc[0])
    return payload(simulate(sites,seed,cfg),sites,request.method,'new_exploratory_run',cfg)
