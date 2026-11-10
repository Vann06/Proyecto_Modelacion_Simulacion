# Integrante NSGA-II — optimización implementada

## Objetivo y representación

Estrategia multiobjetivo principal, branch `feature/NGSA-II`; implementada en `src/bee_sim/project2/strategies/nsga2.py`, con parámetros en `config/project2/strategies/nsga2.yaml`. Un individuo es una lista de K IDs válidos distintos. La representación/caché debe usar el orden canónico para no tratar permutaciones de una instalación como soluciones diferentes.

Objetivos definidos: maximizar `total_resource_obtained`, minimizar `mean_distance_m` y minimizar `competition_pressure`; las direcciones se leen del contrato de métricas. Siempre guardar las nueve métricas, no solo fitness. No cambiar sus fórmulas ni unidades.

## Qué debe documentarse

Codificación, tamaño de población, selección, ordenamiento no dominado y diversidad, crossover, mutación, reparación de duplicados/IDs inválidos, criterio de parada, presupuesto de evaluaciones, restricciones y objetivos. Guardar parámetros y seed del optimizador separadamente del motor. No añadir dependencias innecesarias sin discutirlas con el equipo.

La evaluación fitness llama a **simulate** con el mismo conjunto preacordado de seeds. Cachear por conjunto de IDs + config_hash + engine_hash + seed; una caché sin esas claves mezcla experimentos diferentes. No elegir mejores valores por seed individual ni omitir réplicas de bajo rendimiento.

Si se usan réplicas 1–30 para búsqueda, congelar el frente antes de evaluar 31–100. Reportar el subconjunto reservado por separado; un agregado de las 100 que incluye entrenamiento debe etiquetarse como evaluación interna. No afirmar validación independiente por repetir seeds usadas durante la búsqueda.

## Pruebas del optimizador

Individuos siempre válidos, exactamente K, sin duplicados; reparación terminante; mismo optimizer_seed reproduce la búsqueda bajo mismo presupuesto; pequeña enumeración exacta sobre un subconjunto de pocos sitios si es viable. Esa enumeración usa el motor común y sirve para revisar dominancia/repair, no para afirmar que se resolvió todo Oslo exactamente.

## Generar resultados

Ejecutar desde la raíz del repositorio. La prueba corta usa su propia carpeta; la búsqueda completa se retoma con el mismo comando si se interrumpe y congela el frente en `results/project2/nsga2/front.json`. `holdout` evalúa ese frente en las réplicas 31–100 y escribe `results/project2/nsga2_results.csv`; correrlo solo cuando la búsqueda haya terminado:

```powershell
$env:PYTHONPATH = 'src'
python -m bee_sim.project2.strategies.nsga2 search --stop-after 2 --output results/project2/nsga2_trial
python -m bee_sim.project2.strategies.nsga2 search
python -m bee_sim.project2.strategies.nsga2 holdout
python scripts/project2_run.py inspect --results results/project2/nsga2_results.csv
```

`front.json` no se sobrescribe: una búsqueda nueva necesita otra carpeta con `--output`. Las conclusiones de la corrida actual están en `results/project2/nsga2/conclusiones.md`. La caché `evaluations.jsonl` y `nsga2_trial/` no se versionan.

## Gráficos sugeridos

Frente de Pareto, convergencia/budget, mapa de una solución y comparación contra RANDOM/GREEDY con los mismos parámetros y seeds. Distinguir variabilidad entre réplicas de diversidad entre soluciones del frente y señalar el modo sintético.

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

## Archivos compartidos que no deben cambiarse por estrategia

- `data/project2/raw/`, notebooks 01–04 y 05–08: evidencia y análisis comunes.
- CSV/GeoJSON/NPZ de `data/project2/processed/`, especialmente candidatos, calendario, contrato de métricas, semillas y recursos exclusivos. Solo regenerar derivados con `prepare` cuando el equipo acuerde una nueva versión.
- `src/bee_sim/project2/{config,entities,distance,metrics,simulation,contract}.py`, `config/project2/base.yaml` y `data/project2/simulation_contract.md`: reglas compartidas. Cambiarlas requiere una revisión común y reevaluar todos los métodos; no esconder un cambio en el selector.
- Código y configuración de Proyecto 1.

Los parámetros exclusivos del optimizador (población, mutación, desempates, etc.) deben estar en archivos de estrategia separados. Ninguna estrategia pasa callbacks de métricas, reglas de consumo o distancias al motor.

## Trabajo en branch propia y commits

Después de recibir la versión común revisada del equipo, desde una copia limpia:

```powershell
git switch proyecto2-urban-optimization
git pull --ff-only
git switch -c feature/nsga2-optimization
git status
```

Sustituir `feature/nsga2-optimization` por la branch sugerida en esta guía. Estos son comandos para el integrante; esta entrega se desarrolló únicamente en `proyecto2-urban-optimization`.

Crear el selector y sus tests en archivos propios. Agregar solo esos archivos y resultados revisados con `git add <archivos-propios>`; luego `git commit -m "Describe la estrategia y sus pruebas"` y `git push -u origin HEAD`. No usar `git add .` sin revisar los cambios. Integrar por revisión/PR; no sobrescribir módulos compartidos desde una branch de estrategia.
