# Formato común de resultados

Una fila = una solución evaluada bajo una configuración y una réplica. No es una fila por viaje ni un promedio ya agregado. CSV UTF-8, encabezado, punto decimal y campos vacíos para valores indefinidos; sin redondear antes de guardar.

## Columnas y claves

Obligatorias: `method`, `scenario`, `K`, `replication_id`, `seed`, `site_ids`, las nueve métricas del contrato, `config_hash` y `engine_version`.

El escritor agrega `engine_hash`, `input_hash`, `mode`, `resource_unit`, `solution_id`, `optimizer_seed`, `metric_contract_hash` y `rng`. Se guarda exactamente el orden de `bee_sim.project2.metrics.RESULT_COLUMNS`. `method` usa RANDOM, GREEDY, NSGA2; SMOKE_FIXED_SITES queda reservado a fixtures, no se mezcla en comparaciones de algoritmos.

`site_ids` es una cadena JSON con K IDs ordenados y sin duplicados; recuperarla con `json.loads`, no separando por comas. `replication_id` y `seed` deben coincidir con experiment_seeds.csv. `optimizer_seed` es independiente y puede estar vacío para una heurística determinista. `mode=synthetic` y `resource_unit=synthetic_RU` son obligatorios en esta versión.

Clave única dentro de un archivo: `(method, scenario, K, replication_id, seed, solution_id)`. El escritor rechaza mezclar config_hash, engine_hash, input_hash o metric_contract_hash distintos. Incluso con igual engine_version revisar esos hashes y los input_hashes detallados de procedencia: detectan cambios en código/datos. Los paths de máquina no forman parte de config_hash.

## Métricas

La fuente normativa es `data/project2/processed/simulation_metrics_contract.csv`, congelada por el motor. Recurso = entregado antes del cierre; incluye todas las colonias. Distancias = ida euclidiana por viaje iniciado, incluso si no retorna. Jain queda vacío si todas entregan cero. Sin viajes: total de distancia y parches usados son cero, medias/P95/presión son vacíos. No sustituir los vacíos por cero para hacer un algoritmo parecer mejor.

## Escritura desde una estrategia

```python
from bee_sim.project2.metrics import result_row, write_results
# result = simulate(site_ids, seed, cfg)
# rows.append(result_row("RANDOM", replication_id, result, cfg,
#                        solution_id="solution_001", optimizer_seed=optimizer_seed))
# write_results(rows, "results/project2/random_results.csv")
```

Las líneas comentadas son interfaz de integración, no un selector ya implementado. En scripts propios agregar `src` al path o usar el entry point común explicado en README_TEAM.md.

Outputs esperados por método: `results/project2/random_results.csv`, `greedy_results.csv`, `nsga2_results.csv`. Guardar además archivo de IDs, configuración del optimizador y logs/procedencia de al menos una réplica. El evaluador CLI exporta los logs de la primera réplica en `<nombre_csv>_example/`.

## Comparación posterior

Verificar primero compatibilidad de configuración, motor, datos, horizonte, K y subconjunto de seeds. Emparejar por réplica/seed; usar bootstrap sobre diferencias de réplicas, no sobre viajes dependientes. Registrar el diseño de entrenamiento/evaluación, sin llamar independientes a las seeds usadas para optimizar. No comparar unidades synthetic_RU con flores/m² Dryad o ml de Proyecto 1.

## Comandos comunes disponibles ahora

Ejecutar desde la raíz del repositorio con Python 3.10 o posterior:

```powershell
python -m pip install -r requirements.txt
python scripts/project2_run.py prepare
python -m unittest discover -s tests/project2 -v
python scripts/project2_run.py smoke --replications 2 --output results/project2/smoke_results.csv
python scripts/project2_run.py inspect --results results/project2/smoke_results.csv
```

`prepare` genera derivados sin tocar originales. `smoke` usa los primeros K IDs ordenados como fixture fijo: **no es RANDOM, GREEDY o NSGA-II**, no busca una buena solución y solo prueba el motor sintético. Al repetir se reemplaza explícitamente el CSV de salida indicado. Los logs de la primera réplica quedan en `results/project2/smoke_results_example/`: eventos, viajes, recursos, colonias y procedencia/configuración. No generar resultados "finales de Oslo" con estos parámetros de prueba.

Los tests no necesitan pytest; usan unittest y las dependencias del motor. Las escrituras atómicas requieren permisos sobre la carpeta de resultados/temporales de Windows. Cada integrante debe ejecutar las pruebas antes de proponer cambios.
