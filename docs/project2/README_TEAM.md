# Guía general para integrantes — Proyecto 2

## Problema y estado actual

Buscamos comparar ubicaciones de K colmenas en Oslo con la misma geografía, horizonte, reglas, métricas y azar de evaluación. Existe un motor **sintético agregado** operativo, no una calibración ecológica. Las áreas GIS y las fechas proceden de fuentes documentadas; fichas de recurso, intensidad de viajes y sensibilidad son provisionales. No comparar todavía qué algoritmo es "mejor en Oslo".

## Datos y entidades

- Dryad aporta flores y visitas en una ventana corta, no recursos absolutos por parque ni coordenadas de traps.
- `FloralPatch`: uno de 737 espacios verdes como recurso potencial, incluso donde no se permite colmena bajo el filtro disponible.
- `CandidateHiveSite`: uno de 375 puntos interiores de parques completos que no intersectan zonas libres de abejas; no equivale a una autorización adicional.
- `Hive`: colonia agregada en un sitio candidato, con índice canónico `hive_slot`. Exactamente K sitios distintos por ejecución.
- El horizonte principal es diario, 18/07–04/08/2017. Los resúmenes mensuales no se copian como recursos diarios.
- Recursos exclusivos: prioridad lexicográfica por `patch_id`. Cada porción pertenece al primer ID que la cubre; 680 geometrías conservan área positiva y 57 IDs quedan con área cero asignada. Esto no implica ausencia observada de flores. Se conserva el catálogo completo de 737 IDs.

## Qué hace simulate

```python
import sys
sys.path.insert(0, "src")  # si no se ha instalado el paquete; ejecutar desde la raíz
import pandas as pd
from bee_sim.project2 import load_config, simulate

cfg = load_config("config/project2/base.yaml")
seed = int(pd.read_csv(cfg.root / cfg["seed_bank_file"]).seed.iloc[0])
# site_ids debe venir del selector, nunca de un cambio al motor.
# result = simulate(site_ids, seed, cfg)
```

Valida sitios/configuración, carga calendario/distancias, inicializa fichas según área exclusiva, procesa oportunidades y eventos de todas las colonias en un reloj común, registra consumo y retorno, regenera al cierre y calcula las nueve métricas únicas. Devuelve `metrics`, `per_hive`, `trips`, `resource_log`, `events` y `provenance`. Configuración y estado se copian; no se arrastra una corrida a la siguiente.

El modelo mínimo usa oportunidades Poisson por colonia/día, tiempos uniformes condicionales, búsqueda y demanda exponenciales, velocidad constante y retorno si cabe en la jornada. No modela un número finito de obreras, muerte de colonia, néctar/polen físico ni polinización. El consumo se reserva al comenzar forrajeo; las ocupaciones son intervalos [inicio, fin). Los eventos de cierre preceden inicios/departuras en empates. No usa información de eventos futuros para elegir parche.

## Parametrización y solapamientos

`config/project2/base.yaml` documenta cada valor con `status`, `provisional` y `source`. K=5, radio=3000 m, alpha=1, beta=2, escala=1000 m, 1000 synthetic_RU, regeneración=0.1 del stock inicial/día y 12 oportunidades/día son valores de prueba. No son mediciones. La jornada de 600 min y velocidad de 5.5 m/s son supuestos heredados/convertidos de Proyecto 1. Los otros tiempos y demanda también requieren sensibilidad.

`initial_resource_rule=exclusive_area_share` reparte un total sintético por área exclusiva; no estima flores por m². La regeneración agrega `regeneration_rate * R_initial` al cierre, sin techo de capacidad: si no se consume puede acumularse; esto es una simplificación explícita de prueba. La política de prioridad elimina doble conteo de área, pero la asignación arbitraria por ID no expresa calidad ecológica, puede fragmentar un parque y debe someterse a sensibilidad. Se preserva la unión territorial y los originales. Puntos de destino/distancias se recalculan para los trozos exclusivos; la matriz anterior de 04 permanece intacta para auditoría.

`mode=calibrated` se rechaza: no hay evidencia para habilitar ese modo. Para sensibilidad se usa `with_parameters(cfg, ...)`; cambia el `config_hash` y todos deben reevaluarse con el mismo nuevo perfil. No cambiar reglas o familias por algoritmo.

## Semillas y resultados comparables

Banco compartido: `experiment_seeds.csv`, con 100 réplicas. El RNG del selector/optimizador es independiente y se registra como `optimizer_seed`. El motor usa PCG64 por oportunidad/proceso; las oportunidades se numeran antes de decisiones para mantener el acoplamiento CRN. Una misma seed no obliga a que los resultados de sitios diferentes sean iguales.

Para pruebas de estrategia usar al menos 30 réplicas comunes y, si es viable, las 100 para evaluación final. Si NSGA-II ajusta soluciones con réplicas 1–30, congelar soluciones y reportar también 31–100 como evaluación no usada por el optimizador; el agregado de 100 es evaluación interna en ese diseño, no 100 observaciones independientes de entrenamiento. El mismo subconjunto debe usarse para todos al comparar.

El escritor común `bee_sim.project2.metrics.result_row` y `write_results` conserva métricas y trazabilidad. Consultar `RESULTS_SCHEMA.md`; no redondear métricas antes de guardar. Identificar varias soluciones con `solution_id` y no juntar parámetros/motores distintos en una tabla de comparación como si fueran un experimento único.

## Métricas comunes

Recurso total entregado, media y mínimo por colmena; distancia de ida media, total y P95; presión de competencia; Jain de equilibrio; parches con consumo positivo. Incluyen las K colonias aunque algunas entreguen cero. Distancia total es suma de idas, no trayectoria real ida/vuelta. Valores sin denominador quedan vacíos, no cero inventado. La definición exacta y dirección están congeladas en `simulation_metrics_contract.csv`; parches usados es diagnóstico.

## Qué puede empezar cada integrante

RANDOM desarrolla un selector aleatorio de K candidatos; GREEDY una regla ex ante explicable; NSGA-II una búsqueda multiobjetivo que llama a simulate. Todavía no existen esos selectores. Ver sus guías para branches, pruebas y archivos propios. No desarrollar motores particulares.

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
git switch -c feature/tu-estrategia
git status
```

Sustituir `feature/tu-estrategia` por la branch sugerida en esta guía. Estos son comandos para el integrante; esta entrega se desarrolló únicamente en `proyecto2-urban-optimization`.

Crear el selector y sus tests en archivos propios. Agregar solo esos archivos y resultados revisados con `git add <archivos-propios>`; luego `git commit -m "Describe la estrategia y sus pruebas"` y `git push -u origin HEAD`. No usar `git add .` sin revisar los cambios. Integrar por revisión/PR; no sobrescribir módulos compartidos desde una branch de estrategia.
