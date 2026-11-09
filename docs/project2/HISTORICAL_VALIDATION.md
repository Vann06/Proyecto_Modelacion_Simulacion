# Auditoría de viabilidad histórica: Dietz (2018), Oslo

**Dictamen: detenerse después de la auditoría; no habilitar todavía una simulación
histórica con ubicaciones supuestamente verificadas.** Rama de trabajo:
`feature/project2-validacion-historica-oslo`, creada desde la base limpia
`integracion/project2-comparacion-app`, commit `dff96a37056b668c48a40080d80783b4f0e817be`.
No se modifican motor, restricciones, aplicaciones ni resultados anteriores.
No hay commit, PR ni integración automática de este trabajo.

## 1. Fuente y recuperación reproducible

Fuente primaria: Sabrina Elisabeth Dietz (2018), *An assessment of optimal foraging
in honeybees through decoding of waggle dances in an urban landscape*.
[PDF de ByBi](https://bybi.no/wp-content/uploads/2018/12/Sabrinas-Master-thesis-181210.pdf).
Consulta: 8 de noviembre de 2026, Guatemala. Versión de 62 páginas, SHA256
`f540f7ade82453d54de2a2e94942cca2f64e316941f4f6ba02a01420b662975f`.
La autoría se toma de la portada, no de los metadatos de plantilla del PDF.

Se recuperaron las diez tablas del anexo, páginas 50–59. **Dos motores de extracción
independientes, pypdf y PyMuPDF, coinciden en todas las celdas de 506 filas**.
Se cotejaron visualmente 20 filas seleccionadas y sus campos contra imágenes
renderizadas de las páginas 50, 53, 54, 58 y 59, incluyendo encabezados, coordenadas,
anomalías y límites de tablas. No se afirma inspección visual de cada celda.
Fixtures: `data/project2/historical_manual_checks.json`; evidencia:
`manual_verification.csv`, `source_audit.json` y pruebas de extracción.

La página 2 autoriza acceso abierto en Brage y préstamo bibliotecario, pero no se
identificó una licencia CC ni permiso explícito para redistribuir el PDF. Acceso
abierto no se interpreta como CC0 de Dryad. **PDF, texto completo, imágenes de
inspección y rásteres grandes quedan solo en `.build/historical/`, ignorado por Git**.
Se conservan datos factuales derivados, atribución y huella; antes de publicar los
registros derivados, el equipo debe revisar las condiciones de reutilización.

## 2. Inventario y problemas conservados

| Colonia | Registros recuperados | Distancias no negativas, todo el período | Fechas con danzas | Dentro 18/07–04/08 | Con reloj válido en ventana |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bygdøy | 211 | 210 | 23 | 87 | 86 |
| Ullevål 1 | 190 | 190 | 24 | 97 | 97 |
| Ullevål 2 | 105 | 105 | 17 | 32 | 32 |
| Total | **506** | **505** | **28 fechas distintas entre colonias** | **216** | **215** |

Período del anexo: Bygdøy y Ullevål 1, 01/07–14/08/**2017**; Ullevål 2,
01/07–04/08/2017. Los métodos (p. 15), el resumen y todas las filas concuerdan en
2017. La sección de resultados (p. 27) escribe 2018: se registra la contradicción
sin cambiar las fechas de los registros. Hay 290 filas fuera de nuestra ventana;
la distancia negativa está entre ellas. No se extrapolan esos datos a días sin filmación.

Se mantienen explícitamente:

- Bygdøy, fila 31: distancia **−2,9 m**. No convertirla a cero ni a valor absoluto.
  Se excluye del resumen de distancias no negativas, sin eliminar la fila fuente.
- Bygdøy, filas 164 y 180: segundos **69 y 86**. No normalizar llevando minutos;
  el timestamp es inválido. Solo fila 180 afecta la ventana principal.
- Cinco discrepancias entre prefijo de `dance.id` y `movie ID`; cuatro filas
  participan en dos IDs de danza duplicados en Bygdøy. No renumerar identificadores.
  `record_id` es una clave **derivada** de colonia y fila del anexo, no un ID de abeja.
- Las danzas no son abejas independientes identificadas: podrían repetir individuos.

Los filtros son separados: un problema de ID o de reloj no invalida automáticamente
una distancia descriptiva correctamente transcrita, pero sí limita la vinculación
temporal. CSV completo: `historical_foraging.csv`. `inclusion_exclusion.csv` conserva
las 506 decisiones y `flagged_records.csv` muestra registros que necesitan atención.

### Variables y unidades

Distancia puntual del anexo: metros, según encabezado de la tabla de resultados.
Duración media del waggle run: segundos; dirección media y azimut: grados;
`heading.rad`: radianes; fecha y reloj: componentes escritos. `easting/northing`
son coordenadas proyectadas con **CRS/datum no declarado**. La consistencia de
vectores sugiere unidades compatibles con metros, pero no determina el CRS.
Los números de película/danza/fila son identificadores, no conteos de viajes ni
mediciones de néctar, polen o individuos únicos.

## 3. Qué distancia representa la tesis

Los vídeos fueron recogidos en 28 días de tiempo favorable (>15 °C, sin viento
fuerte/lluvia), 1–2 horas por colmena y día (p. 15), no continuamente 600 minutos.
Se midieron duración y ángulo de las danzas; se añadió azimut solar. El estudio
usó calibración bayesiana de Sussex y 1 000 distancias/direcciones simuladas por
danza, con dispersión direccional von Mises κ=24,9 (pp. 17–19). El análisis no
distingue danzas para néctar y polen. Los puntos del anexo **no son GPS ni las
distribuciones posteriores completas**. No se recuperaron muestras MCMC, vídeos
ni superficies ráster de probabilidad como archivos anexos al PDF.

Los conteos publicados (211/190/105) se reproducen. Las medias publicadas de
distribuciones son 688,39 / 490,95 / 425,27 m. Las medias de la columna puntual
del anexo, descartando la distancia negativa, son 681,76 / 471,54 / 403,08 m.
Estos son estimandos distintos: **no se presentan sus diferencias como error de
extracción, ni como MAE/RMSE del simulador**. `published_summary_check.csv`
registra ambos, sus tamaños muestrales y los intervalos publicados por separado.

### Distancias puntuales dentro de la ventana principal

| Colonia | n | Fechas | Media (m) | Mediana (m) | P95 (m) | >3 km |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Bygdøy | 87 | 9 | 783,50 | 672,10 | 1 719,61 | 0/87 |
| Ullevål 1 | 97 | 10 | 629,47 | 372,10 | 2 802,10 | **3/97 = 3,09%** |
| Ullevål 2 | 32 | 8 | 372,29 | 272,10 | 1 049,58 | 0/32 |

El máximo puntual en ventana es 4 205,4 m (Ullevål 1). Un radio rígido de 3 km
excluiría esos tres destinos puntuales si se confirmara su correspondencia espacial;
no cubre toda la cola observada. Cero casos en otra colonia no prueba un límite
biológico de 3 km. Las distribuciones de calibración tienen incertidumbre adicional.

IC descriptivos de la media en `observed_distances.csv`: bootstrap de **fechas de
filmación** (2 000, semilla 20261108), manteniendo juntas las danzas de un día.
No se tratan las 1 000 muestras bayesianas como 1 000 danzas independientes ni las
fechas de tiempo favorable como muestra aleatoria de todo el período. Estos IC
no incluyen la incertidumbre de la calibración de Sussex ni error de localización.
La semilla de bootstrap no es un banco de semillas de simulación histórica.

## 4. Auditoría espacial y dictamen

El PDF localiza cualitativamente una colmena en Bygdøy y dos en Sogn Hagekoloni,
Ullevål (pp. 14–16); la Figura 1 no tiene rejilla georreferenciada. Se inspeccionaron
también los mapas de pp. 60–62. No se identifican CRS/datum, tabla de GPS de las
colmenas, archivos geográficos adjuntos ni diccionarios de georreferenciación GeoPDF.

Como diagnóstico se invirtió la ecuación de vector descrita en p. 19:

`origen_x = easting − distance × sin(heading.rad)`

`origen_y = northing − distance × cos(heading.rad)`

| Colonia | Mediana x implícita | Mediana y implícita | Filas consistentes a 0,1 unidades |
| --- | ---: | ---: | ---: |
| Bygdøy | 594 294,00 | 6 642 591,00 | 209/211 |
| Ullevål 1 | 596 642,00 | 6 646 904,01 | 181/190 |
| Ullevål 2 | 596 642,00 | 6 646 901,00 | 103/105 |

No son posiciones topográficas verificadas. Algunos vectores cortos no vuelven
al mismo origen; esto podría relacionarse con transformaciones de distancias
negativas o inconsistencias de procesamiento. No se corrigen automáticamente.
Las dos medianas de Ullevål distan **3,010 unidades**, mientras el texto dice
aproximadamente **0,2 m** entre colmenas. La incertidumbre de una danza es mayor
que esa diferencia, pero no autoriza inventar dos ubicaciones exactas para el motor.

UTM 32N es una hipótesis compatible con el contexto geográfico. Se probaron de
forma **condicional**, sin declararlos CRS observado, EPSG:25832 y EPSG:32632,
transformados a EPSG:25833. Sus resultados son casi idénticos, pero esa coincidencia
no confirma qué datum/CRS utilizó Dietz. Que otro ráster NINA de 2022 use 25832
tampoco certifica retrospectivamente el CRS del anexo de 2017.

### Cobertura de parques: diagnóstico condicionado a esa hipótesis

Regla: centro del punto estimado cubierto por la unión de los 737 polígonos
originales, incluyendo bordes. No se usan los 680 parches exclusivos para cambiar
la definición de parque. EPSG:25832 supuesto arroja:

| Colonia | Centros cubiertos | Fuera del catálogo | Mediana hasta parque (m), condicional |
| --- | ---: | ---: | ---: |
| Bygdøy | 9/87 = 10,34% | 89,66% | 184,34 |
| Ullevål 1 | 0/97 = 0% | 100% | 268,35 |
| Ullevål 2 | 1/32 = 3,13% | 96,88% | 191,31 |

**No son porcentajes certificados de destinos reales de Oslo**: dependen de un
CRS no confirmado y de puntos decodificados, no de nubes de probabilidad.
`park_coverage_conditional.csv` presenta ambas hipótesis. Una tolerancia analítica
de 25 m hasta parque se reporta aparte; no es un IC espacial de danzas.

El indicio merece revisión del catálogo: el estudio describe jardines residenciales,
campos agrícolas y jardines de Sogn (pp. 14, 35, 41). Nuestros parques son áreas
administradas por el municipio, no todas las fuentes florales privadas. **Fuera de
parque no significa ausencia de flores**, y no se clasificaron usos del suelo
individuales sin una capa adicional. Las geometrías actuales/2018 tampoco prueban
el estado exacto de cada superficie en 2017.

### Solapamiento

El estudio calcula probabilidad de visita en celdas de 25×25 m a partir de nubes
de 1 000 realizaciones por danza y combina probabilidades de no-visita (p. 19).
Su Jaccard (p. 25/32) es 0,50 global y 0,39 dentro del percentil 50 de distancias.
No están las superficies originales ni su rejilla/umbral operativo completo.
Jaccard de celdas ocupadas por puntos del anexo sería **otro indicador**, y tampoco
equivale a `competition_pressure`. Se guardan los valores publicados y la razón
de no reproducción en `overlap_comparability.csv`, sin crear un falso Jaccard simulado.

### Comparaciones que permite esta auditoría

| Comparación | Viabilidad actual |
| --- | --- |
| Conteos, fechas, errores de reloj/ID y distribuciones puntuales por colonia | Directamente realizable |
| Diferenciar columna puntual y distribuciones publicadas | Directamente realizable; no igualdad esperada |
| Orígenes por inversión de vectores y cobertura parque bajo UTM32 | Diagnóstico con hipótesis explícita; no inicialización verificada |
| Simular las tres ubicaciones históricas verificadas | **No habilitado**: falta confirmar CRS/datum y coordenadas originales |
| Comparar distancias observadas con viajes históricos simulados | Pendiente del escenario y proceso de observación |
| Reproducir Jaccard de probabilidad publicado | No con los archivos recuperados |
| Validar RU, polinización efectiva o impacto en abejas silvestres | No medido por este experimento |

**Se aplica el punto de control solicitado.** No se modifica el motor ni se
implementa adaptador histórico, no se ejecutan 30 simulaciones, no se genera banco
de seeds y no se calcula una tabla ficticia observado/simulado. El comando
`simulate` rechaza continuar con `HistoricalFeasibilityError`.

Una futura interfaz separada tendrá que aceptar ubicaciones históricas documentadas
sin relajar el catálogo de optimización. Las danzas anuncian recursos rentables
tras retornos; `returned & resource_delivered>0` sería una submuestra candidata
más pertinente que todas las oportunidades, pero todavía faltaría modelar selección
de danza, esfuerzo horario y rentabilidad/detección. No se emparejan danzas con
viajes simulados individuales ni se considera validado NSGA-II por este contraste.

## 5. NINA: se encontró acceso numérico oficial adicional

La inspección previa del ArcGIS TilesOnly sigue siendo correcta: `query/identify`
devuelven 404, exportación de tiles deshabilitada, ítem sin recursos descargables.
**No se sustituye ese servicio silenciosamente**. La documentación SPARE enlaza
otro catálogo oficial: [Database](https://ninanor.github.io/SPARE_project/database.html)
→ [localEA](https://maps.nina.no/localEA) → [configuración pública](https://s3-ext-1.nina.no/dms/maps/main/localEA/config.json).

Este catálogo ofrece `pollinator_potentential_0301` como GeoTIFF/COG y declara
**CC-BY 4.0, NINA, período de adquisición 2022**. Atribución y descripción quedan
en `nina_catalog_item.json`. El TIFF original mide 1 635 594 178 bytes, tiene
**EPSG:25832, píxel 1×1 m, float32 y nodata −9999**. El COG oficial está reproyectado
a **EPSG:3857**, píxel 2,388657 unidades proyectadas y niveles reducidos 2–128.
Los metros de Web Mercator no son distancias de terreno de escala uniforme.

Se lee por HTTP Range el nivel reducido publicado **factor 8**, sin descargar el
TIFF completo. La cuadrícula analizada tiene píxeles de **19,109257 unidades
EPSG:3857** (no 19 m exactos sobre terreno). Se conserva su hash, URL, ETag y fecha
de modificación. El origen de remuestreo de los overviews no está documentado;
las medias por parque son **aproximadas**, no estadísticas zonales exactas de 1 m.
Se incluyen centros de píxel dentro de cada polígono; no se imputan parques pequeños.

Resultado: **686/737** parques tienen valores numéricos; 50 no contienen centros
válidos al nivel usado y uno está fuera de la extensión. La correlación de Spearman
descriptiva del índice bruto medio con la fracción sintética de área exclusiva es
**−0,0948**, sin p-valor ni interpretación causal: los polígonos pueden solaparse
y área total no es calidad floral media.

Dos problemas impiden usarlo directamente como calidad/RU:

- La descripción asocia valores altos con menor potencial y mayor demanda de
  plantación, mientras título/leyenda hablan de aptitud creciente. Se retiene
  **índice bruto con sentido pendiente de aclarar**, sin invertirlo arbitrariamente.
- En las muestras del overview sobre parques hay valores de **−0,1118 a 1,0985**;
  349 parques contienen algún valor fuera del rango nominal 0–1. No se recortan.
  Podría intervenir remuestreo/procesamiento, pero no se afirma una causa no verificada.

No se convierte idoneidad a néctar, flores ni RU. No se cruzan danzas históricas
con ese índice como si CRS/época fueran confirmados: 2022 no es una medición de
recursos de 2017. Para análisis fino hace falta resolver semántica/rango y usar
resolución nativa o un muestreo zonal de precisión conocida.

## 6. Evidencia complementaria y recomendaciones

Dryad se reutiliza por referencia, sin repetirlo: `REAL_WORLD_VALIDATION.md` y
`results/project2/scientific_validation/empirical_errors.csv`. Sus MAE/RMSE son de
referentes de flores/actividad ajustados fuera de muestra por sitio, no del motor
de colmenas. Temperatura es contexto observado/estrato de ese referente, no una
respuesta térmica calibrada del simulador.

La tesis describe colonias de aproximadamente 5 000 obreras (p. 14) y otras tres
colmenas de unas 60 000 abejas en Sogn (p. 40), más polinizadores no observados.
El motor agregado solo representa competencia de nuestras colonias y no posee esa
población externa ni selección de danzas; estas diferencias impiden extrapolar
su presión sintética a competencia ecológica real.

`findings_recommendations.csv` presenta hallazgo, evidencia, causa posible,
implicación, cambio recomendado y prioridad. Conservar reglas reproducibles,
separación entre recurso/colocación, balance, unidades y CRN. Proponer, no implementar:
confirmar geometrías históricas, evaluar cobertura de jardines privados, revisar
radio y selección de parches con datos, desarrollar operador de observación y
considerar reclutamiento/memoria y presión externa si existe evidencia suficiente.

**No hace falta repetir NSGA-II para cerrar esta auditoría.** Las conclusiones
originales siguen siendo comparaciones dentro de su modelo y escenario. Si después
se cambia el paisaje, radio, recurso o reglas, deberá crearse otra identidad y
reevaluar todos los métodos con un banco de seeds histórico independiente; nunca
reescribir las 70 réplicas originales ni afirmar mejora real de Oslo.

## 7. Reproducción y entregables

Desde la raíz del checkout:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-historical.txt
.\.venv\Scripts\python.exe scripts/project2_historical_validation.py audit --download-source
.\.venv\Scripts\python.exe scripts/project2_nina_numeric_audit.py
.\.venv\Scripts\python.exe -m unittest discover -s tests/project2 -p test_historical_validation.py -v
```

La descarga del PDF verifica su huella y lo deja en caché ignorada. Una fuente
distinta exige revisar extracción; no se acepta automáticamente. Las lecturas
NINA conservan identidad del proveedor y reutilizan el overview en caché si coincide.
El notebook `09_historical_data_audit.ipynb` lee evidencia exportada y puede comprobar
la extracción si el PDF está disponible. Se conserva `09_scientific_evidence.ipynb`.
No se crea un notebook 10 con una supuesta validación todavía no habilitada.

El módulo se ubica en `src/bee_sim/analysis/project2_historical_audit.py`, en lugar
de la ruta sugerida dentro de `project2/`, porque `_engine_hash()` incluye todos
los `.py` de ese directorio: añadir allí una auditoría cambiaría la identidad de
los experimentos aunque no se modificaran reglas. La protección de restricciones
permanece en el motor original.

Archivos de datos: `data/project2/processed/historical_{foraging,hives}.csv`.
Resultados: `results/project2/historical_validation/`, con tablas de inventario,
inclusión/exclusión, distancias, resúmenes publicados, hipótesis geográficas,
NINA, dictamen, limitaciones y metadatos. Los campos de colmenas inferidas tienen
`placement_allowed_for_historical_simulation=False` y CRS `UNCONFIRMED`.

Siguiente revisión humana esencial: obtener del estudio el CRS/datum, coordenadas
originales/GPS o proyecto R/QGIS, aclarar separación de colmenas y registros
anómalos, solicitar superficies de probabilidad y condiciones de reutilización.
No se enviaron mensajes a terceros. Solo después se diseña el escenario K=3,
se registran nuevas seeds y se decide una comparación observacional defendible.
