# Auditoría científica de Proyecto 2

Se revisaron notebooks 01–08, incluido 06.2, contrato, motor, estrategias, pruebas,
CSV de resultados, frente e historial. Inventario reproducible con hashes y celdas
de error: `results/project2/scientific_validation/notebook_audit.csv`.

## Comparabilidad

RANDOM, GREEDY y NSGA-II históricos comparten hashes de motor **1.1.0**, configuración,
inputs y contrato, K=5 y ventana diaria 2017-07-18 → 2017-08-04. La comparación usa
solo réplicas 31–100. RANDOM: 30 instalaciones × 70 seeds, promediadas por seed;
GREEDY: una instalación; NSGA-II: ejemplo `pareto_047`, elegido únicamente con
medias de búsqueda congeladas por distancia normalizada al ideal, pesos iguales.
La selección es ilustrativa, no una solución universalmente mejor. El equipo ya
inspeccionó el holdout: son resultados descriptivos, no una prueba confirmatoria.

IC bootstrap por seed común y diferencias pareadas: `comparison_paired.csv`.
Cambios absolutos y porcentuales: `scientific_validation/archived_changes.csv`.
Porcentaje firmado = 100 × (nuevo − base)/abs(base); si base=0 queda ausente.
En recurso, mayor es mejor; en distancia/presión, menor es mejor. Un cambio positivo
no es automáticamente una mejora. Los intervalos porcentuales dividen los límites
de la diferencia por la media base fija: no incluyen incertidumbre del denominador.
No son intervalos simultáneos ni incorporan nueva selección de instalaciones.

## Frente, convergencia y costo

49 soluciones por IDs corresponden a 32 conjuntos físicos distintos. 375 candidatos
contienen 351 coordenadas únicas. No se elimina historia ni cambia silenciosamente
la política de factibilidad (IDs distintos); la app muestra ambas identidades y
deduplica solo la presentación del frente. No implica que 32 opciones sean mutuamente
no dominadas bajo medias de evaluación: el frente se construyó en entrenamiento.

Historial: 51 generaciones incluyendo inicial, 75 240 simulaciones, 6,383 h sumadas.
Mostrar tamaño de archivo y mejor objetivo por generación es evidencia de evolución,
no demostración de convergencia al óptimo ni de estabilidad entre optimizer seeds.
Faltan múltiples búsquedas independientes y análisis de convergencia multiobjetivo
con referencia fijada antes de la evaluación (por ejemplo hipervolumen normalizado).
No se repite una búsqueda completa para abrir la app.

El motor acelerado 1.1.1 conserva resultados de una referencia exacta mediante
regresión de métricas y hashes de tablas de eventos; el perfil individual fue ~5×
más rápido. No se mezclan sus experimentos de sensibilidad con los CSV 1.1.0.

## Inconsistencias documentales

Notebooks 03 y 04 son auditorías históricas y algunos campos dicen
`inside_calibrated_window`: representa solapamiento de ventanas de muestreo,
**no calibración estadística lograda**. No se renombra el CSV porque sus bytes
forman parte de identidades de experimentos. El contrato anterior decía que faltaban
motor/estrategias: ahora se incluye un estado vigente, preservando las advertencias
de parámetros pendientes. Los notebooks previos y sus resultados se conservan.

La validación empírica y sus ausencias se detallan en `REAL_WORLD_VALIDATION.md`.
La sensibilidad OAT pertenece al motor 1.1.1, con 30 seeds comunes por condición,
RANDOM fijo seed 2026, GREEDY recalculado y ubicaciones NSGA-II congeladas.
No prueba efectos causales en Oslo, robustez entre optimizer seeds ni interacciones.
