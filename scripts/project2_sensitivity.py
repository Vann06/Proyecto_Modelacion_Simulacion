"""One-factor-at-a-time sensitivity, 30 common holdout seeds per condition.

Frozen NSGA locations are reevaluated, never reoptimized. K variants have no
NSGA result because its frozen solutions contain exactly five sites.
"""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse,json,sys,time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bee_sim.project2 import load_config,with_parameters,simulate
from bee_sim.project2.contract import bootstrap_ci
from bee_sim.project2.metrics import result_row
from bee_sim.project2.strategies.random_baseline import select_sites as random_sites
from bee_sim.project2.strategies.greedy_baseline import select_sites as greedy_sites
from bee_sim.analysis.project2_comparison import representative_front

SCENARIOS={'base':{},'resource_low':{'initial_resource_total':500.},'resource_high':{'initial_resource_total':1500.},
 'K3':{'K':3},'K8':{'K':8},'competition_off':{'alpha':0.},'competition_high':{'alpha':4.},
 'radius_short':{'max_foraging_distance_m':1500.},'radius_long':{'max_foraging_distance_m':5000.},
 'regeneration_off':{'regeneration_rate':0.},'regeneration_high':{'regeneration_rate':.2},
 'distance_low':{'beta':1.},'distance_high':{'beta':3.},'activity_high':{'departures_per_day':24.}}


def evaluate(task):
    scenario,method,sites,replication,seed,cfg=task
    result=simulate(sites,seed,cfg)
    return {**result_row(method,replication,result,cfg,f'{scenario}_{method}',2026), 'experiment_condition':scenario}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if not 1<=args.workers<=8:parser.error('workers debe estar entre 1 y 8')
    out=ROOT/'results/project2/sensitivity_v111';out.mkdir(parents=True,exist_ok=True)
    path=out/'replicates.csv'
    if path.exists():raise SystemExit('Ya existe una cohorte. Conservarla; no sobrescribir ni mezclar ejecuciones.')
    base=load_config(ROOT/'config/project2/base.yaml')
    candidates=pd.read_csv(ROOT/'data/project2/processed/candidate_hive_sites.csv')
    bank=pd.read_csv(ROOT/base['seed_bank_file']).iloc[30:60]
    nsga,_=representative_front(ROOT)
    tasks=[];settings=[]
    for name,values in SCENARIOS.items():
        cfg=with_parameters(base,**values) if values else base
        installations={'RANDOM':list(random_sites(candidates,cfg['K'],2026)), 'GREEDY':greedy_sites(cfg)['site_ids']}
        if cfg['K']==5:installations['NSGA2']=nsga['site_ids']
        settings.append({'condition':name,'config_hash':cfg.config_hash,'parameters':cfg.parameters.copy(),
                         'sites':installations,'nsga_status':'reevaluate frozen sites' if cfg['K']==5 else 'not available for different K'})
        tasks.extend((name,m,sites,int(r.replication_id),int(r.seed),cfg) for m,sites in installations.items() for r in bank.itertuples())
    started=time.perf_counter();rows=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(evaluate,tasks,chunksize=5):
            rows.append(row)
            if len(rows)%90==0:print(f'{len(rows)}/{len(tasks)} simulaciones',flush=True)
    df=pd.DataFrame(rows);df.to_csv(path,index=False,lineterminator='\n')
    summaries=[];differences=[]
    metrics=['total_resource_obtained','min_resource_per_hive','mean_distance_m','competition_pressure','hive_balance_jain']
    for (condition,method),group in df.groupby(['experiment_condition','method']):
        baseline=df.loc[df.experiment_condition.eq('base')&df.method.eq(method)].set_index('seed')
        for metric in metrics:
            values=group[metric].dropna().to_numpy(float)
            ci=bootstrap_ci(values,seed=17,n_boot=2000) if len(values)>1 else {}
            summaries.append({'condition':condition,'method':method,'metric':metric,'mean':float(np.mean(values)) if len(values) else None,
                'std':float(np.std(values,ddof=1)) if len(values)>1 else None,'n':len(values),**ci})
            paired=(group.set_index('seed')[metric]-baseline[metric]).dropna().to_numpy(float)
            paired_ci=bootstrap_ci(paired,seed=17,n_boot=2000) if len(paired)>1 else {}
            differences.append({'condition':condition,'method':method,'metric':metric,'n_pairs':len(paired),**paired_ci})
    summary=pd.DataFrame(summaries);summary.to_csv(out/'summary.csv',index=False,lineterminator='\n')
    pd.DataFrame(differences).to_csv(out/'paired_vs_base.csv',index=False,lineterminator='\n')
    meta={'engine_version':df.engine_version.iloc[0],'engine_hash':df.engine_hash.iloc[0],
      'input_hash':df.input_hash.iloc[0],'replications':30,'replication_ids':bank.replication_id.tolist(),
      'seeds':bank.seed.astype(int).tolist(),'simulations':len(df),'elapsed_seconds':time.perf_counter()-started,
      'optimizer_seed':2026,'nsga_solution_id':nsga['solution_id'],'conditions':settings,
      'design':'OAT synthetic sensitivity, common seeds 31–60; fixed RANDOM optimizer seed; reselect GREEDY for each config',
      'limitations':['not ecological calibration','NSGA sites frozen, not reoptimized',
        'not independent holdout after prior inspection','no interactions or optimizer-seed robustness',
        'changing K changes total travel opportunities; not a controlled density-only intervention']}
    (out/'metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    fig,axes=plt.subplots(2,1,figsize=(13,8),sharex=True)
    for ax,metric,label in zip(axes,['total_resource_obtained','mean_distance_m'],['Recurso entregado (synthetic_RU)','Distancia media de ida (m)']):
        for method,color in [('RANDOM','#bc9643'),('GREEDY','#287c68'),('NSGA2','#6975c4')]:
            d=summary.loc[summary.metric.eq(metric)&summary.method.eq(method)].set_index('condition').reindex(SCENARIOS)
            ax.errorbar(range(len(d)),d['mean'],yerr=[d['mean']-d.ci_lower,d.ci_upper-d['mean']],label=method,color=color,marker='o',capsize=3)
        ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(fontsize=8)
    axes[0].set_title('Sensibilidad sintética: 30 seeds comunes por método y condición, IC 95%')
    axes[-1].set_xticks(range(len(SCENARIOS)),SCENARIOS.keys(),rotation=45,ha='right');fig.tight_layout()
    fig.savefig(out/'sensitivity.png',dpi=150);plt.close(fig)
    print(f'Finalizado: {len(df)} corridas, {meta["elapsed_seconds"]:.1f}s',flush=True)

if __name__=='__main__':main()
