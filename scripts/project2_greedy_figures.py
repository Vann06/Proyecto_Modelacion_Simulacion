"""Figuras y tabla resumen de GREEDY. Todo el recurso es SINTÉTICO (synthetic_RU).

Requiere haber ejecutado `select` y `evaluate`. La comparación con RANDOM está en project2_greedy_vs_random.py.
"""
from pathlib import Path
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
RES = ROOT / 'results/project2'
FIG = RES / 'figures_greedy'
FIG.mkdir(parents=True, exist_ok=True)
METRICS = ['total_resource_obtained', 'mean_resource_per_hive', 'min_resource_per_hive', 'mean_distance_m',
           'total_distance_m', 'p95_distance_m', 'competition_pressure', 'hive_balance_jain', 'patches_used_count']
TAG = 'Recurso sintético (synthetic_RU), no es recurso observado en Oslo'

results = pd.read_csv(RES / 'greedy_results.csv')
steps = pd.read_csv(RES / 'greedy_construction.csv')
sites = json.loads((RES / 'greedy_sites.json').read_text(encoding='utf-8'))
order = json.loads((RES / 'greedy_params.json').read_text(encoding='utf-8'))['selection_order']
cand = pd.read_csv(ROOT / 'data/project2/processed/candidate_hive_sites.csv').set_index('site_id')

# Tabla resumen: media, desviación estándar muestral e IC95% t sobre réplicas.
from scipy import stats
rows = []
for m in METRICS:
    x = results[m].dropna().to_numpy(float)
    n = len(x)
    sd = x.std(ddof=1) if n > 1 else np.nan
    half = stats.t.ppf(.975, n - 1) * sd / np.sqrt(n) if n > 1 else np.nan
    rows.append({'metric': m, 'n': n, 'mean': x.mean(), 'sd': sd, 'ci95_low': x.mean() - half,
                 'ci95_high': x.mean() + half, 'min': x.min(), 'max': x.max()})
pd.DataFrame(rows).to_csv(RES / 'greedy_summary.csv', index=False, lineterminator='\n')

# Fig 1: ganancia marginal por candidato en cada paso de construcción.
fig, ax = plt.subplots(figsize=(8, 4.8))
for step, g in steps.groupby('step'):
    avail = g[~g.already_chosen].marginal_gain.sort_values(ascending=False).to_numpy()
    line, = ax.plot(np.arange(1, len(avail) + 1), avail, label=f'Paso {step}')
    ax.scatter([1], [g[g.chosen_at_step].marginal_gain.iloc[0]], color=line.get_color(), zorder=3)
ax.set_xscale('log')
ax.set_xlabel('Ranking del candidato en el paso (escala log)')
ax.set_ylabel('Ganancia marginal (synthetic_RU ponderadas)')
ax.set_title('GREEDY: ganancia marginal de los candidatos por paso\n(punto = sitio elegido)')
ax.legend(); ax.grid(alpha=.3)
fig.text(.01, .01, TAG, fontsize=7)
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG / 'greedy_fig1_ganancia_por_paso.png', dpi=160); plt.close(fig)

# Fig 2: mapa de selección con parques y radio de forrajeo.
parks = gpd.read_file(ROOT / 'data/project2/processed/oslo_parks.geojson').to_crs(25833)
fig, ax = plt.subplots(figsize=(7.5, 7.5))
parks.plot(ax=ax, color='#cfe8cf', edgecolor='none')
ax.scatter(cand.x_m, cand.y_m, s=5, color='#888888', label='Candidatos (375)')
for k, sid in enumerate(order, 1):
    x, y = cand.loc[sid, ['x_m', 'y_m']]
    ax.add_patch(plt.Circle((x, y), 3000, fill=False, color='#c0392b', alpha=.6))
    ax.scatter([x], [y], s=70, color='#c0392b', zorder=3, label='Elegidos' if k == 1 else None)
    ax.annotate(str(k), (x, y), xytext=(6, 6), textcoords='offset points', fontsize=11, weight='bold')
ax.set_aspect('equal'); ax.legend(loc='lower left')
ax.set_xlabel('Este (m, EPSG:25833)'); ax.set_ylabel('Norte (m, EPSG:25833)')
ax.set_title('GREEDY: sitios elegidos (número = orden) y radio de 3000 m')
ax.grid(alpha=.2); ax.ticklabel_format(style='plain', useOffset=False)
fig.tight_layout(); fig.savefig(FIG / 'greedy_fig2_mapa_seleccion.png', dpi=160); plt.close(fig)

# Fig 3: recurso por colmena y distancias de ida (primera réplica).
ex = RES / 'greedy_results_example'
per_hive = pd.read_csv(ex / 'per_hive.csv')
trips = pd.read_csv(ex / 'trips.csv')
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].bar([f'C{i + 1}' for i in per_hive.hive_slot], per_hive.resource_delivered, color='#2e86c1')
axes[0].set_xlabel('Colmena (slot)'); axes[0].set_ylabel('Recurso entregado (synthetic_RU)')
axes[0].set_title('Recurso entregado por colmena (réplica 1)')
axes[1].hist(trips.one_way_distance_m, bins=30, color='#7d3c98')
axes[1].set_xlabel('Distancia de ida (m)'); axes[1].set_ylabel('Número de viajes')
axes[1].set_title('Distribución de distancias de ida (réplica 1)')
for a in axes: a.grid(alpha=.3)
fig.text(.01, .01, TAG, fontsize=7)
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG / 'greedy_fig3_recurso_distancia.png', dpi=160); plt.close(fig)

# Fig 4: variabilidad de GREEDY entre réplicas (la comparación con RANDOM está en project2_greedy_vs_random.py).
panel = [('total_resource_obtained', 'Recurso total (synthetic_RU)'), ('mean_distance_m', 'Distancia media de ida (m)'),
         ('hive_balance_jain', 'Índice de Jain (adimensional)')]
fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))
for ax, (col, label) in zip(axes, panel):
    ax.boxplot([results[col].dropna()], tick_labels=['GREEDY'])
    ax.set_ylabel(label); ax.grid(alpha=.3)
fig.suptitle('Variabilidad de GREEDY entre las 100 réplicas con semillas comunes')
fig.text(.01, .01, TAG, fontsize=7)
fig.tight_layout(rect=(0, .03, 1, .95)); fig.savefig(FIG / 'greedy_fig4_boxplots.png', dpi=160); plt.close(fig)
print('Listo:', *sorted(p.name for p in FIG.iterdir()), sep='\n  ')
