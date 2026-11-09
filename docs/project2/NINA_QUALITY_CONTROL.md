# Control acotado de la capa numérica NINA

Fecha local: 8 de noviembre de 2026. Rama: `feature/project2-validacion-historica-oslo`.
Solo archivos nuevos. No se modifican motor, entradas, optimizadores, resultados
históricos ni auditoría previa. Cero simulaciones, búsquedas o instalaciones clasificadas.

## Dictamen

**NO APTO para ordenar instalaciones como de mayor/menor idoneidad ecológica.**
El acceso numérico es **APTO CON LIMITACIONES**, pero la dirección ecológica y la
relación exacta del archivo con el indicador publicado siguen sin acreditarse.
Se recomienda cerrar NINA como referencia complementaria. No continuar desarrollando
una clasificación sobre esta escala sin una aclaración de su productor.

Esto no significa que todo el GeoTIFF sea inválido. Los problemas de remuestreo y
muestreo de parques sí tienen explicación numérica; resolverlos no resuelve la semántica.

## Identidad, metodología y contradicción

| Campo | Evidencia confirmada |
| --- | --- |
| Nombre literal del catálogo | `Egnethet for pollinerede insekter  (NINA)` |
| Identificador | `15216100_pollinator_potentential_0301` |
| Nombre de dataset | `pollinator_potentential_0301` (ortografía original) |
| Proyecto / propietario | `nina-15216100` / NINA |
| Método / unidad | `modelled` / `n/a` |
| Año declarado | adquisición/contexto 2022; no acredita fechas de todas las entradas |
| Licencia declarada | CC-BY 4.0 |
| Fuente | https://s3-ext-1.nina.no/dms/maps/sources/192/pollinator_potentential_0301.tif |
| COG vinculado por catálogo | misma URL con sufijo `.cog` |

Fuentes primarias:

- [Catálogo localEA](https://s3-ext-1.nina.no/dms/maps/main/localEA/config.json):
  vincula directamente ambos archivos, pero su descripción relaciona valores bajos
  con mayor potencial y menor necesidad de plantar árboles; los altos con lo contrario.
- [Portal SPARE, apartado 2.3](https://ninanor.github.io/SPARE_project/layers.html):
  presenta la capa como idoneidad y disponibilidad temporal de recursos florales.
  No publica allí la fórmula que genera el archivo descargable.
- [Stange et al. 2017, DOI](https://doi.org/10.3897/oneeco.2.e14014): pp. 5–8,
  sección 2.2 y tabla 1. El ESTIMAP urbano usa valoraciones de coberturas, consulta
  experta y clasificación Sentinel-2; mayor puntuación representa mayor idoneidad.
  El resultado final descrito tiene celdas de 10 m y una corrección por proximidad
  a vías de tráfico. Esa metodología no es una especificación de este GeoTIFF de 1 m.

Se descargó el PDF del editor únicamente a caché ignorada; se revisó el texto de
pp. 5–8 y se inspeccionaron las páginas metodológicas renderizadas. SHA256:
`032fa2076d8bc9adc9ed66cc5a017822ce9e0adabfd6f9546baadf1dc6a3ce7d`.
HTTP, URLs y hashes de respuestas constan en `source_access.json`.

**No está confirmado** si la descripción del catálogo contiene un error, si se
publicó una transformación inversa de ESTIMAP o si es otro indicador relacionado.
No encontramos fórmula ni historial de procesamiento que resuelva esas alternativas.
Una cita común y un título parecido no demuestran identidad numérica.

Como comprobación exploratoria, 19,99 % de los valores nativos muestreados coincide
con las puntuaciones discretas de la tabla 1; con la hipótesis `H = 1 − 0.95 × R`
coincide 88,21 %. La hipótesis se planteó al observar valores modales compatibles
con una inversión y normalización. **No es una fórmula identificada ni validada**:
hay valores intermedios, correcciones originales y posibles transformaciones distintas.
No se aplica para producir una nueva capa, métricas ecológicas ni rankings.

## Muestreo reproducible y diferencias entre archivos

Se fijaron 16 ventanas en una cuadrícula sistemática 4×4 y ocho ventanas adicionales
dirigidas a extremos del overview. Son 24 ventanas de 64×64 píxeles COG, alineadas
a su nivel factor 8; se recuperó el entorno nativo con margen de interpolación.
`sample_manifest.csv` conserva filas, columnas, dimensiones y diseño. Las muestras
se leen por HTTP Range y quedan como NPZ en caché ignorada con hashes.
Los extremos dirigidos no constituyen una muestra aleatoria representativa del área.
Los totales siguientes cuentan valores por ventana, no una auditoría global del ráster.

| Archivo/nivel | CRS | Resolución de cuadrícula | nodata | Valores válidos muestreados | Rango en muestra | Fuera de 0–1 |
| --- | --- | --- | --- | ---: | --- | ---: |
| Original | EPSG:25832 | 1×1 m | −9999 | 103102 | 0 a 1 | 0 |
| COG completo | EPSG:3857 | 2,388657 unidades proyectadas | −9999 | 45672 | −0,117868 a 1,090353 | 1616 |
| Overview factor 8 | EPSG:3857 | 19,109257 unidades proyectadas | −9999 | 755 | −0,152281 a 1,110888 | 72 |

No interpretar la resolución Web Mercator como metros de terreno uniformes ni
el 1 m de cuadrícula nativa como resolución ecológica efectiva demostrada.
Nodata se excluye antes de calcular estadísticas. No se recortan valores a 0–1.

Se reproyectaron las muestras originales a la cuadrícula COG con cinco kernels.
La comparación usa exactamente los mismos **45555 píxeles válidos** para todos:

| Remuestreo probado | MAE contra COG |
| --- | ---: |
| Vecino más próximo | 0,009709 |
| Bilineal | 0,003640 |
| Cúbico | **0,000661** |
| Spline cúbico | 0,007960 |
| Lanczos | 0,002883 |

La inversión `1 − fuente` con reconstrucción cúbica arroja MAE **0,656152**.
El COG conserva estrechamente el sentido numérico del original; no aparece una
inversión entre esos dos archivos. El exceso de rango surge en la versión
reproyectada y es compatible con interpolación de kernels con sobreoscilación.
Es evidencia fuerte de remuestreo, **no identificación documental de la receta exacta**.

Para el overview se compararon cinco agregaciones de píxeles COG. Se descartaron
bordes con soporte incompleto y se usaron 166 celdas comunes: cúbico MAE 0,007713;
promedio 0,019235; vecino próximo 0,093115. No coincide exactamente con un promedio
simple. El kernel, los pasos intermedios y la versión usados por el proveedor no
están documentados. Usar `nearest` para leer un overview ya creado no deshace su
remuestreo anterior. La lectura anterior no inventó la escala fuera de rango.

## Parques: qué se midió y por qué faltaron 51

La auditoría anterior **no tomó un centroide por parque**: seleccionó todos los
píxeles del overview cuyo centro cae dentro del polígono (`all_touched=False`).
Es una muestra de la superficie según centros de celda; no una integración exacta
por fracción cubierta de cada píxel. No deben confundirse ambas reglas.

Se verificaron individualmente los 51 IDs contra el original de 1 m:

| Causa verificada | Parques | Interpretación |
| --- | ---: | --- |
| Píxeles nativos válidos con centros interiores; perdidos al reducir cuadrícula | 30 | Ausencia causada por muestreo reducido; superficies de 0,44 a 91,82 m² |
| Sin centros nativos interiores; sí hay píxeles válidos que tocan el fragmento | 19 | Fragmentos de 0,00035 a 0,64458 m²; asignar el píxel entero incorporaría entorno exterior |
| Dentro de extensión, pero todos los píxeles son nodata | 1 | Parque de 76892,76 m²; 76899 centros nativos, ninguno válido |
| Fuera de la extensión nativa | 1 | Ausencia de cobertura real del archivo |
| **Total** | **51** | No se imputan valores |

El parque enteramente nodata es `patch_941ca1ab497f4ce18f56f9d5cc1a4f6f_0_215`.
`missing_51_parks.csv` conserva ID, área, cobertura, conteos, causa y estadísticas
nativas cuando existen. Los 19 fragmentos no pasan a considerarse hábitat medido
por disponer de un píxel vecino. Nodata nunca equivale a idoneidad cero.

## Aptitud para evaluación externa y criterio de cierre

No hay impedimento técnico fundamental para consultar el original y agregarlo
espacialmente. Pero **no es defendible** comparar instalaciones como mejores o
peores mientras el mismo valor alto pueda interpretarse en sentidos contrarios.
La anomalía semántica afecta el signo de cualquier conclusión, no solo su precisión.

Incluso aclarada la escala, sería una referencia ambiental modelada: mayor
idoneidad puede señalar hábitat valioso para polinizadores silvestres y no implica
menor impacto al colocar colmenas. No mide competencia, capacidad de carga ni
recursos recolectados, y su contexto 2022 no reconstruye julio de 2017.

Se podría reabrir únicamente con la fórmula/historial que vincula el archivo al
indicador y confirma su dirección, o con un dataset corregido con procedencia
equivalente. Para cálculos futuros se preferiría el original y agregación con
cobertura/áreas métricas documentadas, sin optimizar sobre NINA retrospectivamente.
No se implementó ninguna de esas comparaciones ni se modificaron objetivos.

## Reproducción y alcance de verificación

Con las dependencias opcionales ya declaradas en `requirements-historical.txt`:

```powershell
.\.venv\Scripts\python.exe scripts/project2_nina_qc.py
.\.venv\Scripts\python.exe scripts/project2_nina_qc.py --summarize-cached
.\.venv\Scripts\python.exe -m unittest discover -s tests/project2 -p test_nina_qc.py -v
```

El primer comando necesita red y conserva identidad por ETag; si cambia la fuente
se detiene antes de reutilizar muestras. El segundo reconstruye resúmenes sin red
con las muestras cacheadas y CSV. La prueba de hashes se omite explícitamente si
la caché ignorada no está presente. Los CSV con evidencia y metadatos son nuevos
en `results/project2/nina_quality_control/`; no sustituyen los valores previos.
La integridad final de los archivos base y el alcance de pruebas se registran en
`verification.json` dentro de ese directorio. Aprobar estas pruebas no acredita
validez ecológica de NINA ni del simulador. El trabajo termina aquí.
