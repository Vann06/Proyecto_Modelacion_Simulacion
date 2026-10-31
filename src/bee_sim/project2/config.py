"""Configuración estricta y trazable del motor sintético común."""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from numbers import Real, Integral
import copy
import hashlib
import json
import math
import yaml

ENGINE_VERSION = 'project2-synthetic-1.1.0'
PARAMETERS = {'K', 'max_foraging_distance_m', 'alpha', 'beta', 'distance_scale_m',
              'resource_unit', 'initial_resource_rule', 'initial_resource_total', 'regeneration_rate',
              'departures_per_day', 'day_minutes', 'flight_speed_m_s', 'search_time_mean_min',
              'demand_mean_ru', 'foraging_rate_ru_per_min', 'return_model', 'simulation_start',
              'simulation_end', 'replications', 'seed_bank_file'}
STATUSES = {'observed', 'derived', 'inherited_from_project1', 'scenario_parameter', 'pending_calibration'}


@dataclass(frozen=True)
class Config:
    root: Path
    mode: str
    scenario: str
    _records_json: str

    @property
    def records(self):
        return json.loads(self._records_json)

    @property
    def parameters(self):
        return MappingProxyType({k: v['value'] for k, v in self.records.items()})

    def __getitem__(self, key):
        return self.parameters[key]

    @property
    def config_hash(self):
        payload = {'engine_version': ENGINE_VERSION, 'mode': self.mode,
                   'scenario': self.scenario, 'parameters': self.records}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _validated(root, mode, scenario, records):
    root = Path(root).resolve()
    if mode != 'synthetic':
        raise ValueError('Solo está habilitado mode=synthetic; aún no hay calibración ecológica.')
    if not isinstance(scenario, str) or not scenario.strip():
        raise ValueError('scenario debe identificar el perfil sintético')
    if set(records) != PARAMETERS:
        raise ValueError(f'Parámetros faltantes/ajenos: {sorted(PARAMETERS - set(records))} / {sorted(set(records) - PARAMETERS)}')
    for name, record in records.items():
        if not isinstance(record, dict) or set(record) != {'value', 'status', 'provisional', 'source'}:
            raise ValueError(f'{name} requiere value, status, provisional y source')
        if record['status'] not in STATUSES or not isinstance(record['provisional'], bool) or not record['source']:
            raise ValueError(f'Procedencia inválida de {name}')
    p = {k: v['value'] for k, v in records.items()}
    for key in ['K', 'replications']:
        if isinstance(p[key], bool) or not isinstance(p[key], Integral) or p[key] < 1:
            raise ValueError(f'{key} debe ser entero positivo')
    positive = ['distance_scale_m', 'day_minutes', 'flight_speed_m_s', 'search_time_mean_min',
                'demand_mean_ru', 'foraging_rate_ru_per_min']
    nonnegative = ['max_foraging_distance_m', 'alpha', 'beta', 'initial_resource_total',
                   'regeneration_rate', 'departures_per_day']
    for key in positive + nonnegative:
        x = p[key]
        if isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x) or x < 0 or (key in positive and x == 0):
            raise ValueError(f'{key}: valor finito {"positivo" if key in positive else "no negativo"} requerido')
    fixed = {'resource_unit': 'synthetic_RU', 'initial_resource_rule': 'exclusive_area_share',
             'return_model': 'within_day_only', 'simulation_start': '2017-07-18',
             'simulation_end': '2017-08-04', 'seed_bank_file': 'data/project2/processed/experiment_seeds.csv'}
    if any(p[key] != value for key, value in fixed.items()):
        raise ValueError('Regla, horizonte, unidad sintética o banco ajeno al contrato común')
    return Config(root, mode, scenario, json.dumps(records, sort_keys=True, ensure_ascii=False))


def load_config(path='config/project2/base.yaml', root=None):
    path = Path(path).resolve()
    if root is None:
        root = next((p for p in path.parents if (p / 'src/bee_sim').is_dir()), None)
    if root is None:
        raise ValueError('No se encontró la raíz del repositorio')
    raw = yaml.safe_load(path.read_text(encoding='utf-8-sig'))
    if not isinstance(raw, dict) or set(raw) != {'mode', 'scenario', 'parameters'}:
        raise ValueError('Solo se admiten mode, scenario y parameters; no callbacks o reglas de estrategia')
    return _validated(root, raw['mode'], raw['scenario'], raw['parameters'])


def with_parameters(config, **values):
    """Overrides explícitos de escenario, con cambio de hash; nunca reglas del motor."""
    if set(values) - PARAMETERS:
        raise ValueError('Override no permitido: ' + ', '.join(sorted(set(values) - PARAMETERS)))
    records = copy.deepcopy(config.records)
    for key, value in values.items():
        records[key] = {'value': value, 'status': 'scenario_parameter', 'provisional': True,
                        'source': 'Override explícito para prueba/sensibilidad, no observación'}
    return _validated(config.root, config.mode, config.scenario, records)


def validate_config(config):
    if not isinstance(config, Config):
        raise TypeError('Use load_config y with_parameters; no se aceptan dicts/callbacks arbitrarios')
    return _validated(config.root, config.mode, config.scenario, config.records)
