"""FastAPI service, local by default. No NSGA search endpoint."""
from pathlib import Path
from typing import Literal
from functools import lru_cache
import json,threading
from fastapi import FastAPI,HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field,ConfigDict
from . import service

app=FastAPI(title='Oslo Pollinator Lab',version='0.1.0',description='Archived evidence and bounded common-engine experiments; no ecological calibration.')
app.add_middleware(GZipMiddleware,minimum_size=1000)
RUN_LOCK=threading.Lock()


class RunRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    method:Literal['RANDOM','GREEDY','NSGA2','MANUAL']='GREEDY'
    K:int=Field(default=5,ge=1,le=20,strict=True)
    resource_factor:float=Field(default=1,ge=0,le=3)
    alpha:float=Field(default=1,ge=0,le=5)
    beta:float=Field(default=2,ge=0,le=5)
    radius_m:float=Field(default=3000,ge=250,le=6000)
    regeneration:float=Field(default=.1,ge=0,le=.5)
    departures:float=Field(default=12,ge=0,le=60)
    demand_mean:float=Field(default=1,ge=.1,le=3)
    speed_m_s:float=Field(default=5.5,ge=2,le=10)
    optimizer_seed:int=Field(default=2026,ge=0,le=2**32-1,strict=True)
    replication_id:int=Field(default=31,ge=1,le=100,strict=True)
    solution_id:str=Field(default='pareto_047',pattern=r'^pareto_\d{3}$')
    site_ids:list[str]=Field(default_factory=list,max_length=20)


@app.get('/api/health')
def health():return {'status':'ok','mode':'synthetic','engine_version':'project2-synthetic-1.1.1'}


@app.get('/api/overview')
def overview():
    return {'parks':737,'candidate_ids':375,'unique_coordinates':351,'resource_geometries':680,
      'start':'2017-07-18','end':'2017-08-04','days':18,
      'weather':service.file_records('data/project2/processed/simulation_calendar.csv'),
      'source':'Dryad 10.5061/dryad.9kd51c5qk + GIS SPARE/Oslo','calibrated':False}


@app.get('/api/comparison')
def comparison():
    return {**service.comparison(),'history':service.file_records('results/project2/nsga2/history.csv'),
      'front':json.loads((service.ROOT/'results/project2/nsga2/front.json').read_text()),
      'changes':service.file_records('results/project2/scientific_validation/archived_changes.csv')}


@app.get('/api/validation')
def validation():
    folder=service.ROOT/'results/project2/scientific_validation'
    return {'metadata':json.loads((folder/'metadata.json').read_text(encoding='utf-8')),
      'errors':service.file_records('results/project2/scientific_validation/empirical_errors.csv'),
      'flowers':service.file_records('results/project2/scientific_validation/flowers_evaluation.csv'),
      'activity':service.file_records('results/project2/scientific_validation/activity_evaluation.csv')}


@app.get('/api/sensitivity')
def sensitivity():
    folder=service.ROOT/'results/project2/sensitivity_v111'
    if not (folder/'metadata.json').exists():raise HTTPException(503,'La evidencia de sensibilidad todavía no está disponible.')
    return {'metadata':json.loads((folder/'metadata.json').read_text(encoding='utf-8')),
      'summary':service.file_records('results/project2/sensitivity_v111/summary.csv'),
      'paired':service.file_records('results/project2/sensitivity_v111/paired_vs_base.csv')}


@app.get('/api/landscape')
def landscape():return service.landscape()


@app.get('/api/demo/{method}')
def demo(method:Literal['RANDOM','GREEDY','NSGA2']):
    path=service.ROOT/f'results/project2/react_demo/{method.lower()}.json'
    if not path.exists():raise HTTPException(503,'Preparar logs con python scripts/project2_prepare_demo.py')
    return FileResponse(path,media_type='application/json')


@app.post('/api/runs')
def runs(request:RunRequest):
    if not RUN_LOCK.acquire(blocking=False):raise HTTPException(429,'Ya hay un escenario en ejecución. Espera a que termine.')
    try:return service.run(request)
    except (ValueError,TypeError) as exc:raise HTTPException(422,str(exc)) from exc
    finally:RUN_LOCK.release()


DOWNLOADS={
 'comparison':'results/project2/integration/comparison_summary.csv',
 'paired':'results/project2/scientific_validation/archived_changes.csv',
 'validation':'results/project2/scientific_validation/empirical_errors.csv',
 'sensitivity':'results/project2/sensitivity_v111/summary.csv',
 'sensitivity-replicates':'results/project2/sensitivity_v111/replicates.csv',
 'seeds':'data/project2/processed/experiment_seeds.csv'}


@app.get('/api/download/{name}')
def download(name:str):
    if name not in DOWNLOADS:raise HTTPException(404,'Descarga no disponible')
    path=service.ROOT/DOWNLOADS[name]
    if not path.exists():raise HTTPException(404,'Evidencia todavía no generada')
    return FileResponse(path,media_type='text/csv',filename=path.name)


# A production build can be served on the same local origin as the API.
# Register last so static routes never shadow /api.
if (service.ROOT/'frontend/dist/index.html').exists():
    from fastapi.staticfiles import StaticFiles
    app.mount('/',StaticFiles(directory=service.ROOT/'frontend/dist',html=True),name='frontend')
