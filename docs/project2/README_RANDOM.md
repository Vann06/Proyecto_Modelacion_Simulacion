# Integrante RANDOM — baseline pendiente de implementar

## Objetivo y alcance

Crear un selector que elija exactamente K IDs distintos sin reemplazo, usando **solo `candidate_hive_sites.csv`** para decidir la instalación. No dar pesos manuales a favoritos ni filtrar usando futuros recursos o viajes. La evaluación sí usa el mismo motor y todos sus datos. Branch sugerida: `feature/random-baseline`.

Archivo sugerido: `src/bee_sim/project2/strategies/random_baseline.py`, función `select_sites(candidates, K, optimizer_seed)`. No se entrega implementación de esa función ahora.

## Requisitos y pruebas del selector

- K válido, sitios del catálogo, sin duplicados, salida canónica estable.
- Misma seed del selector produce la misma instalación; registrar `optimizer_seed` separadamente de la seed de evaluación.
- Evaluar frecuencias sobre muchas selecciones con seeds de selector distintas. Buscar distribución razonable sin exigir igualdad exacta ni hacer tests frágiles por un p-valor aislado. No favorecer sitios manualmente.
- Al menos 30 réplicas comunes para prueba y 100 finales si es viable; registrar variación de instalación y variación del motor por separado.
- Guardar JSON con la lista elegida. Para variar instalación por réplica se admite un diccionario JSON `replication_id -> lista`; documentar esa decisión y mantenerla al comparar.

## Generar resultados cuando exista el selector

Tras crear `results/project2/random_sites.json` con IDs válidos, este evaluador ya está disponible:

```powershell
python scripts/project2_run.py evaluate --sites-file results/project2/random_sites.json --method RANDOM --optimizer-seed 123 --replications 30 --output results/project2/random_results.csv
python scripts/project2_run.py inspect --results results/project2/random_results.csv
```

Para la campaña final usar `--replications 100` con la misma configuración compartida. El 123 es ejemplo de seed del selector, no parámetro ecológico. No etiquetar una salida smoke como RANDOM. Usar el formato de `RESULTS_SCHEMA.md` y guardar la configuración y los IDs; los logs de primera réplica se exportan automáticamente.

## Gráficos sugeridos

Histograma de recurso total, boxplot de distancia media, mapa de una instalación ejemplo y distribución de competencia. Señalar que los recursos son sintéticos; no convertir diferencias en conclusiones observadas sobre Oslo.

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
git switch -c feature/random-baseline
git status
```

Sustituir `feature/random-baseline` por la branch sugerida en esta guía. Estos son comandos para el integrante; esta entrega se desarrolló únicamente en `proyecto2-urban-optimization`.

Crear el selector y sus tests en archivos propios. Agregar solo esos archivos y resultados revisados con `git add <archivos-propios>`; luego `git commit -m "Describe la estrategia y sus pruebas"` y `git push -u origin HEAD`. No usar `git add .` sin revisar los cambios. Integrar por revisión/PR; no sobrescribir módulos compartidos desde una branch de estrategia.
