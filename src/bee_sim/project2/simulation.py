"""Motor agregado SINTÉTICO; una implementación común, sin estrategias de ubicación."""
from pathlib import Path
import hashlib
import heapq
import json
import numpy as np
import pandas as pd
from .config import Config, ENGINE_VERSION, load_config, validate_config
from .contract import validate_hive_sites, event_rng, resource_step
from .distance import load_landscape, digest
from .entities import Hive, FloralPatch
from .metrics import summarize, validate_metrics_contract

TRIP_COLUMNS = ['date', 'hive_slot', 'site_id', 'trip_slot', 'patch_id', 'departure_min',
                'arrival_min', 'foraging_start_min', 'foraging_end_min', 'return_min',
                'one_way_distance_m', 'competition_at_selection', 'other_colonies_active_at_foraging_start',
                'foraging_attempt', 'resource_consumed', 'resource_delivered', 'returned']


def _engine_hash():
    files = sorted(Path(__file__).parent.glob('*.py'))
    payload = '\n'.join(p.name + '\0' + p.read_text(encoding='utf-8').replace('\r\n', '\n') for p in files)
    return hashlib.sha256(payload.encode()).hexdigest()


def simulate(hive_sites, seed, config):
    """Evalúa ubicaciones dadas. No selecciona K sitios ni implementa optimizadores.

    Reservas/consumo al iniciar forrajeo, ocupación en [inicio,fin), regeneración
    al cierre. Oportunidades Poisson agregadas, sin población finita de abejas.
    """
    cfg = validate_config(config if isinstance(config, Config) else load_config(config))
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0 or seed >= 2**32:
        raise ValueError('seed debe ser uint32')
    seed = int(seed)
    parameters = cfg.parameters  # Materializar una vez; evita miles de json.loads por corrida.
    metric_hash = validate_metrics_contract(cfg.root)
    candidates, patches, all_distances, manifest = load_landscape(cfg)
    sites = validate_hive_sites(hive_sites, candidates.site_id, parameters['K'])
    calendar_path = cfg.root / 'data/project2/processed/simulation_calendar.csv'
    calendar = pd.read_csv(calendar_path, parse_dates=['date'])
    dates = pd.date_range(parameters['simulation_start'], parameters['simulation_end'], freq='D')
    if (calendar.date.tolist() != dates.tolist() or calendar.date.duplicated().any() or
            not calendar.primary_resolution.eq('daily').all() or not calendar.inside_calibrated_window.all() or
            calendar.simulation_day.tolist() != list(range(1, len(dates) + 1))):
        raise ValueError('Calendario ajeno al horizonte común')
    bank_path = cfg.root / parameters['seed_bank_file']
    bank = pd.read_csv(bank_path)
    if (not bank.seed.is_unique or not bank.replication_id.is_unique or
            bank.replication_id.tolist() != list(range(1, len(bank) + 1)) or
            parameters['replications'] > len(bank) or seed not in set(bank.seed)):
        raise ValueError('Seed o número de réplicas fuera del banco común')
    hives = [Hive(i, site_id) for i, site_id in enumerate(sites)]
    # Las tres entidades tienen papeles distintos; no se eliminan parches por no admitir colmena.
    floral_patches = [FloralPatch(r.patch_id, r.exclusive_area_m2) for r in patches.itertuples()]
    row_indices = {site_id: i for i, site_id in enumerate(candidates.site_id)}
    distances = all_distances[[row_indices[s] for s in sites]]
    areas = patches.exclusive_area_m2.to_numpy(float)
    if areas.sum() <= 0:
        raise ValueError('No existe superficie exclusiva de recurso')
    initial = parameters['initial_resource_total'] * (areas / areas.sum())
    stock = initial.copy()
    delivered = np.zeros(len(hives))
    trips, events, resource_rows = [], [], []
    end_of_day = parameters['day_minutes']
    speed_m_min = parameters['flight_speed_m_s'] * 60
    priorities = {'return': 0, 'foraging_end': 1, 'foraging_start': 2, 'arrival': 3, 'departure': 4}

    for day, date in enumerate(dates):
        day_start_stock = stock.copy()
        active = np.zeros((len(floral_patches), len(hives)), dtype=np.int64)
        heap, daily_trips = [], {}

        def schedule(time, kind, hive_slot, trip_slot):
            if time <= end_of_day:
                heapq.heappush(heap, (float(time), priorities[kind], hive_slot, trip_slot, kind))

        def log(time, kind, hive_slot, trip_slot, patch=None, amount=0.):
            events.append({'date': date.strftime('%Y-%m-%d'), 'time_min': float(time), 'event': kind,
                           'hive_slot': hive_slot, 'trip_slot': trip_slot,
                           'patch_id': None if patch is None else floral_patches[patch].patch_id,
                           'amount_ru': float(amount)})

        for hive in hives:
            rng = event_rng(seed, day, hive.hive_slot, 0, 'departures')
            n = int(rng.poisson(parameters['departures_per_day']))
            times = np.sort(rng.uniform(0, end_of_day, size=n))
            for trip_slot, time in enumerate(times):
                schedule(time, 'departure', hive.hive_slot, trip_slot)
        while heap:
            time, _, i, slot, kind = heapq.heappop(heap)
            key = (i, slot)
            if kind == 'departure':
                competition = (active > 0).sum(axis=1) - (active[:, i] > 0)
                eligible = (stock > 0) & (distances[i] <= parameters['max_foraging_distance_m'])
                columns = np.flatnonzero(eligible)
                if not len(columns):
                    log(time, 'no_available_patch', i, slot)
                    continue
                log_scores = (np.log(stock[columns]) - parameters['beta'] * np.log1p(distances[i, columns] / parameters['distance_scale_m'])
                              - np.log1p(parameters['alpha'] * competition[columns]))
                if not np.isfinite(log_scores).all():
                    raise ValueError('Score no finito; revisar parámetros')
                scores = np.exp(log_scores - log_scores.max())
                probabilities = scores / scores.sum()
                j = int(event_rng(seed, day, i, slot, 'patch_selection').choice(columns, p=probabilities))
                flight = float(distances[i, j] / speed_m_min)
                row = dict(zip(TRIP_COLUMNS, [None] * len(TRIP_COLUMNS)))
                row.update(date=date.strftime('%Y-%m-%d'), hive_slot=i, site_id=sites[i], trip_slot=slot,
                           patch_id=floral_patches[j].patch_id, departure_min=time, arrival_min=time + flight,
                           one_way_distance_m=float(distances[i, j]), competition_at_selection=int(competition[j]),
                           other_colonies_active_at_foraging_start=0, foraging_attempt=False,
                           resource_consumed=0., resource_delivered=0., returned=False)
                daily_trips[key] = (row, j, flight)
                trips.append(row)
                log(time, 'departure', i, slot, j)
                schedule(time + flight, 'arrival', i, slot)
            else:
                row, j, flight = daily_trips[key]
                if kind == 'arrival':
                    log(time, 'arrival', i, slot, j)
                    search = float(event_rng(seed, day, i, slot, 'search').exponential(parameters['search_time_mean_min']))
                    schedule(time + search, 'foraging_start', i, slot)
                elif kind == 'foraging_start':
                    row['foraging_start_min'] = time
                    row['foraging_attempt'] = True
                    others = np.count_nonzero(active[j]) - int(active[j, i] > 0)
                    row['other_colonies_active_at_foraging_start'] = int(others)
                    demand = float(event_rng(seed, day, i, slot, 'nectar').exponential(parameters['demand_mean_ru']))
                    amount = min(float(stock[j]), demand, max(0., end_of_day - time) * parameters['foraging_rate_ru_per_min'])
                    stock[j] -= amount
                    row['resource_consumed'] = amount
                    duration = amount / parameters['foraging_rate_ru_per_min']
                    finish = min(end_of_day, time + duration)
                    row['foraging_end_min'] = finish
                    row['return_min'] = finish + flight
                    if duration > 0:
                        active[j, i] += 1
                    log(time, 'foraging_start', i, slot, j, amount)
                    schedule(finish, 'foraging_end', i, slot)
                elif kind == 'foraging_end':
                    if row['resource_consumed'] > 0:
                        active[j, i] -= 1
                    log(time, 'foraging_end', i, slot, j)
                    schedule(time + flight, 'return', i, slot)
                elif kind == 'return':
                    row['returned'] = True
                    row['resource_delivered'] = row['resource_consumed']
                    delivered[i] += row['resource_delivered']
                    log(time, 'return', i, slot, j, row['resource_delivered'])
        if (stock < 0).any() or np.any(active != 0):
            raise AssertionError('Stock negativo u ocupación sin cerrar')
        consumed = day_start_stock - stock
        regeneration = parameters['regeneration_rate'] * initial
        stock = resource_step(day_start_stock, consumed, regeneration)
        for j, patch in enumerate(floral_patches):
            resource_rows.append({'date': date.strftime('%Y-%m-%d'), 'patch_id': patch.patch_id,
                                  'R_before': day_start_stock[j], 'consumption': consumed[j],
                                  'regeneration': regeneration[j], 'R_after': stock[j]})
    trip_frame = pd.DataFrame(trips, columns=TRIP_COLUMNS)
    per_hive = pd.DataFrame({'hive_slot': range(len(sites)), 'site_id': sites, 'resource_delivered': delivered})
    resource_log = pd.DataFrame(resource_rows)
    if not np.isclose(trip_frame.resource_consumed.sum(), resource_log.consumption.sum()):
        raise AssertionError('Consumos de viajes y balance no coinciden')
    summary = summarize(trip_frame, per_hive)
    provenance = {'mode': cfg.mode, 'scenario': cfg.scenario, 'resource_unit': parameters['resource_unit'],
                  'seed': seed, 'config_hash': cfg.config_hash, 'engine_version': ENGINE_VERSION,
                  'engine_hash': _engine_hash(), 'metric_contract_hash': metric_hash,
                  'input_hashes': {**manifest['source_hashes'], **manifest['asset_hashes'],
                                   'simulation_calendar.csv': digest(calendar_path), 'experiment_seeds.csv': digest(bank_path),
                                   'temporal_variable_metadata.csv': digest(cfg.root / 'data/project2/processed/temporal_variable_metadata.csv')},
                  'rng': 'PCG64_event_key_v1', 'overlap_policy': manifest['policy'],
                  'numpy_version': np.__version__, 'pandas_version': pd.__version__}
    provenance['input_hash'] = hashlib.sha256(json.dumps(provenance['input_hashes'], sort_keys=True).encode()).hexdigest()
    return {'metrics': summary, 'per_hive': per_hive, 'trips': trip_frame,
            'resource_log': resource_log, 'events': pd.DataFrame(events, columns=['date', 'time_min', 'event', 'hive_slot', 'trip_slot', 'patch_id', 'amount_ru']),
            'provenance': provenance}
