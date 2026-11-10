"""Comparación GREEDY vs RANDOM con semillas pareadas. Recurso SINTÉTICO (synthetic_RU).

Requiere results/project2/greedy_results.csv y results/project2/random_results.csv
(este último lo genera la rama de RANDOM: 30 instalaciones aleatorias x 100 réplicas).

Diseño:
- GREEDY es una sola instalación determinista evaluada en 100 semillas comunes.
- RANDOM son 30 instalaciones independientes evaluadas en las mismas 100 semillas.
- Diferencia pareada por réplica: d_r = GREEDY_r - media sobre instalaciones de RANDOM_r.
  Bootstrap (5000, semilla 123) sobre las 100 diferencias. Captura la variación del motor
  pero no la variación entre instalaciones, que se reporta aparte con el percentil de GREEDY
  entre las medias por instalación de RANDOM.
Se rechaza la comparación si los hashes de config, motor, contrato o datos difieren.
"""
from pathlib import Path
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
contract = pd.read_csv(ROOT / 'data/project2/processed/simulation_metrics_contract.csv')
DIRECTION = dict(zip(contract.metric, contract.direction))
LABELS = {'total_resource_obtained': 'Recurso total (synthetic_RU)', 'mean_resource_per_hive': 'Recurso medio por colmena (synthetic_RU)',
          'min_resource_per_hive': 'Recurso mínimo por colmena (synthetic_RU)', 'mean_distance_m': 'Distancia media de ida (m)',
          'total_distance_m': 'Distancia total de ida (m)', 'p95_distance_m': 'Distancia P95 (m)',
          'competition_pressure': 'Presión de competencia (fracción)', 'hive_balance_jain': 'Índice de Jain',
          'patches_used_count': 'Parches usados (diagnóstico)'}
TAG = 'Recurso sintético (synthetic_RU), no es recurso observado en Oslo'

g = pd.read_csv(RES / 'greedy_results.csv')
r = pd.read_csv(RES / 'random_results.csv')
for col in ['config_hash', 'engine_hash', 'input_hash', 'metric_contract_hash', 'engine_version', 'K', 'scenario']:
    if g[col].nunique() != 1 or r[col].nunique() != 1 or g[col].iloc[0] != r[col].iloc[0]:
        sys.exit(f'No comparable: {col} difiere entre GREEDY y RANDOM. Reevaluar con el mismo entorno y config.')
if set(g.replication_id) != set(r.replication_id) or not (g.sort_values('replication_id').seed.values ==
        r[r.solution_id == r.solution_id.iloc[0]].sort_values('replication_id').seed.values).all():
    sys.exit('Las semillas/réplicas no coinciden.')

rng = np.random.default_rng(123)
rows, paired = [], {}
for m, direction in DIRECTION.items():
    gm = g.set_index('replication_id')[m].sort_index()
    rm = r.groupby('replication_id')[m].mean().sort_index()           # media sobre instalaciones por semilla
    d = (gm - rm).dropna().to_numpy(float)
    boots = rng.choice(d, size=(5000, len(d)), replace=True).mean(axis=1)
    inst = r.groupby('solution_id')[m].mean()                        # una media por instalación aleatoria
    # fracción de instalaciones RANDOM con peor media que GREEDY según la dirección del contrato
    if direction == 'minimize':
        share = float((inst > gm.mean()).mean())
    elif direction == 'maximize':
        share = float((inst < gm.mean()).mean())
    else:
        share = float('nan')
    rows.append({'metric': m, 'direction': direction, 'greedy_mean': gm.mean(), 'random_mean': rm.mean(),
                 'abs_change': d.mean(), 'pct_change_vs_random': 100 * d.mean() / rm.mean() if rm.mean() else np.nan,
                 'paired_diff_ci95_low': np.quantile(boots, .025), 'paired_diff_ci95_high': np.quantile(boots, .975),
                 'n_pairs': len(d), 'random_installations': len(inst),
                 'share_random_installations_worse_than_greedy': share})
    paired[m] = (gm, rm, inst)
table = pd.DataFrame(rows)
table.to_csv(RES / 'greedy_vs_random.csv', index=False, lineterminator='\n')

# Figura 5: pareado por semilla (3 métricas) + dispersión de instalaciones RANDOM.
panel = ['total_resource_obtained', 'mean_distance_m', 'hive_balance_jain']
fig, axes = plt.subplots(2, 3, figsize=(13, 8))
for j, m in enumerate(panel):
    gm, rm, inst = paired[m]
    ax = axes[0, j]
    ax.boxplot([gm.to_numpy(), rm.to_numpy()], tick_labels=['GREEDY', 'RANDOM\n(media de 30 inst.)'])
    ax.set_ylabel(LABELS[m]); ax.grid(alpha=.3)
    ax.set_title('Por semilla común (n = 100)')
    ax = axes[1, j]
    ax.hist(inst, bins=12, color='#aab7c4', edgecolor='white', label='Instalaciones RANDOM (media de 100 réplicas)')
    ax.axvline(gm.mean(), color='#c0392b', lw=2, label='GREEDY (media de 100 réplicas)')
    ax.set_xlabel(LABELS[m]); ax.set_ylabel('Número de instalaciones'); ax.grid(alpha=.3)
    if j == 0: ax.legend(fontsize=7)
fig.suptitle('GREEDY vs RANDOM con semillas pareadas')
fig.text(.01, .005, TAG, fontsize=7)
fig.tight_layout(rect=(0, .02, 1, .96)); fig.savefig(FIG / 'greedy_fig5_vs_random.png', dpi=160); plt.close(fig)
pd.set_option('display.width', 220)
print(table.round(4).to_string(index=False))
