# Síntesis científica final — Oslo Pollinator Lab

**Proyecto 2, UVG CC3074 · revisión de evidencia del commit dff96a3 · 7 de noviembre de 2026**

Este documento es la base del informe técnico y de la defensa. **No sustituye el PDF final**: integra resultados ya publicados y evita afirmar validación ecológica que los datos no respaldan. Complementa el notebook `notebooks/project2/08_final_results.ipynb` actualizado y `09_scientific_evidence.ipynb`.

## 1. Pregunta, sistema y alcance

**Pregunta experimental:** para cinco colmenas ubicadas en candidatos de un paisaje geográfico real de Oslo, ¿cómo se compara el recurso sintético entregado, distancia de forrajeo y presión de competencia al elegir instalaciones con RANDOM, GREEDY o NSGA-II?

**Actores/entidades:** parques y parches de recursos, sitios candidatos de colmena, colonias, viajes de forrajeo y eventos de consumo/retorno. Se simulan **viajes agregados**, no abejas identificadas, visitas reales ni polinización efectiva.

**Espacio:** capa GIS con 737 parques; 6 polígonos de precaución para colmenas; 375 IDs candidatos iniciales, **351 coordenadas diferentes**. Un parque no apto para instalar colmena puede seguir siendo recurso. La capa derivada exclusiva contiene **680 geometrías con superficie de recurso no solapada**, para evitar doble conteo; no equivale a decir que solo esos parques tienen flores. La capa GIS y la campaña Dryad no son una instantánea uniforme de 2017.

**Tiempo:** calendario diario del **18 de julio al 4 de agosto de 2017 (18 días)**. El recurso, consumo y regeneración por día son simulados; fechas del calendario no son observaciones diarias del recurso de cada parque. No se reconstruyó un año.

**Métrica principal:** `total_resource_obtained` en **synthetic_RU**, maximizar. Complementarias: `mean_distance_m` (m, minimizar), presión de competencia (fracción, minimizar), mínimo por colmena (synthetic_RU), equilibrio Jain, P95 distancia y parches utilizados (diagnóstico). No existe conversión validada de RU a néctar, polen o flores/m².

## 2. Modelo y simulación: qué es observado y qué es hipotético

- **Datos observados públicos:** Dryad, 593 filas florales, 1 297 de actividad, especies/fechas/condiciones; no hay coordenadas del `trap_number` que permitan un join exacto con los parques GIS.
- **Geografía pública:** polígonos de Oslo y restricciones de gestión para instalar colmenas; representaciones métricas EPSG:25833 y distancias de ida. La capa de aptitud visual no se transformó en valores numéricos.
- **Datos derivados:** áreas exclusivas sin doble conteo, densidades florales por transecto, agrupaciones por sitio/sesión, calendario y candidatos.
- **Parámetros de escenario, no medidas:** recurso inicial total 1 000 synthetic_RU; regla proporcional a superficie exclusiva; regeneración 0.1 del stock inicial por día; 12 oportunidades promedio por colonia/día; beta 2, alpha 1, radio 3 000 m, velocidad 5.5 m/s, K=5, entre otros. Ver `config/project2/base.yaml`.

El motor en `src/bee_sim/project2/simulation.py` genera oportunidades estocásticas, selecciona parches accesibles según recurso/distancia/competencia, organiza eventos de partida, viaje, búsqueda, forrajeo y retorno, descuenta stock, aplica regeneración al cierre y registra métricas. Mantiene recurso no negativo y usa un banco reproducible de semillas. El clima de Dryad se presenta como contexto, **no** como un predictor causal integrado al simulador actual.

## 3. Técnica de optimización y comparación justa

**RANDOM:** elige K IDs válidos sin reemplazo; referencia sin heurística. **GREEDY:** selección secuencial de sitios por ganancia de accesibilidad. **NSGA-II:** individuos con K sitios, cruce/mutación/reparación, ordenamiento no dominado y diversidad de crowding para maximizar recurso y minimizar distancia/presión.

Se cita la fuente original Deb et al. (2002), la documentación de pymoo y DEAP en `docs/project2/SOURCES_AND_AI.md`. La implementación de NSGA-II es propia del repositorio, no un simple wrapper de biblioteca.

**Identidad de la comparación histórica:** motor `project2-synthetic-1.1.0`, config/input/contrato con hashes compatibles, K=5, horizonte idéntico, seeds **31–100** (70). RANDOM tiene 30 instalaciones y 2 100 filas de evaluación, que se **promedian entre instalaciones por seed**, nunca se tratan como 2 100 réplicas independientes. GREEDY tiene una instalación; NSGA-II un frente archivado con 49 IDs que equivalen a 32 distribuciones físicas únicas. La alternativa `pareto_047` se escogió con medias de la búsqueda; el holdout fue examinado, por lo que las inferencias se consideran **descriptivas**.

### Valores medios archivados (motor 1.1.0)

| Métrica | RANDOM | GREEDY | NSGA-II: pareto_047 |
|---|---:|---:|---:|
| Recurso entregado (synthetic_RU) | 721.66 | 914.38 | **927.79** |
| Distancia media de ida (m) | 1 618.41 | 1 318.74 | **1 274.47** |
| Mínimo por colmena (synthetic_RU) | 106.11 | 158.91 | **161.35** |
| P95 distancia de ida (m) | 2 852.91 | **2 670.24** | 2 692.59 |
| Equilibrio Jain | 0.9549 | 0.9885 | 0.9893 |
| Parches utilizados | **239.36** | 232.04 | 225.17 |

**Diferencias relevantes:** NSGA-II vs RANDOM: **+206.12 synthetic_RU (+28.56%)** y **−343.94 m (−21.25%)** de distancia media. IC bootstrap 95% para diferencias pareadas: recurso [201.77, 210.50] RU y distancia [−347.58, −340.58] m. NSGA-II vs GREEDY: +13.41 RU y −44.27 m; **GREEDY tiene P95 22.35 m menor** que pareto_047. Son intervalos *puntuales condicionales a instalaciones fijas*; no cubren selección de nuevas instalaciones ni búsquedas independientes.

**Precaución:** una diferencia estadística dentro del simulador no demuestra intervención real mejorada en Oslo. No declarar un ganador universal: el orden depende de los objetivos y parámetros.

## 4. NSGA-II: interpretación, diversidad y costo

La búsqueda archivada registró **75 240 simulaciones, unas 6.38 horas**, 50 individuos y 50 generaciones más población inicial. Hubo una semilla de búsqueda principal: no hay estabilidad demostrada entre `optimizer_seed` diferentes, convergencia multiobjetivo formal ni garantía de óptimo global. El frente archivado contiene 49 filas por IDs, pero solo 32 configuraciones físicas: **375 candidatos no equivalen a 375 coordenadas únicas**. No se borran duplicados históricos ni se reoptimiza con el conjunto de evaluación.

El motor 1.1.1 se aceleró ~5× en una corrida perfilada manteniendo igualdad de registros contra referencia; esa prueba **no** equivale a medir otra búsqueda NSGA-II completa.

## 5. Sensibilidad e incertidumbre

**Experimento distinto:** motor 1.1.1, 14 condiciones OAT, **1 200 corridas**, 30 seeds comunes por combinación de método/condición disponible (31–60). RANDOM conserva una semilla de instalación, GREEDY recalcula la configuración y NSGA-II **reevalúa sitios congelados**, no reoptimiza. Para K=3 y K=8 no hay filas NSGA-II y no deben imputarse.

| Condición | RANDOM | GREEDY | NSGA-II congelado |
|---|---:|---:|---:|
| Base | 725.75 | 919.83 | 933.56 |
| Radio 1 500 m | 419.49 | **848.14** | 785.82 |
| Radio 5 000 m | 845.93 | **954.28** | 950.81 |
| Sin regeneración | 410.21 | 602.50 | 621.91 |
| 24 oportunidades por colmena/día | 1 019.68 | 1 466.75 | 1 502.32 |

Valores en synthetic_RU, **no comparables numéricamente** con las medias históricas 1.1.0. Radio corto y radio largo muestran que la ubicación fija `pareto_047` puede dejar de superar a GREEDY. Si K aumenta, aumenta además el número de oportunidades porque se mantiene la tasa por colmena; no interpretar el aumento de RU total como eficiencia individual. Competencia cercana a cero refleja los parámetros del escenario, no ausencia de competencia ecológica en Oslo.

Las comparaciones son emparejadas por seeds; IC bootstrap de 95% son puntuales. Se requiere estudiar interacciones y otras seeds de optimizador para robustez más fuerte.

## 6. Contraste cuantitativo con datos reales Dryad

**Qué se pudo hacer:** dos referentes estadísticos *independientes* del motor principal, con variables observacionales comparables consigo mismas.

- **Densidad floral:** 99 unidades completas, split por sitio de 79 para ajuste / 20 para evaluación; medición derivada **flores/m² del transecto**.
- **Actividad:** 216 sesiones elegibles, split por trap 79/20; tasa derivada de conteos registrados por minuto en sesión candidata, **no** individuos únicos ni polinización. El archivo tiene 101 IDs de traps para visitas y 100 para flores; no se eliminan identificadores por conveniencia.
- Treinta bootstrap de sitios de **ajuste** cuantifican variabilidad de ajuste; 2 000 remuestreos de sitios de evaluación dan IC de los errores. La separación es espacial por trap dentro de la muestra, no temporal ni validación de ciudad completa.

| Métrica | Modelo empírico global: MAE | Modelo empírico estratificado: MAE | Interpretación |
|---|---:|---:|---|
| Flores/m² | **10.227** | 11.106 | Estratificar por mes empeora |
| Conteos registrados/min | 0.9251 | **0.8425** | Estratificar por bandas de temperatura mejora en este split |

Los modelos empíricos predicen desde observaciones Dryad. **No fueron conectados a la lógica de resource/visitas del motor**. Falta un operador de observación que relacione viajes del motor con esfuerzo de muestreo y detectabilidad, y disponibilidad de recurso del motor con flores/m² sin equivalencias arbitrarias. Tampoco existe correspondencia espacial trap→parque. **La rúbrica de comparación de simulación con referencia real está parcialmente pendiente.**

### Tabla de correspondencia honesta

| Métrica/unidad | Referencia real | RANDOM del simulador | NSGA-II del simulador |
|---|---|---|---|
| Flores/m² del transecto | Disponible en Dryad | No produce esta unidad | No produce esta unidad |
| Conteos registrados/min | Disponible en Dryad (con restricciones) | No produce esta unidad | No produce esta unidad |
| synthetic_RU entregadas | No medido | 721.66 | 927.79 |
| Distancia media de ida (m) | Sin viajes reales comparables | 1 618.41 | 1 274.47 |
| Polinización efectiva | No medida | No implementada | No implementada |

**No inventar una fila con tres números equivalentes cuando no existe la medición.** La guía UVG acepta un referente documentado con limitaciones, pero los datos sintéticos por sí solos no constituyen validación con la realidad.

## 7. Conclusiones que sí se pueden defender

1. Una estrategia de ubicación multiobjetivo modifica sustancialmente el rendimiento de **este modelo sintético**, especialmente respecto de RANDOM.
2. GREEDY es un baseline competitivo e interpretable; NSGA-II no domina todas las métricas y su preferencia depende de los objetivos.
3. La sensibilidad muestra que una ubicación seleccionada en condiciones base **no tiene robustez universal**; con radios de vuelo distintos puede superar GREEDY.
4. El contraste empírico indica dispersión real de recursos/actividad y límites de una estratificación simple, **pero no valida el motor**.
5. La optimización no es una recomendación real de instalar colmenas: requiere calibración biológica, validación externa, estudio de permisos y protección de polinizadores silvestres.

**Recomendación condicionada:** para analizar compromisos en el escenario sintético, usar NSGA-II; si se busca rapidez y simplicidad, GREEDY es una alternativa razonable. Para decisiones ecológicas reales, recopilar datos empíricos de colonias, rendimiento floral y visitas bajo un diseño compatible antes de optimizar ubicaciones reales.

## 8. Reproducibilidad y material para la defensa

- Notebook: `notebooks/project2/08_final_results.ipynb` (con tablas, IC, Pareto, sensibilidad, evidencia Dryad y gráficos, sin optimización costosa).
- Evidencia adicional: `notebooks/project2/09_scientific_evidence.ipynb`.
- Resultados originales: `results/project2/integration/`; validación: `results/project2/scientific_validation/`; sensibilidad: `results/project2/sensitivity_v111/`.
- Frontend/backend: seguir `README_REACT.md`; diferencias en motores 1.1.0/1.1.1 explicadas.
- Verificaciones: `docs/project2/VERIFICATION.md`, hashes de config/entradas y banco de seeds.
- Fuentes e IA: `docs/project2/SOURCES_AND_AI.md`.
- Guion: `docs/project2/DEMO_SCRIPT.md`; adaptar a número real de integrantes y ensayar.

**Pendiente de entrega:** PDF técnico final que corresponda exactamente a este alcance, diapositivas, registro nominal de contribuciones, ensayo cronometrado, ejecución de pruebas/build en el equipo de demostración y verificación ecológica directa si existe evidencia suficiente. Ver `FINAL_DELIVERY_CHECKLIST.md`.

No mezclar resultados de motor 1.1.0 y 1.1.1. No atribuir una mejora sintética a una intervención real.