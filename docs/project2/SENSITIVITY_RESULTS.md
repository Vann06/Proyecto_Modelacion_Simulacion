# Sensibilidad y robustez limitada del modelo sintético

Evidencia: `results/project2/sensitivity_v111/`. Motor 1.1.1, 1 200 simulaciones,
14 condiciones, 30 seeds comunes 31–60 por condición/método disponible, 4 procesos.
Todos los parámetros, IDs de sitios, config_hash, seeds, identidad de datos y motor
están en metadata/replicates. No se reutilizan medias históricas 1.1.0 como base.

Diseño OAT: variar un factor respecto de la base (K=5, total=1 000 RU, alpha=1,
beta=2, radio=3 000 m, regeneración=0,1, oportunidades=12). Condiciones:

| Factor | Valores adicionales |
| --- | --- |
| Recurso total | 500, 1 500 synthetic_RU |
| K | 3, 8 |
| Alpha de competencia | 0, 4 |
| Radio | 1 500, 5 000 m |
| Regeneración | 0, 0,2 × recurso inicial/día |
| Beta de distancia | 1, 3 |
| Oportunidades | 24/colmena/día |

RANDOM utiliza una instalación por condición y optimizer_seed=2026; GREEDY se
recalcula con cada configuración. NSGA-II reevalúa las ubicaciones congeladas de
pareto_047, **sin nueva optimización**; no tiene filas para K=3/8 porque no existe
frente con ese K. Todos usan exactamente la misma configuración dentro de cada
condición. CSV conserva las nueve métricas; summary presenta cinco métricas, SD
muestral, media e IC bootstrap percentil 95% por seed (2 000, semilla 17).
`paired_vs_base.csv` conserva diferencias respecto de la base del mismo método.

## Lectura de resultados

| Condición | RANDOM | GREEDY | NSGA-II congelado | Unidad |
| --- | ---: | ---: | ---: | --- |
| Base | 725,75 | 919,83 | 933,56 | synthetic_RU entregadas |
| Radio 1 500 m | 419,49 | 848,14 | 785,82 | synthetic_RU entregadas |
| Radio 5 000 m | 845,93 | 954,28 | 950,81 | synthetic_RU entregadas |
| Sin regeneración | 410,21 | 602,50 | 621,91 | synthetic_RU entregadas |
| 24 oportunidades/día | 1 019,68 | 1 466,75 | 1 502,32 | synthetic_RU entregadas |

La regeneración y las oportunidades cambian fuertemente el recurso obtenido.
Con radio largo GREEDY supera ligeramente en media a las ubicaciones NSGA-II
congeladas: el ranking depende de la condición y estas últimas no se reoptimizaron.
Los números puntuales no sustituyen sus diferencias pareadas e intervalos.

La presión base es aproximadamente 0,000251 RANDOM, 0,000312 GREEDY y 0 NSGA-II.
Variar alpha produce diferencias pequeñas: con estas oportunidades y recursos,
la competencia simultánea entre colonias aparece raramente. Eso limita la señal
del tercer objetivo; no demuestra que la competencia ecológica real sea débil.

Subir K aumenta también el total de oportunidades (media por colmena fija), por
lo que una mayor entrega total no es prueba de eficiencia por colmena ni una
intervención controlada manteniendo demanda total. Consultar mínimo por colmena,
Jain y distancias para analizar ese compromiso.

## Lo que no se demostró

No hay interacciones factoriales, incertidumbre entre ubicaciones RANDOM nuevas,
múltiples optimizer seeds ni convergencia multiobjetivo confirmada. Seeds 31–60 ya
se habían examinado en resultados anteriores: la evidencia es descriptiva, no
holdout nuevo. Cambiar supuestos sintéticos no calibra parámetros ecológicos ni
valida recursos florales de Oslo. El clima se muestra como contexto observado,
sin introducir una relación causal no estimada en el motor.
