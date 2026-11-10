# GREEDY: diseño, pruebas y resultados

Branch sugerida: `feature/greedy-baseline`. Todo el recurso es sintético (`synthetic_RU`). Nada de este documento es una estimación ecológica de Oslo.

## Información permitida

El selector usa solo el catálogo de 375 candidatos, el recurso inicial sintético que define la regla común (`exclusive_area_share`), la matriz de distancias derivada, el radio de forrajeo, la escala de distancia y K del config común. No llama a `simulate` ni lee `resource_log`, viajes o rendimientos futuros. No usa azar.

## Score

Para un candidato `s`, un parche `p` y el conjunto `S` ya elegido:

- `valor(s,p) = R0_p * (1 + d_sp / escala)^(-gamma)` si `d_sp <= radio`, y 0 en otro caso. Unidades: synthetic_RU por un factor de atracción adimensional.
- `n_S(p)` es el número de sitios de `S` que cubren a `p` (distancia menor o igual al radio).
- `ganancia(s | S) = sum_p valor(s,p) / (1 + lambda * n_S(p))`.

En cada paso se agrega el candidato con mayor ganancia. Desempate: menor `site_id` en orden lexicográfico. Este orden se fija antes de cualquier comparación.

## Actualización y duplicados

Al elegir un sitio se suma 1 a `n_S(p)` de todos los parches dentro de su radio. Esa cobertura pasa a ser compartida y su valor para los siguientes candidatos se divide entre `1 + lambda * n_S(p)`. Los sitios ya elegidos se excluyen del argmax, así que no hay duplicados.

La penalización es una estimación de diseño. No es competencia observada ni el estado futuro de ocupación del motor.

## Parámetros

Están en `config/project2/strategies/greedy.yaml`, aparte del config común y fuera de su `config_hash`.

| Parámetro | Valor | Nota |
|---|---|---|
| `distance_exponent` (gamma) | 2.0 | Propio de la heurística, no se enlaza con `beta` del motor |
| `overlap_penalty` (lambda) | 1.0 | 0 desactiva la penalización |

Si cambian `alpha`, `beta`, K o el radio del motor, el cambio se aplica a todos los métodos y GREEDY se vuelve a correr con el nuevo config.

## Complejidad

Con N candidatos y M parches, construir los valores cuesta O(NM) y cada uno de los K pasos recalcula las ganancias en O(NM), para un total de O(KNM) y memoria O(NM). No se usan cachés porque N=375, M=737 y K=5, y la selección tarda menos de un segundo.

## Pruebas del selector

`tests/project2/test_greedy_selector.py` (unittest) verifica:

- exactamente K IDs válidos y sin duplicados
- terminación con scores todos cero o empatados
- desempate estable y resultado idéntico en repeticiones
- la penalización favorece cobertura nueva
- ganancias elegidas no crecientes (propiedad submodular)
- entradas inválidas rechazadas
- ausencia de acceso a información futura o azar en el código del selector
- parámetros de GREEDY fuera del `config_hash` común

## Reproducción

```powershell
python -m pip install -r requirements.txt
python scripts/project2_run.py prepare
python -m unittest discover -s tests/project2 -v
python scripts/project2_greedy.py select
python scripts/project2_run.py evaluate --sites-file results/project2/greedy_sites.json --method GREEDY --replications 100 --output results/project2/greedy_results.csv
python scripts/project2_run.py inspect --results results/project2/greedy_results.csv
python scripts/project2_greedy_figures.py
# con results/project2/random_results.csv presente (rama RANDOM):
python scripts/project2_greedy_vs_random.py
# con results/project2/nsga2_results.csv presente (rama NSGA-II):
python scripts/project2_greedy_vs_nsga2.py
```

## Resultados (100 réplicas, semillas comunes, config `synthetic_base_v1`)

Sitios elegidos (en orden): `..._0_643`, `..._0_188`, `..._0_172`, `..._0_553`, `..._0_274`.

| Métrica | Media | Desv. est. | IC95% |
|---|---|---|---|
| Recurso total (synthetic_RU) | 915.10 | 32.85 | 908.58 a 921.62 |
| Recurso medio por colmena | 183.02 | 6.57 | 181.72 a 184.32 |
| Recurso mínimo por colmena | 159.13 | 9.06 | 157.33 a 160.93 |
| Distancia media de ida (m) | 1318.4 | 21.2 | 1314.2 a 1322.6 |
| Distancia P95 (m) | 2671.0 | 33.9 | 2664.3 a 2677.7 |
| Presión de competencia | 0.00026 | 0.00053 | 0.00016 a 0.00037 |
| Jain de equilibrio | 0.9887 | 0.0064 | 0.9874 a 0.9900 |
| Parches usados | 232.2 | 7.8 | 230.7 a 233.7 |

Tabla completa en `results/project2/greedy_summary.csv`.

## Comparación con RANDOM (semillas pareadas)

Script: `scripts/project2_greedy_vs_random.py`. Tabla: `results/project2/greedy_vs_random.csv`. Figura: `figures_greedy/greedy_fig5_vs_random.png`.

Diseño: GREEDY es una instalación determinista evaluada en las 100 semillas comunes. RANDOM son 30 instalaciones aleatorias evaluadas en esas mismas 100 semillas. El script verifica que config_hash, engine_hash, input_hash, contrato de métricas y semillas coincidan, y se detiene si no. La diferencia pareada por réplica es GREEDY menos la media de las 30 instalaciones RANDOM, con bootstrap de 5000 remuestreos (semilla 123) sobre las 100 diferencias. Ese intervalo cubre la variación del motor y no la variación entre instalaciones, que se reporta con la fracción de instalaciones RANDOM peores que GREEDY.

| Métrica | GREEDY | RANDOM | Cambio | IC95% pareado |
|---|---|---|---|---|
| Recurso total (synthetic_RU) | 915.1 | 722.0 | +193.1 (+26.7%) | 189.5 a 196.6 |
| Recurso mínimo por colmena | 159.1 | 106.0 | +53.1 (+50.1%) | 51.4 a 54.8 |
| Distancia media de ida (m) | 1318.4 | 1618.5 | -300.2 (-18.5%) | -304.2 a -296.1 |
| Distancia P95 (m) | 2671.0 | 2853.2 | -182.2 (-6.4%) | -188.7 a -175.7 |
| Jain | 0.9887 | 0.9548 | +0.0339 (+3.5%) | 0.0327 a 0.0350 |
| Competencia (fracción) | 0.00026 | 0.00032 | -0.00006 | -0.00016 a 0.00005 |

GREEDY supera a las 30 instalaciones RANDOM en recurso total, recurso mínimo y distancia media. En Jain supera a 25 de 30 (83%). En competencia el intervalo incluye 0, por lo que no hay diferencia distinguible.

## Comparación con NSGA-II (réplicas reservadas 31 a 100)

Script: `scripts/project2_greedy_vs_nsga2.py`. Tabla: `results/project2/greedy_vs_nsga2.csv` y `greedy_vs_nsga2_extra.json`. Figura: `figures_greedy/greedy_fig6_vs_nsga2.png`.

NSGA-II congeló un frente de 49 soluciones con las réplicas 1 a 30 y lo evaluó en las réplicas 31 a 100. GREEDY se recorta a esas mismas 70 semillas. El script verifica hashes y semillas y se detiene si no coinciden. La diferencia pareada usa la solución recomendada por NSGA-II (`pareto_013`, que se eligió viendo el conjunto reservado) y, para no depender de esa elección, también se reporta la mediana del frente y cuántas de las 49 soluciones superan a GREEDY.

| Métrica | GREEDY | pareto_013 | Cambio | IC95% pareado | Frente mejor que GREEDY |
|---|---|---|---|---|---|
| Recurso total (synthetic_RU) | 914.4 | 957.5 | +43.1 (+4.7%) | 39.5 a 46.7 | 48 de 49 |
| Distancia media (m) | 1318.7 | 1395.6 | +76.8 | 70.9 a 82.8 | 14 de 49 |
| Distancia P95 (m) | 2670.2 | 2600.9 | -69.3 | -81.0 a -57.6 | 39 de 49 |
| Jain | 0.9885 | 0.9921 | +0.0036 | 0.0019 a 0.0053 | 48 de 49 |

Nueve soluciones del frente dominan a GREEDY en los tres objetivos de NSGA-II y GREEDY no domina a ninguna. NSGA-II gana en recurso y GREEDY queda en el extremo de poca distancia. La búsqueda de NSGA-II usó unas 75 mil simulaciones y GREEDY se calcula en menos de un segundo.

## Limitaciones

- Las comparaciones con RANDOM y NSGA-II son solo sobre el motor sintético y no son evidencia sobre Oslo.
- La puntuación de GREEDY usa la misma forma funcional de atracción que el motor (recurso y distancia con exponente), así que su ventaja sobre RANDOM es esperable y no prueba que una regla distinta bajo otro motor se comporte igual.
- La competencia baja es consecuencia de los parámetros sintéticos de prueba (12 salidas por día, 1000 synthetic_RU totales). No debe interpretarse como un hallazgo sobre Oslo.
- El score usa recurso inicial según área exclusiva. La asignación por orden de `patch_id` es arbitraria y puede fragmentar parques.
- Una heurística sin retroalimentación del motor puede quedar lejos del óptimo si la dinámica de agotamiento domina.

## Archivos propios

`src/bee_sim/project2/strategies/{__init__,greedy_baseline}.py`, `config/project2/strategies/greedy.yaml`, `tests/project2/test_greedy_selector.py`, `scripts/project2_greedy.py`, `scripts/project2_greedy_figures.py`, `scripts/project2_greedy_vs_random.py`, `scripts/project2_greedy_vs_nsga2.py`, `docs/project2/greedy_design.md` y `results/project2/greedy_*`.
