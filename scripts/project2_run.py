"""CLI común: preparar geografía, smoke fijo y evaluar selecciones externas."""
from pathlib import Path
import argparse
import json
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bee_sim.project2 import load_config, simulate
from bee_sim.project2.distance import prepare_resources
from bee_sim.project2.metrics import result_row, write_results, RESULT_COLUMNS, METHODS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare')
    for command in ['smoke', 'evaluate']:
        p = sub.add_parser(command)
        p.add_argument('--config', default='config/project2/base.yaml')
        p.add_argument('--replications', type=int, default=2 if command == 'smoke' else None)
        p.add_argument('--output', default='results/project2/smoke_results.csv' if command == 'smoke' else None,
                       required=command == 'evaluate')
        if command == 'evaluate':
            p.add_argument('--sites-file', required=True, help='JSON con lista de site_id, o diccionario replication_id -> lista')
            p.add_argument('--method', required=True, choices=METHODS[:-1])
            p.add_argument('--solution-id', default='solution_001')
            p.add_argument('--optimizer-seed', type=int)
    p = sub.add_parser('inspect')
    p.add_argument('--results', required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        manifest = prepare_resources(ROOT)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return
    if args.command == 'inspect':
        frame = pd.read_csv(ROOT / args.results)
        if tuple(frame.columns) != RESULT_COLUMNS:
            raise ValueError('Esquema no contractual')
        print(frame[['method', 'scenario', 'K', 'replication_id', 'seed', 'mode', 'total_resource_obtained']].to_string(index=False))
        print('Filas:', len(frame), '| configuraciones:', frame.config_hash.nunique(), '| versiones:', frame.engine_version.unique())
        return
    cfg = load_config(ROOT / args.config)
    bank = pd.read_csv(ROOT / cfg['seed_bank_file'])
    count = cfg['replications'] if args.replications is None else args.replications
    if count < 1 or count > min(cfg['replications'], len(bank)):
        raise ValueError('Número de réplicas fuera de configuración/banco')
    if args.command == 'smoke':
        # Fixture determinista, no baseline ni recomendación de instalación.
        candidates = pd.read_csv(ROOT / 'data/project2/processed/candidate_hive_sites.csv')
        placements = sorted(candidates.site_id)[:cfg['K']]
        method, solution_id, optimizer_seed = 'SMOKE_FIXED_SITES', 'fixed_fixture', None
    else:
        placements = json.loads((ROOT / args.sites_file).read_text(encoding='utf-8-sig'))
        method, solution_id, optimizer_seed = args.method, args.solution_id, args.optimizer_seed
    rows, first = [], None
    for item in bank.head(count).itertuples(index=False):
        sites = placements[str(int(item.replication_id))] if isinstance(placements, dict) else placements
        result = simulate(sites, int(item.seed), cfg)
        rows.append(result_row(method, int(item.replication_id), result, cfg, solution_id, optimizer_seed))
        if first is None:
            first = result
    output = ROOT / args.output
    write_results(rows, output)
    detail = output.parent / (output.stem + '_example')
    detail.mkdir(parents=True, exist_ok=True)
    for key in ['per_hive', 'trips', 'resource_log', 'events']:
        first[key].to_csv(detail / (key + '.csv'), index=False, lineterminator='\n')
    (detail / 'provenance.json').write_text(json.dumps(first['provenance'], sort_keys=True, indent=2), encoding='utf-8')
    (detail / 'config_records.json').write_text(json.dumps(cfg.records, ensure_ascii=False, sort_keys=True, indent=2), encoding='utf-8')
    print(f'{count} réplicas SINTÉTICAS: {output.relative_to(ROOT)}; logs de primera réplica: {detail.relative_to(ROOT)}')
    if args.command == 'smoke':
        print('Selección fija de fixture. NO implementa RANDOM, GREEDY ni NSGA-II y no calibra Oslo.')


if __name__ == '__main__':
    main()
