"""Reproduce the empirical reference audit without changing historical inputs."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bee_sim.analysis.project2_validation import prepare_observations,benchmark,percentage_change
from bee_sim.analysis.project2_comparison import build_comparison


def main():
    out=ROOT/'results/project2/scientific_validation'
    out.mkdir(parents=True,exist_ok=True)
    flowers,sessions,metadata=prepare_observations(ROOT)
    bank=pd.read_csv(ROOT/'data/project2/processed/experiment_seeds.csv').iloc[30:60]
    seeds=[(int(r.replication_id),int(r.seed)) for r in bank.itertuples()]
    rows=[]
    for label,frame,unit in [('flowers',flowers,'flores/m²'),('activity',sessions,'conteos registrados/minuto de sesión candidata')]:
        split,test,draws,errors=benchmark(frame,label,unit,seeds)
        for suffix,data in [('observations',frame),('split',split),('evaluation',test),('replicates',draws),('errors',errors)]:
            data.to_csv(out/f'{label}_{suffix}.csv',index=False,lineterminator='\n')
        rows.append(errors)
        plot_unit = 'conteos/min de sesión' if label=='activity' else unit
        fig,axes=plt.subplots(1,2,figsize=(11,4.6))
        for col,title,color in [('reference_base','Referencia global','#bd943e'),('reference_stratified','Referencia estratificada','#24816c')]:
            axes[0].scatter(test.observed,test[col],label=title,alpha=.65,s=25,color=color)
        limit=max(test.observed.max(),test.reference_stratified.max())
        axes[0].plot([0,limit],[0,limit],'--',color='#555',label='Igualdad')
        axes[0].set(xlabel=f'Observado ({plot_unit})',ylabel=f'Predicción ({plot_unit})',title='Sitios excluidos de calibración')
        axes[0].legend(fontsize=8)
        axes[1].hist(test.observed,bins=14,color='#24816c',alpha=.75)
        axes[1].set(xlabel=f'Observado ({plot_unit})',ylabel='Unidades de evaluación',title='Dispersión real, sin equivalencia con RU')
        fig.tight_layout();fig.savefig(out/f'{label}_validation.png',dpi=150);plt.close(fig)
    pd.concat(rows).to_csv(out/'empirical_errors.csv',index=False,lineterminator='\n')
    comparison=build_comparison(ROOT)
    improvements=[]
    for row in comparison['paired'].itertuples():
        left,right=row.contrast.split('-')
        baseline=float(comparison['summary'].query('method == @right and metric == @row.metric')['mean'].iloc[0])
        improvements.append({**row._asdict(),'baseline_mean':baseline,'percent_change':percentage_change(row.difference+baseline,baseline),
            'percentage_ci_low_conditional_on_baseline_mean':percentage_change(row.ci95_low+baseline,baseline),
            'percentage_ci_high_conditional_on_baseline_mean':percentage_change(row.ci95_high+baseline,baseline),
            'note':'sign is change, not universal improvement; percentage interval uses fixed baseline mean'})
    pd.DataFrame(improvements).to_csv(out/'archived_changes.csv',index=False,lineterminator='\n')
    inventory=[]
    for p in sorted((ROOT/'notebooks/project2').glob('*.ipynb')):
        if p.name.startswith('09_'):continue  # do not embed a self-referential notebook hash
        n=json.loads(p.read_text(encoding='utf-8'));source='\n'.join(''.join(c['source']) for c in n['cells'])
        inventory.append({'notebook':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cells':len(n['cells']),
          'error_outputs':sum(o.get('output_type')=='error' for c in n['cells'] for o in c.get('outputs',[])),
          'temporal_wording_requires_care':'calibrated_window' in source,'status':'reviewed; legacy outputs retained'})
    pd.DataFrame(inventory).to_csv(out/'notebook_audit.csv',index=False,lineterminator='\n')
    metadata.update({'split_seed':20261107,'bootstrap_error_seed':17,'train_bootstrap_replications':30,
      'engine_calibrated':False,'observation_operator_available':False,
      'empirical_models':'global mean vs month-stratified floral / fixed temperature-bin activity means; separate empirical references',
      'limitations':['No trap-to-GIS mapping','No RU conversion','No trips-to-counts observation process',
        'Candidate sessions may recount individuals; all pollinator taxa, not honeybees only',
        'Floral transect aggregation assumes rows describe same trap/date footprint',
        'Spatial holdout within sample, not temporal or city-wide generalization'],
      'archived_identity':comparison['audit'].iloc[0].to_dict()})
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(metadata,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
