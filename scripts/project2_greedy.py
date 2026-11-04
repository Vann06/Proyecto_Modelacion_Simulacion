"""Genera la selección GREEDY y guarda IDs, pasos de construcción y parámetros.

Uso (desde la raíz del repositorio):
    python scripts/project2_greedy.py select
Luego evaluar con el CLI común (ver docs/project2/greedy_design.md).
"""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config
from bee_sim.project2.strategies.greedy_baseline import select_sites


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['select'])
    parser.add_argument('--config', default='config/project2/base.yaml')
    parser.add_argument('--out-dir', default='results/project2')
    args = parser.parse_args()
    cfg = load_config(ROOT / args.config)
    result = select_sites(cfg)
    out = ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / 'greedy_sites.json').write_text(json.dumps(result['site_ids'], indent=2) + '\n', encoding='utf-8')
    result['steps'].to_csv(out / 'greedy_construction.csv', index=False, lineterminator='\n')
    meta = {'method': 'GREEDY', 'config_hash': cfg.config_hash, 'K': cfg['K'],
            'selection_order': result['selection_order'],
            'greedy_params': {'distance_exponent': result['params'].distance_exponent,
                              'overlap_penalty': result['params'].overlap_penalty},
            'tie_break': 'menor site_id', 'uses_randomness': False,
            'note': 'Score ex ante sintetico: no es competencia observada ni resultado de simulate.'}
    (out / 'greedy_params.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('GREEDY:', *result['selection_order'], sep='\n  ')


if __name__ == '__main__':
    main()
