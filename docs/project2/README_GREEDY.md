# Integrante GREEDY — heurística pendiente de implementar

## Objetivo y alcance

Implementar una heurística simple e interpretable, branch `feature/greedy-baseline`. Archivo sugerido `src/bee_sim/project2/strategies/greedy_baseline.py`. Debe proponer K sitios y evaluarlos con simulate, sin reescribir el motor.

Información permitida: catálogo de candidatos, recurso inicial sintético declarado por la regla común, matriz de distancias derivada, cercanía a sitios ya elegidos y estimación ex ante de competencia. No leer resource_log, viajes o rendimientos futuros de la réplica para decidir el siguiente sitio.

## Diseño que debe documentarse

- Definir fórmula/score, unidades, ponderaciones y orden de desempate antes de la comparación.
- Explicar cómo se actualiza el score al agregar cada sitio, qué cobertura se vuelve compartida y cómo se evitan duplicados.
- Una penalización por proximidad o cobertura compartida es una estimación de diseño; no es competencia observada ni el estado futuro de ocupación del motor.
- Declarar complejidad: por ejemplo un recálculo ingenuo de coberturas de N candidatos y M parches en K pasos cuesta O(KNM), antes de posibles cachés; justificar la complejidad de la implementación real.
- Guardar parámetros de la heurística aparte del config común. Un cambio de alpha/beta del motor debe aplicarse a todos los métodos, no solo a GREEDY.

## Pruebas del selector

Exactamente K IDs válidos sin duplicados; terminación aunque algunos scores empaten o sean cero; mismo resultado si no usa azar y desempates estables; si incorpora azar, seed propia reproducible. Ningún acceso a información futura de la simulación.

## Generar resultados cuando exista el selector

Guardar la lista en `results/project2/greedy_sites.json` y ejecutar:

```powershell
python scripts/project2_run.py evaluate --sites-file results/project2/greedy_sites.json --method GREEDY --replications 30 --output results/project2/greedy_results.csv
python scripts/project2_run.py inspect --results results/project2/greedy_results.csv
```

La salida final esperada es `results/project2/greedy_results.csv`; usar 100 réplicas finales si es viable y el mismo banco/config que RANDOM y NSGA-II. Mantener la solución congelada durante su evaluación.

## Gráficos sugeridos

Scores de candidatos y pasos de construcción, mapa de selección, recurso/distancia y boxplots contra RANDOM usando seeds emparejadas y configuración idéntica. Etiquetar todas las conclusiones del recurso como sintéticas.

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
git switch -c feature/greedy-baseline
git status
```

Sustituir `feature/greedy-baseline` por la branch sugerida en esta guía. Estos son comandos para el integrante; esta entrega se desarrolló únicamente en `proyecto2-urban-optimization`.

Crear el selector y sus tests en archivos propios. Agregar solo esos archivos y resultados revisados con `git add <archivos-propios>`; luego `git commit -m "Describe la estrategia y sus pruebas"` y `git push -u origin HEAD`. No usar `git add .` sin revisar los cambios. Integrar por revisión/PR; no sobrescribir módulos compartidos desde una branch de estrategia.
