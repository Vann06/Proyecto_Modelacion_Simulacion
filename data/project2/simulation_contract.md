# Contrato común del simulador — Proyecto 2, Oslo

Versión: 1.0. Motor espacial futuro: **no implementado ni calibrado** en esta entrega.
Guía común para RANDOM, GREEDY y NSGA-II; ningún algoritmo redefine motor, métricas o parámetros.

## Entidades e inputs

- FloralPatch: los 737 polígonos de espacios verdes como recurso potencial, incluidos 362 que no admiten colmena bajo la regla conservadora. No hay capacidades absolutas asignadas.
- CandidateHiveSite: uno de 375 puntos representativos interiores de polígonos enteramente disjuntos de zonas libres de abejas. Validación geométrica de la regla disponible, no inferencia de otros permisos.
- Hive: una colonia en un CandidateHiveSite; exactamente K sitios válidos distintos, sin duplicados. K aún debe fijarse por experimento y ser común a todos los métodos.
- Inputs: processed/spatial_patches.csv, oslo_parks.geojson, bee_free_zones.geojson, simulation_calendar.csv y temporal_variable_metadata.csv; TXT Dryad originales para observación. Nuevas entradas compartidas: candidate_hive_sites.csv, hive_patch_distances.npz, experiment_seeds.csv y simulation_metrics_contract.csv.
- Preservar IDs y hashes. Traps Dryad carecen de coordenadas; no unirlos arbitrariamente a parques. Polígonos solapados requieren política de recurso compartido antes de parametrizar stock por área.

## Horizonte y evidencia

Resolución diaria: 2017-07-18 a 2017-08-04, 18 días inclusivos. Ventana para calibrar/validar, no modelo ya calibrado. Junio–septiembre es apoyo estacional cualitativo; anual es exploratorio sin curva de recurso.
observed = medición escrita en fuente; derived = fechas contextualizadas/densidades/distancias/agregaciones; modeled = recurso futuro y procesos ecológicos; scenario_parameter = K, sensibilidad, seeds y decisiones del experimento. Metadatos de 03 siguen vigentes. Proxies July=1 y August≈0.761 no son curva longitudinal ni recursos diarios automáticos.

## Interfaz única y resultados

`simulate(hive_sites, seed, config)` devolverá un diccionario con `metrics`, `per_hive`, `trips`, `resource_log`, `provenance`.
`hive_sites`: IDs ordenados canónicamente por el motor; colonias asociadas a hive_slot 0…K−1. Validar antes de sortear, sin reducir silenciosamente K.
`config`: mismo motor/versiones, hashes de inputs, K, calendario, familias y parámetros de distribuciones para todos. Rechazar configuración incompleta antes de consumir RNG. Recursos/unidades no tienen defaults inventados.
`per_hive`: K filas, incluso con entrega cero; hive_slot, site_id, resource_delivered. `trips`: date, hive_slot, trip_slot, patch_id, one_way_distance_m, foraging_start/end_min, resource_consumed/delivered, returned, competition_at_selection y other_colonies_active_at_foraging_start. `resource_log`: date/patch_id, R_before, consumption, regeneration, R_after. `provenance`: seed, config/input hashes, versiones y esquema RNG. No incluir tiempo de ejecución variable en igualdad estocástica.
Las nueve métricas obligatorias se emiten siempre; valores indefinidos quedan ausentes con denominador documentado, no se omite la clave. Diagnósticos adicionales separados.

## Flujo y recurso

Inicio del día → generar viajes → seleccionar parche → viajar → forrajear → consumir recurso → regresar → registrar métricas; cerrar balance y trasladar estado al día siguiente.
Procesar colonias en un reloj de eventos común; empates por (tiempo, hive_slot, trip_slot, tipo de evento), congelado en la versión del motor. Las oportunidades de viaje deben tener slots estables antes de ramas aleatorias.
R_j(t) = stock al inicio del día, en RU simbólica pendiente de calibrar. R_j(t+1)=max(0,R_j(t)-consumption_j(t)+regeneration_j(t)). Regeneración acreditada al cierre. Consumo atómico compartido y no mayor al stock inicial; no ocultar sobreconsumo con max. Fallo de retorno no repone lo consumido. Recurso entregado solo cuenta retornos exitosos dentro del horizonte. No se ejecutó esta dinámica ecológica aún.

## Selección y competencia configurables

score_j = R_j / ((1+d_ij/distance_scale_m)^beta * (1+alpha*competition_j)); P(j)=score_j/sum(score).
alpha>=0, beta>=0 y distance_scale_m>0, sin valores fijados. competition_j cuenta otras colonias distintas activas al seleccionar el destino. No usa ocupación futura. Registrar también ocupación al inicio de forrajeo para la métrica de presión, que puede diferir tras viajar. Si sum(score)=0, no hay forrajeo disponible; registrar oportunidad no atendida, sin fallback uniforme silencioso. Destinos florales incluyen todos los parches, no solo candidatos para colmenas.

## Distancias y unidades

EPSG:25833, metros; matriz 375x737 entre puntos representativos interiores, distancia euclidiana de ida, sin rutas ni barreras. NPZ contiene distancias, IDs, coordenadas y CRS; leer con allow_pickle=False. Permitir cero al parche de origen. No confundir con km de Proyecto 1 ni con suma ida/vuelta.
RU es símbolo, no ml ni conteo floral observado. Definir resource_unit y conversión mediante evidencia antes de simular. No asignar capacidades por área sin resolver solapamientos y falta de correspondencia entre traps y parques.

## Semillas y comparación justa

100 seeds uint32 en experiment_seeds.csv, replication_id 1…100, generadas con SeedSequence(2017). Igual banco para todas las estrategias bajo igual escenario/K/config. RNG del optimizador independiente del de evaluación. Guardar también versiones de NumPy y motor.
CRN: PCG64 por (seed, day, hive_slot, trip_slot, draw_slot, process_code), sin algoritmo ni hash() de Python en clave. Códigos fijos: {"climate": 8, "departures": 0, "flowers": 2, "foraging": 6, "nectar": 3, "patch_selection": 1, "pollination": 4, "regeneration": 9, "return": 7, "search": 5}. Crear un bloque una vez por evento y usar subslots estables por flor. Ramas de un proceso no desplazan otros procesos. Repetir clave reinicia bloque. Misma seed secuencial sola no garantiza CRN: la alineación del motor debe probarse después.
Todos usan exactamente K, restricciones, horizonte, simulador, distribuciones, parámetros y seeds iguales. Emparejar diferencias por (scenario,K,replication_id,seed); comparar configuraciones idénticas salvo ubicaciones. No mezclar calibración y evaluación sin declarar validación interna. Las direcciones no fijan ponderaciones de objetivos; número de parches es diagnóstico.

## Métricas comunes

| metric | definition | unit | direction |
| --- | --- | --- | --- |
| total_resource_obtained | Sum of resource delivered to all K colonies by successful returns within horizon; consumption on failed trips is not delivered | RU: config.resource_unit, pending calibration | maximize |
| mean_resource_per_hive | Total delivered / K, including zero-delivery colonies | RU per hive | maximize |
| min_resource_per_hive | Minimum cumulative delivered resource across exactly K colonies | RU per hive | maximize |
| mean_distance_m | Mean one-way point-to-point distance over initiated patch trips, including trips without return; undefined if none | m | minimize |
| total_distance_m | Sum of one-way distances over initiated patch trips; not round-trip or realized flight path; zero if no trips | m | minimize |
| p95_distance_m | 95th percentile of same one-way trip distances using linear quantile; undefined if no trips | m | minimize |
| competition_pressure | Fraction of foraging attempts with at least one other distinct colony active in the patch at foraging start; undefined if no attempts | fraction [0,1] | minimize |
| hive_balance_jain | (sum delivered_i)^2 / (K * sum delivered_i^2); includes zero-delivery hives; undefined if all zero | index [1/K,1] when defined | maximize |
| patches_used_count | Distinct patch_id with positive resource consumption during horizon; zero if none | count | report_only |

Sin viajes: distancia total y parches usados=0; distancia media/P95 y presión ausentes. Sin entrega: total/media/mínimo=0 sobre K colonias; Jain ausente si todas entregan cero. Distancias incluyen viajes iniciados sin retorno, son siempre de ida y no trayectoria real. Presión usa fracción de intentos con otra colonia activa, no densidad de polinizadores Dryad.

## Reutilización de Proyecto 1

| component | reusable | changes_needed |
| --- | --- | --- |
| departures — simulation/departures.py | partial | Reutilizar generar_salidas A/B; fijar el mismo método para todos. Calibrar intensidad por colonia/día y jornada; tratar cierres y continuidad entre días. |
| distance — simulation/distance.py | partial | Sustituir sortear_distancia Weibull por matriz geográfica. Adaptar metros/km y velocidad. tiempo_vuelo usa 2D/V; permitir distancia cero; retorno logístico no calibrado. |
| flowers visited — simulation/flowers.py | partial | Reutilizar Poisson/negbin y validaciones; ligar media al recurso del parche y limitar consumo compartido. No adoptar niveles baja/media/alta sin ajuste. |
| pollination — simulation/pollination.py | partial | Reutilizar Bernoulli como hipótesis opcional; p_success sin evidencia aquí. Visitas Dryad no validan polinización efectiva. |
| nectar — simulation/nectar.py | partial | Reutilizar suma Gamma y dominios; no heredar escala/unidad ml como observada. Definir conversión y conservación con R; separar consumido y entregado. |
| trip duration — simulation/trip_duration.py | partial | Reutilizar suma vuelo+búsqueda+forrajeo; estimar escalas y velocidad, adaptar distancia métrica y jornadas. Duración de observación Dryad no es duración de un viaje. |
| return model — simulation/return_model.py | partial | Reutilizar chequeo horario y Bernoulli; recalibrar logística y transición de colonia entre días. No inferir supervivencia de visitas observadas. |
| random generators — generators/ | yes_with_adapter | Reutilizar RNG explícito y transformaciones; PCG64 para CRN. LCG solo diagnóstico. Separar procesos/eventos: misma seed global no garantiza alineación bajo ramas diferentes. |

Environment sortea disponibilidad por viaje y simular_jornada reinicia una colonia de una jornada: necesitan adaptación multi-colmena/día/stock compartido. Validadores heredados con distancia estrictamente positiva deben permitir cero en Proyecto 2.

## Parámetros pendientes

| parameter | classification | requirement_or_pending_work |
| --- | --- | --- |
| K | scenario_parameter | Exactamente K sitios; entero entre 1 y número de candidatos; valor pendiente del diseño experimental |
| horizon / time_resolution | scenario_parameter | Fijos para comparación principal: 2017-07-18 a 2017-08-04, diaria |
| resource_unit / initial_resources | modeled | Unidad y stock por parche sin cuantificar; no copiar ml de Proyecto 1 ni multiplicar áreas por Dryad sin correspondencia |
| regeneration / overlap_policy | modeled | Sin parametrizar; renovación al cierre y tratamiento de áreas solapadas antes de asignar recursos |
| alpha / beta / distance_scale_m | scenario_parameter | Pendientes de sensibilidad; alpha>=0, beta>=0 y escala de distancia>0 |
| departures / day_minutes / active_foragers | modeled | Familia, intensidad y esfuerzo diario/por colonia pendientes de calibración |
| flowers / search / nectar / velocity | modeled | Familias reutilizables, parámetros y unidades por justificar; misma configuración para todos |
| return / pollination / colony_transition | modeled | Probabilidades y continuidad de colonia entre días no identificadas con estos TXT |
| seed bank / RNG schema / engine_version | scenario_parameter | Banco compartido, PCG64, claves de evento estables y versión congelada por comparación |

No adoptar automáticamente valores de config/base.yaml. Las pruebas con ese archivo y cantidades abstractas son fixtures, no parametrización de Oslo.

## Validación e intervalos

Datos actuales: geometrías/IDs/filtro/áreas, distancias no negativas, calendario y clasificación, reconstrucción de conteos/densidad Dryad. Helpers: K único/válido, balance sin sobreconsumo, RNG reproducible y bootstrap. Motor legado: prueba de misma seed con configuración sintética.
Pendientes: motor común, invariantes en toda corrida, continuidad diaria, consumo compartido, CRN entre decisiones y determinismo de simulate incluyendo permutaciones de sitios. No etiquetar estas pruebas como aprobadas antes de ejecutarlas. validation_report.csv conserva estados separados.
Comparación Dryad: flores/m² solo frente a un operador de observación compatible; R, néctar y composición de polen no son flores/m². Actividad requiere misma ventana, taxones, detección y esfuerzo; viajes/día no son individuos/min ni individuos únicos. La duración del muestreo no es duración de viaje. Sin coordenadas no hay validación parche/trap. Respetar agrupación por sitio y muestreo único floral.
Bootstrap reutilizable: bee_sim.project2.contract.bootstrap_ci, IC percentil 95%, 5000 por defecto, seed explícita. Para estrategias usar diferencias emparejadas por réplica; no tratar viajes/días como réplicas independientes. Rechaza ausencias, no produce inferencia simultánea o causal. Para datos observados remuestrear sitios/bloques según dependencia y diseño.
El siguiente trabajo es calibrar y validar antes de experimentos de ubicación. No se implementaron algoritmos, dashboard ni dinámica ecológica completa.
