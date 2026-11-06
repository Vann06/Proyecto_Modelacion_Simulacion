"""figuras del piloto de nsga-ii; el analisis vive en nsga2_pilot."""
import matplotlib.pyplot as plt
import numpy as np

COLORS = {'uniform': '#2a78d6', 'clustered': '#eb6834'}
MARKERS = {'uniform': 'o', 'clustered': '^'}
FAMILY_LABELS = {'uniform': 'Uniformes', 'clustered': 'Agrupadas'}
SERIES = ['#2a78d6', '#eb6834', '#1baf7a']
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
LABELS = {'total_resource_obtained': 'Recurso total (synthetic_RU)', 'mean_distance_m': 'Distancia media de ida (m)',
          'competition_pressure': 'Presión de competencia (%)'}
SHORT = {'total_resource_obtained': 'Recurso total', 'mean_distance_m': 'Distancia media',
         'competition_pressure': 'Competencia'}


def _style(ax):
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color(GRID)
    ax.grid(color=GRID, linewidth=.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def _axis_values(means, metric):
    return means[metric] * (100 if metric == 'competition_pressure' else 1)


def plot_objective_pairs(means, front):
    """tres vistas por pares; el frente de los tres objetivos va marcado con anillo."""
    pairs = [('total_resource_obtained', 'mean_distance_m'), ('total_resource_obtained', 'competition_pressure'),
             ('mean_distance_m', 'competition_pressure')]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), layout='constrained')
    for ax, (x, y) in zip(axes, pairs):
        for family, group in means.groupby('family'):
            ax.scatter(_axis_values(group, x), _axis_values(group, y), s=30, c=COLORS[family], marker=MARKERS[family],
                       alpha=.75, linewidths=0, label=FAMILY_LABELS[family])
        ax.scatter(_axis_values(means[front], x), _axis_values(means[front], y), s=80, facecolors='none',
                   edgecolors=INK, linewidths=1.2, label='Frente (3 objetivos)')
        ax.set(xlabel=LABELS[x], ylabel=LABELS[y])
        _style(ax)
    axes[0].legend(frameon=False, fontsize=9, labelcolor=MUTED, loc='upper right')
    fig.suptitle('Las 200 instalaciones del piloto: las agrupadas no llegan al frente', x=.01, ha='left', fontsize=13, color=INK)
    return fig


def plot_reliability(signal, replications=30, horizon=60):
    """fiabilidad esperada de la media segun el numero de replicas."""
    r = np.arange(1, horizon + 1)
    fig, ax = plt.subplots(figsize=(8, 4.2), layout='constrained')
    for color, (metric, row), offset in zip(SERIES, signal.iterrows(), (.02, -.025, -.03)):
        curve = row.sd_between ** 2 / (row.sd_between ** 2 + row.sd_noise ** 2 / r)
        ax.plot(r, curve, color=color, linewidth=2, label=SHORT[metric])
        ax.annotate(SHORT[metric], (horizon, curve[-1] + offset), xytext=(5, 0), textcoords='offset points',
                    va='center', fontsize=9, color=MUTED, annotation_clip=False)
    ax.axhline(.9, color=MUTED, linewidth=1, linestyle='--')
    ax.axvline(replications, color=MUTED, linewidth=1, linestyle=':')
    ax.text(horizon, .885, 'Fiabilidad 0.9', ha='right', va='top', fontsize=9, color=MUTED)
    ax.text(replications + .6, .03, f'{replications} réplicas de búsqueda', fontsize=9, color=MUTED)
    ax.set(xlabel='Réplicas promediadas por instalación', ylabel='Fiabilidad de la media', ylim=(0, 1.02), xlim=(1, horizon))
    ax.legend(frameon=False, fontsize=9, labelcolor=MUTED, loc='lower right', bbox_to_anchor=(1, .12))
    fig.suptitle('Competencia es el objetivo que fija el número de réplicas', x=.01, ha='left', fontsize=13, color=INK)
    _style(ax)
    return fig
