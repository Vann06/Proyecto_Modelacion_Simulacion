"""Comparación de resultados archivados: no ejecuta búsquedas ni simulaciones."""
from pathlib import Path
import argparse
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.analysis.project2_comparison import build_comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='results/project2/integration')
    parser.add_argument('--bootstrap', type=int, default=2000)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    data = build_comparison(ROOT, n_boot=args.bootstrap)
    for name in ['summary', 'paired', 'audit', 'nsga_installations']:
        data[name].to_csv(output / f'comparison_{name}.csv', index=False, lineterminator='\n')
    (output / 'comparison_metadata.json').write_text(json.dumps(data['metadata'], sort_keys=True, indent=2), encoding='utf-8')
    summary = data['summary']
    metrics = [('total_resource_obtained', 'Recurso entregado (synthetic_RU)'),
               ('mean_distance_m', 'Distancia media de ida (m)'), ('competition_pressure', 'Presión de competencia')]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    colors = ['#b78235', '#278875', '#5865b8']
    for ax, (metric, title) in zip(axes, metrics):
        rows = summary.loc[summary.metric.eq(metric)].set_index('method').loc[['RANDOM', 'GREEDY', 'NSGA2']]
        ax.bar(range(3), rows['mean'], color=colors)
        ax.errorbar(range(3), rows['mean'], yerr=[rows['mean'] - rows.ci95_low, rows.ci95_high - rows['mean']], fmt='none', color='#172b3a', capsize=4)
        ax.set_xticks(range(3), ['RANDOM', 'GREEDY', 'NSGA-II'])
        ax.set_title(title, fontsize=10)
        ax.grid(axis='y', alpha=.2)
        ax.set_axisbelow(True)
    fig.suptitle('Réplicas comunes 31–100 · comparación descriptiva del escenario sintético')
    fig.text(.01, .01, 'RANDOM: promedio de 30 instalaciones por seed. NSGA-II: ejemplo elegido con medias de búsqueda. IC 95% condicionales.', fontsize=8)
    fig.tight_layout(rect=(0, .05, 1, .94))
    fig.savefig(output / 'comparison_methods.png', dpi=150)
    plt.close(fig)
    cloud = data['nsga_installations'].loc[~data['nsga_installations'].physical_duplicate]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(cloud.mean_distance_m, cloud.total_resource_obtained, c=cloud.competition_pressure, cmap='viridis', label='Frente congelado: ubicaciones físicas distintas')
    for method, color in [('RANDOM', colors[0]), ('GREEDY', colors[1])]:
        vals = data['frames'][method].groupby('solution_id')[['mean_distance_m', 'total_resource_obtained']].mean()
        ax.scatter(vals.mean_distance_m, vals.total_resource_obtained, color=color, marker='x' if method == 'RANDOM' else 'D', label=method)
    ax.set(xlabel='Distancia media de ida (m)', ylabel='Recurso entregado (synthetic_RU)', title='Desempeño en holdout: no es un nuevo frente optimizado')
    ax.legend(fontsize=8)
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(output / 'comparison_tradeoffs.png', dpi=150)
    plt.close(fig)
    print(json.dumps(data['metadata'], indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
