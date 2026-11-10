# Modalidad rápida NSGA-II — cierre de implementación

Rama local: `feature/project2-entrega-final`. Sin commit, push, PR ni merge.
Se conservaron los cambios anteriores del frontend. No se agregaron dependencias
de producción ni se modificó `src/bee_sim/project2/`.

## Comportamiento

Dentro de **Configura una pregunta**, en Movimiento y Sensibilidad, NSGA-II permite
elegir frente histórico K=5 o una búsqueda nueva. La búsqueda usa el algoritmo
existente `run_nsga2` y `SimulationEvaluator`, incluyendo reparación, elitismo,
caché persistente y checkpoints. No sustituye NSGA-II por una heurística nueva.

Se fijan población 8, generaciones 5, réplicas de búsqueda 1–2 del banco autorizado,
cruce 0.90, mutación 0.20 y seed PCG64 2026. K y los nueve controles del escenario
usan el mismo adaptador de configuración que las simulaciones individuales.
Los objetivos son maximizar recursos entregados y minimizar distancia media de
ida. No se modifica ninguna fórmula del motor común.

El proceso separado usa dos workers de evaluación. Presupuesto máximo: 96
simulaciones (8 iniciales + hasta 40 descendientes, por dos seeds), 15 minutos y
un trabajo simultáneo en el servidor local de un solo worker. La aplicación no
inicia búsquedas al mover controles, seleccionar puntos o abrir páginas. El cierre
del backend termina el proceso de trabajo y sus procesos descendientes.

Los puntos solo aparecen como frente final tras cinco generaciones. Un objetivo
indefinido no se transforma en cero ni en un punto ficticio; si ninguna instalación
tiene objetivos definidos se informa un frente vacío. Errores e interrupciones
conservan los archivos de auditoría, sin presentar el checkpoint como resultado.

Seleccionar un punto muestra sus K ubicaciones **sin viajes anteriores**. La
simulación individual usa el escenario congelado de la búsqueda y una réplica
31–100 elegida por el usuario. Sus nueve métricas y logs se presentan por separado
de los promedios de las dos seeds de búsqueda. Se conserva la reproducción diaria.

## API y archivos de resultados

| Endpoint | Función |
| --- | --- |
| `POST /api/quick-nsga2` | Valida controles e inicia un trabajo; HTTP 202. |
| `GET /api/quick-nsga2/{job_id}` | Estado, generaciones completadas, instalaciones, simulaciones, tiempo, tamaño del frente; resultado solo al finalizar. |
| `POST /api/quick-nsga2/{job_id}/simulate` | Simula un `solution_id` del frente completo con `replication_id` 31–100. |

Cada UUID se guarda en `results/project2/quick_nsga2/`, ignorado por Git. Contiene
`request.json`, `metadata.json`, `evaluations.jsonl`, `checkpoint.json`,
`history.csv`, `front.json`, `result.json`, `status.json`, `worker.log` y, al
simular una instalación, `individual-<uuid>.json`. La metadata registra K,
parámetros y procedencia, seeds, versión y huellas del motor/configuración/datos.
Los IDs públicos son `quick_###` dentro de su trabajo; no se confunden con
`pareto_047` del frente histórico. Los checkpoints quedan disponibles para
diagnóstico; la interfaz no los reanuda automáticamente.

## Verificación y tiempos

`QUICK_NSGA_VERIFICATION.json` registra cinco búsquedas **reales**, cada una con
48 instalaciones y 96 simulaciones. Tiempos locales medidos, no garantías de
rendimiento; hubo otras comprobaciones ejecutándose en el equipo.

| Prueba | Tiempo total (s) | Tiempo worker (s) | Soluciones |
| --- | ---: | ---: | ---: |
| K=3 base | 164.72 | 140.37 | 3 |
| K=5 base | 223.37 | 211.38 | 7 |
| K=8 base | 344.64 | 313.33 | 4 |
| K=3 repetido, mismos parámetros/seed | 214.18 | 198.83 | 3 |
| K=3, recurso 1.5× y radio 1,500 m | 241.52 | 195.24 | 3 |

La repetición reproduce sitios y métricas exactamente (misma SHA-256 del frente).
La variante usa stock inicial 1,500 RU y radio 1,500 m; cambia la huella de
configuración y el frente. Se probaron varias soluciones individuales en K=3/K=8,
RANDOM K=3, GREEDY K=8 y el frente histórico con `pareto_047` K=5. SHA-256 antes y
después: **176 archivos protegidos, cero cambios** en fuentes, configuraciones,
datos y resultados científicos previos.

Pruebas Python: `tests/test_quick_nsga.py`, `tests/test_react_api.py`,
`tests/test_delivery_evidence.py` y `tests/project2/test_nsga2.py`. Cubren
validación, concurrencia, presupuesto/timeout, interrupciones, caché, selección,
reparación, reproducibilidad y uso de escenario congelado. React cubre arranque
explícito, polling, frente de un único punto, selección, K variable, vista previa,
reproducción y separación de métricas. Para equipos cargados:
`npm --prefix frontend test -- --maxWorkers=1`.

Resultado final: **45 pruebas Python distintas aprobadas** (44 de la suite
principal y el caso adicional de objetivos indefinidos), **53 pruebas React
aprobadas** y compilación TypeScript/Vite aprobada. La ejecución paralela de una
repetición de Vitest agotó el tiempo de arranque de sus workers en el equipo
cargado; la ejecución final secuencial terminó sin errores.

La verificación visual `scripts/project2_verify_quick_ui.cjs` reutiliza la
respuesta **real** del trabajo K=8: intercepta únicamente el POST inicial para
evitar otra optimización por una captura. La simulación individual y el resto de
la API son reales. Los tiempos y el progreso de las búsquedas se verifican en el
script Python, no mediante esta repetición visual. Sus capturas y resultados
se guardan en `screenshots/quick-nsga/` y `QUICK_NSGA_UI_VERIFICATION.json`.
La prueba visual aprobó selección de puntos, ocho marcadores/controles, ausencia
de viajes en vista previa, una simulación individual real, reproducción y ancho
móvil de 430 px sin desbordamiento ni errores JavaScript. No hizo otra búsqueda.

## Archivos de esta ampliación

- Backend: `backend/main.py`, `backend/service.py`, nuevos `backend/quick_nsga.py`
  y `backend/quick_nsga_worker.py`.
- React: `frontend/src/App.tsx`, `types.ts`, `movementModel.ts`,
  `components/MovementView.tsx`, `MovementMap.tsx`, `TripResources.tsx`, nuevos
  `components/QuickNsgaResults.tsx`, `quickNsga.css` y `useQuickNsga.ts`.
- Pruebas: `tests/test_quick_nsga.py`, `frontend/src/movementModel.test.ts`,
  `components/MovementView.test.tsx`, nuevos `components/QuickNsgaResults.test.tsx`
  y `useQuickNsga.test.tsx`.
- Reproducción: nuevos `scripts/project2_verify_quick_nsga.py` y
  `scripts/project2_verify_quick_ui.cjs`.
- Documentación: `.gitignore`, `README_REACT.md`, este documento, los dos reportes
  JSON y las capturas de esta modalidad.

## Límites

Cinco generaciones con dos semillas no demuestran un óptimo global ni robustez
estadística. El frente exploratorio no reemplaza la comparación histórica ni
justifica comparaciones de sus medias con las 70 réplicas de evaluación. RU sigue
siendo una unidad sintética, sin calibración ecológica. Se mantiene el contrato de
IDs distintos, que permite coordenadas coincidentes. No se implementaron modos
de 20 o 50 individuos, campañas nuevas de holdout ni simulación histórica Dietz.
