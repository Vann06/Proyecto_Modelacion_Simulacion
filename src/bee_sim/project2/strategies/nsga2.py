"""nsga-ii sobre instalaciones de K sitios; evalua con simulate y no toca el motor.

busca solo con replicas 1-30. el frente se congela antes de evaluar 31-100.
"""
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from math import comb
from pathlib import Path
import argparse
import hashlib
import json
import os
import time
import numpy as np
import pandas as pd
import yaml
from ..contract import _integer
from ..metrics import METRIC_NAMES, result_row, write_results
from ..simulation import _engine_hash, simulate
from .nsga2_pilot import SEARCH_REPLICATIONS, _evaluate

METHOD = 'NSGA2'
HOLDOUT_REPLICATIONS = range(SEARCH_REPLICATIONS + 1, 101)
PARAMETERS_FILE = 'config/project2/strategies/nsga2.yaml'
OUTPUT_DIRECTORY = 'results/project2/nsga2'
MAX_OFFSPRING_ATTEMPTS = 20


@dataclass(frozen=True)
class NSGA2Parameters:
    objectives: tuple
    population: int
    generations: int
    crossover_rate: float
    mutation_rate: float
    search_replications: int
    optimizer_seed: int

    def __post_init__(self):
        if len(self.objectives) < 2 or len(set(self.objectives)) != len(self.objectives):
            raise ValueError('Se requieren al menos dos objetivos distintos')
        if not set(self.objectives) <= set(METRIC_NAMES):
            raise ValueError('Objetivo fuera del contrato de metricas')
        _integer(self.population, 'population', 2)
        _integer(self.generations, 'generations', 1)
        _integer(self.optimizer_seed, 'optimizer_seed')
        if not 1 <= _integer(self.search_replications, 'search_replications', 1) <= SEARCH_REPLICATIONS:
            raise ValueError('La busqueda no puede usar replicas reservadas (31-100)')
        if not (0 <= self.crossover_rate <= 1 and 0 <= self.mutation_rate <= 1):
            raise ValueError('Las tasas deben estar en [0, 1]')

    @property
    def parameters_hash(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def load_parameters(path):
    raw = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    return NSGA2Parameters(**{**raw, 'objectives': tuple(raw['objectives'])})


def objective_directions(config, objectives):
    """direcciones del contrato comun; rechaza metricas que solo se reportan."""
    contract = pd.read_csv(config.root / 'data/project2/processed/simulation_metrics_contract.csv')
    directions = contract.set_index('metric').direction.to_dict()
    if any(directions[o] not in ('maximize', 'minimize') for o in objectives):
        raise ValueError('Una metrica report_only no puede ser objetivo')
    return {o: directions[o] for o in objectives}


def repair(sites, catalog, K, rng):
    """quita duplicados e ids ajenos y completa al azar; termina por construccion."""
    valid = set(catalog)
    kept = sorted({s for s in sites if s in valid})
    if len(kept) > K:
        kept = sorted(rng.choice(kept, size=K, replace=False).tolist())
    free = sorted(valid - set(kept))
    if K - len(kept) > len(free):
        raise ValueError('K supera el numero de candidatos')
    return tuple(sorted(kept + rng.choice(free, size=K - len(kept), replace=False).tolist()))


def crossover(first, second, K, rng):
    """conserva los sitios comunes y completa con los no comunes de ambos padres."""
    common = set(first) & set(second)
    others = sorted(set(first) ^ set(second))
    return tuple(sorted(common | set(rng.choice(others, size=K - len(common), replace=False).tolist())))


def mutate(sites, catalog, rate, rng):
    """cada sitio se cambia con probabilidad rate por uno que no este en la instalacion."""
    current = list(sites)
    for i in range(len(current)):
        if rng.random() < rate:
            free = sorted(set(catalog) - set(current))
            if free:
                current[i] = str(rng.choice(free))
    return tuple(sorted(current))


def initial_population(catalog, K, size, rng):
    if size > comb(len(catalog), K):
        raise ValueError('La poblacion supera las instalaciones posibles')
    population = set()
    while len(population) < size:
        population.add(repair((), catalog, K, rng))
    return sorted(population)


def aggregate(rows, directions):
    """media por replica en sentido minimizar; vacios cuentan como violacion, nunca como cero."""
    values = np.array([[row[o] for o in directions] for row in rows], dtype=float)
    violation = int(np.isnan(values).sum())
    signs = np.array([1. if d == 'minimize' else -1. for d in directions.values()])
    means = np.full(len(directions), np.inf)
    defined = ~np.isnan(values).all(0)
    means[defined] = np.nanmean(values[:, defined], axis=0) * signs[defined]
    return means, violation


def dominance_matrix(x, violation):
    """[i, j] true si i domina a j; una solucion factible domina a toda infactible."""
    v = np.asarray(violation)
    pareto = (x[:, None, :] <= x[None, :, :]).all(2) & (x[:, None, :] < x[None, :, :]).any(2)
    return (v[:, None] < v[None, :]) | ((v[:, None] == 0) & (v[None, :] == 0) & pareto)


def nondominated_fronts(x, violation):
    dominated_by = dominance_matrix(x, violation)
    remaining = np.ones(len(x), dtype=bool)
    fronts = []
    while remaining.any():
        current = remaining & ~dominated_by[remaining].any(0)
        fronts.append(np.flatnonzero(current))
        remaining &= ~current
    return fronts


def crowding_distance(x):
    """distancia de hacinamiento normalizada; los extremos de cada objetivo son infinitos."""
    n, m = x.shape
    distance = np.zeros(n)
    finite = np.isfinite(x).all(1)
    if n <= 2:
        return np.full(n, np.inf)
    for k in range(m):
        order = np.argsort(x[:, k], kind='stable')
        order = order[finite[order]]
        if len(order) < 2:
            continue
        distance[order[[0, -1]]] = np.inf
        span = x[order[-1], k] - x[order[0], k]
        if span > 0:
            distance[order[1:-1]] += (x[order[2:], k] - x[order[:-2], k]) / span
    return distance


def rank_population(x, violation):
    rank, crowding = np.zeros(len(x), dtype=int), np.zeros(len(x))
    for level, front in enumerate(nondominated_fronts(x, violation)):
        rank[front] = level
        crowding[front] = crowding_distance(x[front])
    return rank, crowding


def tournament(rank, crowding, rng):
    a, b = (int(i) for i in rng.integers(0, len(rank), size=2))
    if rank[a] != rank[b]:
        return a if rank[a] < rank[b] else b
    return a if crowding[a] >= crowding[b] else b


def make_offspring(population, rank, crowding, catalog, K, params, rng):
    """hasta una poblacion de hijos nuevos; no reevalua padres ni repite hijos."""
    seen, children = set(population), []
    for _ in range(MAX_OFFSPRING_ATTEMPTS * len(population)):
        if len(children) == len(population):
            break
        first = population[tournament(rank, crowding, rng)]
        second = population[tournament(rank, crowding, rng)]
        child = crossover(first, second, K, rng) if rng.random() < params.crossover_rate else first
        child = repair(mutate(child, catalog, params.mutation_rate, rng), catalog, K, rng)
        if child not in seen:
            seen.add(child)
            children.append(child)
    return children


def select_survivors(installations, x, violation, size):
    """elitista: frentes completos y, en el ultimo, los menos hacinados."""
    survivors = []
    for front in nondominated_fronts(x, violation):
        if len(survivors) + len(front) <= size:
            survivors.extend(front.tolist())
            continue
        crowding = crowding_distance(x[front])
        survivors.extend(front[np.argsort(-crowding, kind='stable')][:size - len(survivors)].tolist())
        break
    return sorted(installations[i] for i in survivors)


def update_archive(archive, installations, x, violation):
    """no dominados de todo lo evaluado: la poblacion puede perderlos si el frente la supera."""
    merged = {**archive, **{i: (x[n], violation[n]) for n, i in enumerate(installations)}}
    names = sorted(merged)
    front = nondominated_fronts(np.array([merged[i][0] for i in names]), [merged[i][1] for i in names])[0]
    return {names[n]: merged[names[n]] for n in front}


class SimulationEvaluator:
    """corre simulate una vez por instalacion y seed, con cache persistente.

    la clave incluye config_hash y engine_hash para no mezclar experimentos.
    """

    def __init__(self, config, replications, workers=None, path=None):
        self.config, self.path, self.simulations = config, Path(path) if path else None, 0
        self.workers = workers or max(1, (os.cpu_count() or 2) - 2)
        bank = pd.read_csv(config.root / config['seed_bank_file']).head(replications)
        self.seeds = [(int(s.replication_id), int(s.seed)) for s in bank.itertuples()]
        self.engine_hash, self.cache, self.pool = _engine_hash(), {}, None
        if self.path and self.path.exists():
            self._load()

    def _key(self, installation):
        return self.config.config_hash, self.engine_hash, tuple(installation)

    def _load(self):
        lines = self.path.read_text(encoding='utf-8').splitlines()
        for number, line in enumerate(lines, 1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                if number == len(lines):  # corte durante la ultima escritura
                    break
                raise
            key = item['config_hash'], item['engine_hash'], tuple(item['site_ids'])
            self.cache[key] = {int(k): v for k, v in item['rows'].items()}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.pool:
            self.pool.shutdown()

    def __call__(self, installations):
        missing = [i for i in installations if self._key(i) not in self.cache]
        if missing:
            self._simulate(missing)
        return {i: [self.cache[self._key(i)][seed] for _, seed in self.seeds] for i in installations}

    def _simulate(self, installations):
        self.pool = self.pool or ProcessPoolExecutor(max_workers=self.workers)
        tasks = [(None, list(i), replication, seed, self.config)
                 for i in installations for replication, seed in self.seeds]
        rows = iter(self.pool.map(_evaluate, tasks, chunksize=5))
        lines = []
        for installation in installations:
            stored = {}
            for _, seed in self.seeds:
                row = next(rows)
                stored[seed] = {m: row[m] for m in METRIC_NAMES}
            self.cache[self._key(installation)] = stored
            lines.append(json.dumps({'config_hash': self.config.config_hash, 'engine_hash': self.engine_hash,
                                     'site_ids': list(installation), 'rows': stored}, separators=(',', ':')))
        self.simulations += len(tasks)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open('a', encoding='utf-8') as file:
                file.write('\n'.join(lines) + '\n')


def _score(installations, evaluate, directions):
    rows = evaluate(installations)
    scored = [aggregate(rows[i], directions) for i in installations]
    return np.array([s[0] for s in scored]), [s[1] for s in scored]


def _history_row(generation, x, violation, archive, directions, new_simulations, elapsed):
    signs = np.array([1. if d == 'minimize' else -1. for d in directions.values()])
    natural = x * signs
    row = {'generation': generation, 'front_size': len(nondominated_fronts(x, violation)[0]), 'archive_size': len(archive),
           'infeasible': int(np.count_nonzero(violation)), 'new_simulations': new_simulations, 'elapsed_s': elapsed}
    for k, (objective, direction) in enumerate(directions.items()):
        row[f'best_{objective}'] = float(x[:, k].min() * signs[k])
        row[f'mean_{objective}'] = float(natural[np.isfinite(natural[:, k]), k].mean())
    return row


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding='utf-8')
    temp.replace(path)


def _read_checkpoint(path, identity):
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding='utf-8'))
    if state['identity'] != identity:
        raise ValueError('El checkpoint es de otra configuracion, motor o parametros; use otra carpeta')
    return state


def run_nsga2(catalog, K, params, directions, evaluate, identity=None, output=None, stop_after=None):
    """bucle (mu + lambda). con output guarda el avance al cerrar cada generacion.

    evaluate recibe instalaciones y devuelve {instalacion: filas de metricas}.
    stop_after corta antes del final para pruebas; el resultado no queda congelado.
    """
    catalog = sorted(catalog)
    checkpoint = Path(output) / 'checkpoint.json' if output else None
    state = _read_checkpoint(checkpoint, identity) if output else None
    rng = np.random.Generator(np.random.PCG64(params.optimizer_seed))
    start = time.perf_counter()
    last = params.generations if stop_after is None else min(stop_after, params.generations)

    def simulations():
        return getattr(evaluate, 'simulations', 0)

    if state:
        rng.bit_generator.state = state['rng']
        population = [tuple(i) for i in state['population']]
        generation, history = state['generation'], state['history']
        x, violation = _score(population, evaluate, directions)
        stored = [tuple(i) for i in state['archive']]
        archive = update_archive({}, stored, *_score(stored, evaluate, directions))
    else:
        population = initial_population(catalog, K, params.population, rng)
        x, violation = _score(population, evaluate, directions)
        generation = 0
        archive = update_archive({}, population, x, violation)
        history = [_history_row(0, x, violation, archive, directions, simulations(), time.perf_counter() - start)]

    def save():
        if output:
            _write_json(checkpoint, {'identity': identity, 'generation': generation, 'history': history,
                                     'population': [list(i) for i in population], 'archive': [list(i) for i in archive],
                                     'rng': rng.bit_generator.state})

    save()
    while generation < last:
        before, begun = simulations(), time.perf_counter()
        rank, crowding = rank_population(x, violation)
        children = make_offspring(population, rank, crowding, catalog, K, params, rng)
        merged = population + children
        merged_x, merged_v = _score(merged, evaluate, directions)
        archive = update_archive(archive, merged, merged_x, merged_v)
        population = select_survivors(merged, merged_x, merged_v, params.population)
        x, violation = _score(population, evaluate, directions)
        generation += 1
        history.append(_history_row(generation, x, violation, archive, directions, simulations() - before,
                                    time.perf_counter() - begun))
        save()
    return {'population': population, 'objectives': x, 'violation': violation, 'generation': generation, 'archive': archive,
            'history': pd.DataFrame(history), 'finished': generation == params.generations}


def freeze_front(result, params, directions, identity, path):
    """guarda el frente final antes de mirar las replicas reservadas; no se sobrescribe."""
    path = Path(path)
    if path.exists():
        raise ValueError('Ya existe un frente congelado; no se reemplaza')
    if not result['finished']:
        raise ValueError('Solo se congela una busqueda terminada')
    signs = np.array([1. if d == 'minimize' else -1. for d in directions.values()])
    solutions = [{'solution_id': f'pareto_{n:03d}', 'site_ids': list(installation),
                  'search_means': dict(zip(directions, (result['archive'][installation][0] * signs).tolist()))}
                 for n, installation in enumerate(sorted(result['archive']), 1)]
    _write_json(path, {'identity': identity, 'optimizer_seed': params.optimizer_seed, 'solutions': solutions})
    return solutions


def _evaluate_holdout(task):
    solution_id, sites, replication_id, seed, config, optimizer_seed = task
    return result_row(METHOD, replication_id, simulate(sites, seed, config), config, solution_id, optimizer_seed)


def evaluate_frozen_front(front_path, config, output, replications=HOLDOUT_REPLICATIONS, workers=None):
    """evalua el frente congelado solo en replicas reservadas, con el esquema comun."""
    if min(replications) <= SEARCH_REPLICATIONS:
        raise ValueError('La evaluacion final no debe reutilizar replicas de busqueda')
    front = json.loads(Path(front_path).read_text(encoding='utf-8'))
    bank = pd.read_csv(config.root / config['seed_bank_file'])
    bank = bank[bank.replication_id.isin(replications)]
    tasks = [(s['solution_id'], s['site_ids'], int(b.replication_id), int(b.seed), config, front['optimizer_seed'])
             for s in front['solutions'] for b in bank.itertuples()]
    with ProcessPoolExecutor(max_workers=workers or max(1, (os.cpu_count() or 2) - 2)) as pool:
        rows = list(pool.map(_evaluate_holdout, tasks, chunksize=5))
    return write_results(rows, output)


def main():
    from ..config import load_config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['search', 'holdout'])
    parser.add_argument('--output', default=OUTPUT_DIRECTORY)
    parser.add_argument('--workers', type=int)
    parser.add_argument('--stop-after', type=int, help='corta en esa generacion; para pruebas de tiempo')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    config = load_config(root / 'config/project2/base.yaml')
    output = root / args.output
    if args.command == 'holdout':
        frame = evaluate_frozen_front(output / 'front.json', config, root / 'results/project2/nsga2_results.csv',
                                      workers=args.workers)
        print(f'{len(frame)} filas de replicas reservadas')
        return
    params = load_parameters(root / PARAMETERS_FILE)
    directions = objective_directions(config, params.objectives)
    catalog = pd.read_csv(root / 'data/project2/processed/candidate_hive_sites.csv').site_id.tolist()
    identity = {'config_hash': config.config_hash, 'engine_hash': _engine_hash(), 'parameters_hash': params.parameters_hash}
    with SimulationEvaluator(config, params.search_replications, args.workers, output / 'evaluations.jsonl') as evaluate:
        result = run_nsga2(catalog, config['K'], params, directions, evaluate, identity, output, args.stop_after)
        result['history'].to_csv(output / 'history.csv', index=False, lineterminator='\n')
        if result['finished']:
            solutions = freeze_front(result, params, directions, identity, output / 'front.json')
            print(f'Frente congelado: {len(solutions)} soluciones')
    print(f'Generacion {result["generation"]}; simulaciones nuevas: {evaluate.simulations}')


if __name__ == '__main__':
    main()
