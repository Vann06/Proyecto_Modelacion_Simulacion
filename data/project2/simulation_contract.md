# Contrato común del simulador — Proyecto 2, Oslo

Estado vigente: motor **project2-synthetic-1.1.1**, exclusivamente sintético y sin calibración ecológica. RANDOM, GREEDY y NSGA-II están implementados y comparten `simulate`. Los resultados históricos se conservan con project2-synthetic-1.1.0; no mezclar cohortes. Ver docs/project2/SCIENTIFIC_AUDIT.md y REAL_WORLD_VALIDATION.md.

## Entidades e inputs

- `FloralPatch`: cualquiera de los 737 espacios verdes como recurso potencial, incluidos los 362 excluidos para colocar colmena. No equivale a capacidad floral observada.
- `CandidateHiveSite`: uno de 375 puntos interiores admisibles bajo la regla de polígonos enteramente disjuntos de zonas libres de abejas. No se infieren otros permisos.
- `Hive`: colonia agregada en un sitio candidato; exactamente K sitios distintos. El motor mínimo no representa un número finito de obreras ni mortalidad de colonia.
- Inputs originales: `data/project2/processed/{spatial_patches.csv,oslo_parks.geojson,bee_free_zones.geojson,candidate_hive_sites.csv,hive_patch_distances.npz,simulation_calendar.csv,temporal_variable_metadata.csv,experiment_seeds.csv,simulation_metrics_contract.csv}`. Dryad es evidencia de auditoría, no stock por parque ni coordenadas de traps.
- Nuevos derivados: `resource_patches.csv`, `resource_patches.geojson`, `resource_patch_distances.npz`, `resource_preparation.json`. Preparar explícitamente con `python scripts/project2_run.py prepare`. No se sobrescriben originales.

## Horizonte y procedencia

Diario, 2017-07-18 → 2017-08-04, 18 días inclusivos. Es la ventana propuesta para calibrar/validar; el motor actual sigue siendo de prueba. Junio–septiembre es contexto cualitativo y anual es arquitectura sin curva calibrada. Los proxies July=1/August≈0.761 no se aplican como recursos diarios.

Cada parámetro de `config/project2/base.yaml` tiene `value`, `status`, `provisional` y `source`. Estados: observed, derived, inherited_from_project1, scenario_parameter, pending_calibration. Heredar un supuesto no lo convierte en observación. Las etiquetas observed/derived/modeled/scenario_parameter de las variables de 03 permanecen vigentes.

## Solapamientos y recurso inicial

Regla fija `lexicographic_patch_id_priority_v1`: ordenar IDs como texto y asignar a cada j su geometría menos la unión de todos los polígonos anteriores. La unión territorial se conserva y los interiores no cuentan dos veces. El CSV mantiene 737 IDs; 680 tienen área positiva y 57 reciben área cero según esta convención. El GeoJSON derivado contiene solo geometrías positivas; no inventa polígonos para los restantes. Cero área asignada no significa cero flores observado.

Ventajas: simple, determinista, trazable, conserva IDs y unión sin doble conteo. Desventajas: prioridad arbitraria sin calidad ecológica; fragmenta parques, puede cambiar puntos representativos y afectar resultados. Requiere sensibilidad frente a otras políticas antes de conclusiones ecológicas. Los originales permanecen intactos.

`exclusive_area_share` reparte un total de fichas sintéticas según área exclusiva/área de unión. No multiplica áreas por densidad Dryad ni estima capacidad floral. Cero área asignada implica siempre cero stock bajo esta regla.

## Interfaz y retorno

`simulate(hive_sites, seed, config)` en `bee_sim.project2.simulation`. `load_config` crea un objeto validado e inmutable. Los overrides explícitos `with_parameters` cambian config_hash; no se admiten callbacks de reglas o métricas.

Validar K IDs distintos del catálogo antes de sortear y ordenar canónicamente; hive_slot=0…K−1. Seed uint32 del banco común. El horizonte y las reglas no se alteran por estrategia. Falta de configuración/derivados o manifest obsoleto producen error claro, sin fallback.

Salida:

- `metrics`: exactamente nueve claves; None cuando el denominador no existe.
- `per_hive`: K filas con hive_slot, site_id, resource_delivered, incluyendo entrega cero.
- `trips`: date, hive_slot, site_id, trip_slot, patch_id, departure/arrival/foraging_start/foraging_end/return_min, one_way_distance_m, competition_at_selection, other_colonies_active_at_foraging_start, foraging_attempt, resource_consumed, resource_delivered, returned. Etapas no alcanzadas quedan ausentes. Arrival/return definidos fuera de jornada son tiempos planificados, no eventos ejecutados después del cierre.
- `resource_log`: date/patch_id, R_before, consumption, regeneration, R_after en todos los días/parches.
- `events`: oportunidades sin destino, salida, llegada, inicio/fin de forrajeo y retorno. amount_ru depende del tipo de evento; no sumar retiros y entregas como si ambos fueran recurso obtenido.
- `provenance`: mode, scenario, resource_unit, seed, config_hash, engine_version, engine_hash, metric_contract_hash, input_hash (resumen) e input_hashes (detalle), rng, política y versiones NumPy/pandas. No incluir tiempo de ejecución en igualdad estocástica. El escritor rechaza mezclar datos/configuraciones/motores/contratos distintos en un archivo comparable.

## Flujo diario implementado

Inicio → oportunidades de viaje → seleccionar → viajar → buscar/forrajear → consumir → regresar → registrar → regenerar al cierre.

Oportunidades Poisson por colonia/día; tiempos uniformes condicionales y slots definidos antes de decisiones. Sin destinos no se inicia viaje; el slot no se recicla. Reloj común de todas las colonias, empates por `(time_min,event_priority,hive_slot,trip_slot)`: return=0, foraging_end=1, foraging_start=2, arrival=3, departure=4. Cierres antes de aperturas implementan ocupación [inicio,fin).

`score_j = R_j / ((1+d_ij/distance_scale_m)^beta * (1+alpha*competition_j))`; `P(j)=score_j/sum(score)` sobre stock positivo y distancia <= max_foraging_distance_m. competition_j cuenta otras colonias distintas activas al seleccionar, sin mirar eventos futuros. Si no hay scores positivos, registrar oportunidad sin parche, no fallback uniforme. La presión se mide al inicio de forrajeo y puede diferir del snapshot de selección.

Búsqueda y demanda exponenciales con medias de prueba. Al iniciar forrajeo reservar/retirar atómicamente `min(stock,demanda,tiempo_restante*foraging_rate)`. Tiempo de servicio=consumo/tasa. Retorno si cabe en jornada, sin mortalidad biológica. Se generan nuevas oportunidades al siguiente día sin retirar obreras por fallos; no se representa población finita. No se calcula polinización, néctar físico o polen.

## Balance del recurso

R_j(t) es el stock inicial del día en **synthetic_RU**, fichas sin conversión observada.

`R_j(t+1)=max(0,R_j(t)-consumption_j(t)+regeneration_j(t))`.

Consumo acumulado <= stock inicial, sin esconder sobreconsumo con max. Un fallo de retorno no repone recurso. Regeneración al cierre = regeneration_rate * R_initial, sin techo adicional: puede acumularse si no se consume. Es una simplificación sintética explícita, no fenología calibrada. Recurso obtenido significa entregado por retornos dentro de jornada, no todo lo consumido.

## Distancias

EPSG:25833 y metros, distancia euclidiana de ida entre puntos representativos. Los destinos se recalculan dentro de las geometrías exclusivas. La nueva matriz 375x737 incluye IDs, coordenadas y CRS; leer NPZ con allow_pickle=False. Los IDs sin área mantienen referencia geométrica original solo como coordenada finita, nunca destino elegible. La matriz de 04 permanece intacta. Distancias cero son válidas. No son rutas ni trayectorias reales; convertir velocidad m/s a m/min para vuelos.

## Métricas congeladas

Fuente normativa: `simulation_metrics_contract.csv`, verificada por nombres, definiciones, unidades y direcciones. Única implementación: `metrics.py`.

| metric | Definición resumida | direction |
| --- | --- | --- |
| total_resource_obtained | Total entregado a K colonias dentro de jornada | maximize |
| mean_resource_per_hive | Entrega total/K incluyendo ceros | maximize |
| min_resource_per_hive | Mínima entrega acumulada entre K | maximize |
| mean_distance_m | Media de idas de viajes iniciados, incluso sin retorno | minimize |
| total_distance_m | Suma de idas, no vuelo total ida/vuelta | minimize |
| p95_distance_m | P95 de esas idas, quantile linear | minimize |
| competition_pressure | Fracción de intentos con otra colonia activa al inicio de forrajeo | minimize |
| hive_balance_jain | (suma entregas)^2/(K*suma entregas²) | maximize |
| patches_used_count | IDs con consumo positivo | report_only |

Recurso en synthetic_RU, distancias en metros, presión [0,1], Jain [1/K,1] si definido y parches en conteo. Sin viajes: distancia total/parches=0; media/P95/presión ausentes. Sin entrega: total/media/mínimo=0 y Jain ausente. No omitir métricas ni colonias de bajo rendimiento.

## Seeds y comparación

Banco de 100 uint32, replication_id 1…100. PCG64 por `(seed,day,hive_slot,trip_slot,draw_slot,process_code)`, sin nombre de algoritmo ni hash() de Python. Acoplamiento CRN por oportunidad y proceso; mismas semillas en instalaciones distintas no significan mismas métricas. Repetir la misma clave reinicia el bloque.

Todos usan igual K, horizonte, motor/hash, datos, familias y parámetros, y seeds. RNG del optimizador separado, registrado como optimizer_seed. Solo se generan instalaciones fuera del motor. El escritor común result_row/write_results conserva esquema; ver `RESULTS_SCHEMA.md`. Cambios de reglas/contrato requieren versión y reevaluación común. Si se optimiza con réplicas 1–30, congelar soluciones y reportar 31–100 por separado; el agregado de 100 incluye entrenamiento y no es independiente de él.

## Pruebas y pendientes

`python -m unittest discover -s tests/project2 -v` comprueba reproducibilidad/permutaciones, K/sitios, distancias/cierre, balance/continuidad/no negativos, ausencia de recurso, conservación de área, protección de métricas y esquema. Bootstrap 95% de contract.py sigue disponible para diferencias emparejadas de réplicas, no viajes dependientes.

04 conserva la auditoría previa; sus límites de calibración no se resuelven con pruebas sintéticas. Proyecto 1 permanece intacto. Sus componentes son referencias reutilizables; disponibilidad por viaje, Weibull espacial y logística no se heredan como calibración de Oslo.

Pendientes: unidades/capacidades biológicas, calidad floral, regeneración/techo, otras políticas de solapamientos, alpha/beta/radio/escala, actividad y población de colonia, intensidad y tiempos, preferencias, supervivencia, polinización y operador de observación. Dryad flores/m² no es R, y conteos durante muestreos no son viajes/día ni individuos únicos. Se necesita correspondencia espacial y control del esfuerzo antes de equivalencias. Los algoritmos de ubicación ya están implementados; sus resultados no resuelven estos pendientes ecológicos.
