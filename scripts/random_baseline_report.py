"""Resumen y figuras del baseline RANDOM; solo lee el CSV, nunca vuelve a simular."""
from pathlib import Path
import argparse
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2.contract import bootstrap_ci
from bee_sim.project2.metrics import METRIC_NAMES, RESULT_COLUMNS
from bee_sim.visualization.plots import AMBAR, TINTA

BOOTSTRAP_SEED = 123
SYNTHETIC_NOTE = 'modo sintético · synthetic_RU, no recurso observado en Oslo'


def summarize(frame):
    """por metrica: media entre instalaciones con ic, y la variacion separada en dos.

    entre instalaciones = de de las medias por instalacion (efecto de la ubicacion).
    dentro = promedio de las de por instalacion (efecto del azar del motor).
    los vacios quedan como nan; no se rellenan con cero.
    """
    groups = frame.groupby('solution_id')[list(METRIC_NAMES)]
    means, spreads = groups.mean(), groups.std(ddof=1)
    rows = []
    for metric in METRIC_NAMES:
        values = means[metric].dropna().to_numpy(float)
        # el ic necesita al menos dos instalaciones con valor definido
        ci = bootstrap_ci(values, BOOTSTRAP_SEED) if len(values) >= 2 else {}
        rows.append({'metric': metric, 'mean_of_installation_means': ci.get('estimate', np.nan),
                     'ci_lower': ci.get('ci_lower', np.nan), 'ci_upper': ci.get('ci_upper', np.nan),
                     'between_installation_sd': means[metric].std(ddof=1),
                     'within_installation_sd_mean': spreads[metric].mean(),
                     'n_installations': len(means), 'replications_per_installation': int(groups.size().iloc[0]),
                     'n_undefined_rows': int(frame[metric].isna().sum()),
                     'bootstrap_seed': BOOTSTRAP_SEED, 'n_boot': ci.get('n_boot', np.nan)})
    return pd.DataFrame(rows)


def _finish(fig, ax):
    # la nota va al pie para que no tape barras ni cajas
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    fig.text(0.01, 0.01, SYNTHETIC_NOTE, fontsize=8, color=TINTA)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return fig


def plot_total_resource(frame):
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.hist(frame.total_resource_obtained, bins=30, color=AMBAR, edgecolor='white')
    ax.set_xlabel('recurso total entregado por réplica, synthetic_RU')
    ax.set_ylabel('réplicas (instalación × seed)')
    ax.set_title('RANDOM: recurso total entregado')
    return _finish(fig, ax)


def plot_mean_distance(frame):
    # ordenadas por mediana para que se lea la variacion entre instalaciones
    order = frame.groupby('solution_id').mean_distance_m.median().sort_values().index
    data = [frame.loc[frame.solution_id.eq(s), 'mean_distance_m'].dropna() for s in order]
    fig, ax = plt.subplots(figsize=(10.0, 4.5))
    ax.boxplot(data, patch_artist=True, widths=0.6,
               boxprops={'facecolor': AMBAR, 'edgecolor': TINTA, 'linewidth': 1},
               medianprops={'color': TINTA, 'linewidth': 2}, whiskerprops={'color': TINTA},
               capprops={'color': TINTA}, flierprops={'markeredgecolor': TINTA, 'markersize': 4})
    ax.set_xticks(range(1, len(order) + 1), [s.replace('random_', '') for s in order], rotation=90, fontsize=8)
    ax.set_xlabel('instalación (random_XXX), ordenada por mediana')
    ax.set_ylabel('distancia media de ida por réplica, m')
    ax.set_title('RANDOM: distancia media por instalación')
    return _finish(fig, ax)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='results/project2/random_results.csv')
    parser.add_argument('--summary-output', default='results/project2/random_summary.csv')
    parser.add_argument('--figures-dir', default='results/project2/figures')
    args = parser.parse_args()
    frame = pd.read_csv(ROOT / args.results)
    if tuple(frame.columns) != RESULT_COLUMNS or not frame['method'].eq('RANDOM').all():
        raise ValueError('Se espera un CSV del esquema común con method=RANDOM')
    summary_path = ROOT / args.summary_output
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summarize(frame).to_csv(summary_path, index=False, lineterminator='\n')
    figures = ROOT / args.figures_dir
    figures.mkdir(parents=True, exist_ok=True)
    for name, build in [('random_total_resource_hist.png', plot_total_resource),
                        ('random_mean_distance_box.png', plot_mean_distance)]:
        fig = build(frame)
        fig.savefig(figures / name, dpi=150)
        plt.close(fig)
    print(f'resumen: {summary_path.relative_to(ROOT)}; figuras: {figures.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
