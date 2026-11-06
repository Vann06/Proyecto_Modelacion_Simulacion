"""Baseline RANDOM: genera N instalaciones, las evalúa con el motor común y guarda todo."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config
from bee_sim.project2.distance import load_landscape
from bee_sim.project2.metrics import write_results
from bee_sim.project2.strategies.random_baseline import METHOD, generate_installations, evaluate_installation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config/project2/base.yaml')
    parser.add_argument('--n-installations', type=int, default=30)
    parser.add_argument('--optimizer-seed', type=int, default=123, help='seed base; la instalación i usa base + i')
    parser.add_argument('--replications', type=int, default=30)
    parser.add_argument('--sites-output', default='results/project2/random_sites.json')
    parser.add_argument('--output', default='results/project2/random_results.csv')
    args = parser.parse_args()
    cfg = load_config(ROOT / args.config)
    candidates = load_landscape(cfg)[0]
    installations = generate_installations(candidates, cfg['K'], args.n_installations, args.optimizer_seed)
    sites_path = ROOT / args.sites_output
    sites_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {'method': METHOD, 'scenario': cfg.scenario, 'config_hash': cfg.config_hash, 'K': cfg['K'],
               'n_installations': args.n_installations, 'base_seed': args.optimizer_seed,
               'installations': installations}
    # newline fijo para que el json salga igual en cualquier sistema
    sites_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    rows, example = [], None
    for i, (solution_id, installation) in enumerate(installations.items(), 1):
        found, first = evaluate_installation(solution_id, installation, cfg, args.replications)
        rows += found
        if example is None:
            example = first
        print(f'{i}/{len(installations)} {solution_id} listo', flush=True)
    output = ROOT / args.output
    write_results(rows, output)
    # mismo formato de logs que project2_run.py, para no inventar otro
    detail = output.parent / (output.stem + '_example')
    detail.mkdir(parents=True, exist_ok=True)
    for key in ['per_hive', 'trips', 'resource_log', 'events']:
        example[key].to_csv(detail / (key + '.csv'), index=False, lineterminator='\n')
    (detail / 'provenance.json').write_text(json.dumps(example['provenance'], sort_keys=True, indent=2), encoding='utf-8')
    (detail / 'config_records.json').write_text(json.dumps(cfg.records, ensure_ascii=False, sort_keys=True, indent=2), encoding='utf-8')
    print(f'{len(rows)} filas SINTÉTICAS ({len(installations)} instalaciones x {args.replications} réplicas): '
          f'{output.relative_to(ROOT)}; sitios: {sites_path.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
