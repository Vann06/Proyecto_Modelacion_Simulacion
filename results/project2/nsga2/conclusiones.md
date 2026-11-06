# Conclusiones de NSGA-II, Proyecto 2

NSGA-II encontró instalaciones mucho mejores que las colocadas al azar, y esas mejoras se sostienen con réplicas nuevas. Todavía no se puede afirmar que sea mejor que RANDOM o GREEDY, ni que los resultados representen el Oslo real.

> En el escenario sintético, NSGA-II identificó 32 instalaciones físicas distintas, con desempeño estable en 70 réplicas reservadas. El conflicto dominante fue recurso contra distancia, mientras que la competencia tuvo un efecto marginal con estos parámetros.

## Corrida evaluada

| Elemento | Valor |
|---|---|
| Escenario | `synthetic_base_v1`, con parámetros de prueba |
| Instalación | K = 5 colmenas entre 375 sitios candidatos |
| Objetivos | Maximizar `total_resource_obtained`, minimizar `mean_distance_m` y `competition_pressure` |
| Búsqueda | Población 50, 50 generaciones, réplicas 1–30, `optimizer_seed` 2026 |
| Costo de la búsqueda | 75,240 simulaciones, unas 6.4 horas, 2,508 instalaciones evaluadas |
| Frente congelado | 49 soluciones en `front.json` |
| Holdout | Réplicas 31–100: 49 soluciones × 70 réplicas = 3,430 filas en `../nsga2_results.csv` |
| `config_hash` | `32b62484aff30d3403707694d538d776600f9dec8381d4f6dae22405452e673d` |
| `engine_hash` | `6a032bf015293cabcaa47dc8b0a3cd72e8b8d3e1061deeed8664cb88108f1d62` |

Salvo que se indique otra cosa, los valores son medias del holdout.

## Lo que los datos respaldan

1. **La optimización aporta mucho.** La población inicial aleatoria promediaba 771.8 de recurso y 1,610 m de distancia. La mediana del frente en el holdout es 953.1 y 1,394 m: cerca de 23% más recurso y 13% menos distancia. Es una referencia orientativa, no una comparación formal, porque la población inicial se midió con las réplicas 1–30.

2. **Los resultados no fueron suerte.** Del paso de búsqueda a holdout, el recurso bajó en promedio 2.9 unidades (0.3%) y la distancia cambió −0.8 m. El orden de las soluciones se mantuvo, con Spearman de 0.98 en recurso, 0.996 en distancia y 0.94 en competencia.

3. **El dilema real es recurso contra distancia.** Pasar de `pareto_038` a `pareto_002` da 4% más recurso (926.0 → 965.7), pero cuesta 11% más distancia (1,284 → 1,428 m).

4. **Hay un punto donde reducir distancia deja de valer la pena.** `pareto_045` es la de menor distancia, pero frente a `pareto_047` ahorra solo 37 m y pierde unas 170 unidades de recurso (18%).

5. **La competencia casi no influye.** Su valor máximo en el holdout es de 0.11%, y el piloto ya mostró que casi no ocurre con estos parámetros. En la práctica, el problema se comporta casi como uno de dos objetivos. También fue la métrica menos estable: de las 19 soluciones con media 0 en la búsqueda, solo 5 siguen en 0 en el holdout.

6. **La ubicación importa mucho.** El frente usa solo 23 de los 375 sitios candidatos, y dos de ellos aparecen en 39 y 37 de las 49 soluciones. Eso apunta a que unas pocas zonas concentran el valor, aunque falta verlas en un mapa para explicar por qué.

## Soluciones destacadas

| Solución | Perfil | Recurso | Distancia (m) | Competencia |
|---|---|---|---|---|
| `pareto_002` | Más recurso | 965.7 | 1,428.3 | 0.000952 |
| `pareto_013` | Compromiso recomendado | 957.5 | 1,395.6 | 0.000026 |
| `pareto_021` | Más recurso con competencia 0 | 951.2 | 1,368.1 | 0 |
| `pareto_038` | Distancia baja con recurso alto | 926.0 | 1,283.8 | 0.000013 |
| `pareto_047` | Distancia baja con recurso alto | 927.8 | 1,274.5 | 0.000026 |
| `pareto_045` | Menor distancia | 757.9 | 1,237.9 | 0.000095 |

**Recomendación:** `pareto_013` es un compromiso equilibrado: queda a 0.9% de la mejor solución en recurso, con competencia casi nula. Frente a `pareto_017` cede 7.3 unidades de recurso (±1.1 de error estándar) y recorre 38 m menos. Si la prioridad es recorrer menos, `pareto_038` o `pareto_047` son mejores opciones.

## Soluciones duplicadas

Las 49 soluciones del frente corresponden a **32 instalaciones físicas distintas**. El catálogo tiene 375 candidatos pero solo 351 coordenadas únicas; por ejemplo, los sitios `_679` y `_680` están en el mismo punto, y NSGA-II los trató como soluciones diferentes. Por eso, 16 grupos de soluciones dieron métricas idénticas en las 70 réplicas.

- Ninguna solución pone dos colmenas en el mismo punto, así que los valores son válidos.
- Con los valores del holdout, 26 de las 32 instalaciones quedan no dominadas. Ese filtro usa el propio holdout, así que es una descripción, no un frente nuevo.
- Los duplicados también ocuparon lugares en la población, lo que redujo algo la diversidad de la búsqueda.
- `front.json` no se modificó. Corregir esto requiere otra búsqueda, y las réplicas 31–100 ya no contarían como datos nuevos para ella.

## Lo que todavía no se puede concluir

- **Que NSGA-II supere a RANDOM y GREEDY:** falta correrlos con las mismas réplicas. GREEDY en particular podría acercarse bastante si unos pocos sitios concentran el valor.
- **Que esto aplique al Oslo real:** la corrida usa un escenario sintético con parámetros de prueba. Las conclusiones valen para el modelo; ubicar colmenas reales requiere calibrarlo.
- **Que el frente esté completo:** los mejores valores de recurso y distancia no mejoran desde la generación 40 o antes, pero el frente seguía creciendo al final (de 32 a 49 soluciones). Pueden faltar soluciones intermedias.
- **Que la competencia no importe en la realidad:** el resultado depende de los parámetros actuales; con más colmenas o más viajes podría pesar mucho más.

## Siguiente paso

Comparar con RANDOM y GREEDY usando las réplicas 31–100.
