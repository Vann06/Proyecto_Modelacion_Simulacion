"""Comparación GREEDY vs NSGA-II en las réplicas reservadas 31-100. Recurso SINTÉTICO (synthetic_RU).

Requiere results/project2/greedy_results.csv y results/project2/nsga2_results.csv (rama NSGA-II:
frente de 49 soluciones congelado con las réplicas 1-30 y evaluado en las réplicas 31-100).
Si existe random_results.csv, se agrega la media de RANDOM como contexto.

Diseño:
- GREEDY se recorta a las réplicas 31-100 para usar las mismas 70 semillas que NSGA-II.
- Diferencia pareada por semilla entre una solución de NSGA-II (por defecto pareto_013, la que
  NSGA-II recomienda) y GREEDY, con bootstrap (5000, semilla 123).
- Como la solución recomendada se eligió viendo el conjunto reservado, también se reporta la
  mediana del frente y cuántas de las 49 soluciones superan a GREEDY en cada métrica.
- Dominancia de Pareto sobre los tres objetivos de NSGA-II (recurso total, distancia media y competencia).
Se detiene si los hashes de config, motor, contrato o datos, o las semillas, no coinciden.
"""
from pathlib import Path
import argparse
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results/project2'
FIG = RES / 'figures_greedy'
FIG.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--solution', default='pareto_013')
args = parser.parse_args()
contract = pd.read_csv(ROOT / 'data/project2/processed/simulation_metrics_contract.csv')
DIRECTION = dict(zip(contract.metric, contract.direction))
METRICS = ['total_resource_obtained', 'min_resource_per_hive', 'mean_distance_m', 'p95_distance_m',
           'competition_pressure', 'hive_balance_jain']
OBJECTIVES = ['total_resource_obtained', 'mean_distance_m', 'competition_pressure']
TAG = 'Recurso sintético (synthetic_RU), no es recurso observado en Oslo'

g = pd.read_csv(RES / 'greedy_results.csv')
n = pd.read_csv(RES / 'nsga2_results.csv')
for col in ['config_hash', 'engine_hash', 'input_hash', 'metric_contract_hash', 'engine_version', 'K', 'scenario']:
    if g[col].nunique() != 1 or n[col].nunique() != 1 or g[col].iloc[0] != n[col].iloc[0]:
        sys.exit(f'No comparable: {col} difiere entre GREEDY y NSGA-II.')
g = g[g.replication_id >= 31].set_index('replication_id').sort_index()
first = n[n.solution_id == n.solution_id.iloc[0]].set_index('replication_id').sort_index()
if list(g.index) != list(first.index) or not (g.seed.values == first.seed.values).all():
    sys.exit('Las réplicas o semillas reservadas no coinciden.')
if args.solution not in set(n.solution_id):
    sys.exit(f'No existe la solución {args.solution}.')
sel = n[n.solution_id == args.solution].set_index('replication_id').sort_index()
front = n.groupby('solution_id')[METRICS].mean()
rnd = None
if (RES / 'random_results.csv').is_file():
    r = pd.read_csv(RES / 'random_results.csv')
    if r.config_hash.nunique() == 1 and r.config_hash.iloc[0] == g.config_hash.iloc[0]:
        r = r[r.replication_id >= 31]
        rnd = r.groupby('solution_id')[METRICS].mean()

rng = np.random.default_rng(123)
rows = []
for m in METRICS:
    d = (sel[m] - g[m]).to_numpy(float)
    boots = rng.choice(d, size=(5000, len(d)), replace=True).mean(axis=1)
    better = (front[m] < g[m].mean()) if DIRECTION[m] == 'minimize' else (front[m] > g[m].mean())
    rows.append({'metric': m, 'direction': DIRECTION[m], 'greedy_mean': g[m].mean(), 'nsga2_selected_mean': sel[m].mean(),
                 'nsga2_front_median': front[m].median(), 'random_mean': rnd[m].mean() if rnd is not None else np.nan,
                 'abs_change': d.mean(), 'pct_change': 100 * d.mean() / g[m].mean(),
                 'paired_diff_ci95_low': np.quantile(boots, .025), 'paired_diff_ci95_high': np.quantile(boots, .975),
                 'n_pairs': len(d), 'front_solutions': len(front), 'front_solutions_better_than_greedy': int(better.sum())})
pd.DataFrame(rows).to_csv(RES / 'greedy_vs_nsga2.csv', index=False, lineterminator='\n')

sign = {m: (-1 if DIRECTION[m] == 'maximize' else 1) for m in OBJECTIVES}   # convierte todo a minimizar
F = pd.DataFrame({m: sign[m] * front[m] for m in OBJECTIVES})
G = pd.Series({m: sign[m] * g[m].mean() for m in OBJECTIVES})
dominate_g = ((F <= G).all(axis=1) & (F < G).any(axis=1))
extra = {'selected_solution': args.solution, 'front_solutions': int(len(front)),
         'front_dominating_greedy': int(dominate_g.sum()),
         'front_dominated_by_greedy': int((((G <= F).all(axis=1)) & ((G < F).any(axis=1))).sum()),
         'front_better_in_resource_and_distance': int(((front.total_resource_obtained > g.total_resource_obtained.mean()) &
                                                       (front.mean_distance_m < g.mean_distance_m.mean())).sum()),
         'front_resource_range': [float(front.total_resource_obtained.min()), float(front.total_resource_obtained.max())],
         'front_distance_range': [float(front.mean_distance_m.min()), float(front.mean_distance_m.max())],
         'replications': [int(g.index.min()), int(g.index.max())]}
(RES / 'greedy_vs_nsga2_extra.json').write_text(json.dumps(extra, indent=2) + '\n', encoding='utf-8')

fig, ax = plt.subplots(figsize=(7.5, 5.6))
if rnd is not None:
    ax.scatter(rnd.mean_distance_m, rnd.total_resource_obtained, s=22, color='#c8d0d8', label='RANDOM (30 instalaciones)')
ax.scatter(front.mean_distance_m, front.total_resource_obtained, s=30, color='#2e86c1', alpha=.8, label='NSGA-II (49 soluciones del frente)')
ax.scatter([sel.mean_distance_m.mean()], [sel.total_resource_obtained.mean()], s=110, marker='D', color='#1b4f72', zorder=4, label=f'NSGA-II {args.solution}')
ax.scatter([g.mean_distance_m.mean()], [g.total_resource_obtained.mean()], s=190, marker='*', color='#c0392b', zorder=5, label='GREEDY')
ax.set_xlabel('Distancia de ida media (m)  - menor es mejor')
ax.set_ylabel('Recurso total entregado (synthetic_RU)  - mayor es mejor')
ax.set_title('GREEDY y NSGA-II en las réplicas reservadas 31 a 100')
ax.grid(alpha=.3); ax.legend(fontsize=8, loc='lower right')
fig.text(.01, .01, TAG, fontsize=7)
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG / 'greedy_fig6_vs_nsga2.png', dpi=160); plt.close(fig)
pd.set_option('display.width', 220)
print(pd.DataFrame(rows).round(4).to_string(index=False)); print(json.dumps(extra, indent=2))
