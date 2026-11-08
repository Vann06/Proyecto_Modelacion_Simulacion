"""Freeze small display logs under current engine; never rerun optimization."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.main import RunRequest
from backend.service import run

if __name__=='__main__':
    folder=ROOT/'results/project2/react_demo';folder.mkdir(exist_ok=True,parents=True)
    for method in ['RANDOM','GREEDY','NSGA2']:
        path=folder/(method.lower()+'.json')
        if path.exists():raise SystemExit(f'No sobrescribir demo existente: {path}')
        result=run(RunRequest(method=method));result['kind']='archived_demo_v111'
        path.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
        print(method,len(result['trips']),'viajes, demo motor 1.1.1')
