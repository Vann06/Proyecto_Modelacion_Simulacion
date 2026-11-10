"""baseline random: k sitios al azar usando solo el catalogo de candidatos.

no mira recursos, distancias ni viajes; la evaluacion si usa el motor comun.
"""
import numpy as np
import pandas as pd
from ..contract import _integer, validate_hive_sites
from ..metrics import result_row
from ..simulation import simulate

METHOD = 'RANDOM'


def select_sites(candidates, K, optimizer_seed):
    """elige K site_id sin reemplazo; misma seed, misma instalacion."""
    # se ordena antes de sortear para que el orden del csv no cambie nada
    ids = sorted(candidates['site_id'])
    K = _integer(K, 'K', 1)
    if K > len(ids):
        raise ValueError('K supera el numero de candidatos')
    rng = np.random.Generator(np.random.PCG64(_integer(optimizer_seed, 'optimizer_seed')))
    picked = rng.choice(len(ids), size=K, replace=False)
    return validate_hive_sites([ids[i] for i in picked], ids, K)


def generate_installations(candidates, K, n, base_seed):
    """n instalaciones independientes; la i-esima usa base_seed + i."""
    n = _integer(n, 'n', 1)
    base_seed = _integer(base_seed, 'base_seed')
    return {f'random_{i + 1:03d}': {'optimizer_seed': base_seed + i,
                                    'site_ids': list(select_sites(candidates, K, base_seed + i))}
            for i in range(n)}


def evaluate_installation(solution_id, installation, config, replications):
    """corre una instalacion sobre las primeras R seeds del banco comun.

    devuelve las filas del esquema comun y el primer resultado (para logs).
    """
    bank = pd.read_csv(config.root / config['seed_bank_file'])
    replications = _integer(replications, 'replications', 1)
    if replications > min(config['replications'], len(bank)):
        raise ValueError('Número de réplicas fuera de configuración/banco')
    rows, first = [], None
    for item in bank.head(replications).itertuples(index=False):
        result = simulate(installation['site_ids'], int(item.seed), config)
        rows.append(result_row(METHOD, int(item.replication_id), result, config,
                               solution_id, installation['optimizer_seed']))
        if first is None:
            first = result
    return rows, first
