# Revisión de integración

## Preservación

Se creó `integracion/project2-comparacion-app` desde `proyecto2-urban-optimization`
(`e534b1c`) en un worktree separado. Se incorporaron mediante merges las ramas
`origin/RANDOM` (`8f55264`), `origin/feature/GREEDY` (`29a5537`) y
`origin/feature/NGSA-II` (`1a67412`). Se conservan los resultados y el notebook
`06.2_ngsaii_implementation.ipynb` originales. El árbol de trabajo original y sus
cambios locales no forman parte de esta integración.

## Hallazgos corregidos

1. **Tiempo del motor.** La configuración se deserializaba miles de veces por
   corrida y los contadores de competencia recorrían los parches en Python.
   Ahora se obtiene una copia de parámetros por corrida y se usa una matriz de
   actividad NumPy. Se conserva orden de eventos, RNG y reglas. La versión pasa
   de 1.1.0 a 1.1.1 para hacer visible el cambio de motor.
   En una corrida perfilada idéntica: 2,517 s frente a 0,505 s (4,99 veces).
   Se verificó igualdad exacta de métricas, viajes, eventos, recursos y por-colmena
   contra la referencia anterior. No equivale a medir una búsqueda completa nueva.
2. **Costo NSGA-II.** El historial registra 75 240 simulaciones, 2 508 instalaciones
   y 6,383 h. La configuración 50 individuos × 51 poblaciones × 30 réplicas
   permite hasta 76 500 simulaciones antes de descuentos por caché. El costo
   no es únicamente un fallo: combina muchos experimentos estocásticos.
   Se agregó `--dry-run`, presupuesto explícito y cuatro trabajadores por defecto.
3. **Caché parcial.** Una instalación evaluada con menos réplicas no debe darse
   por completa al aumentar el presupuesto de réplicas. Se completan solo seeds
   faltantes, se canonicaliza el orden de IDs y se comprueba motor/config/datos.
   Logs con última línea interrumpida se recuperan con respaldo de los bytes.
4. **Separación de cohortes.** La evaluación de un frente verifica su identidad y
   no escribe sobre el CSV histórico. Nuevas búsquedas usan otra carpeta. El
   frente 1.1.0 no debe presentarse como búsqueda ejecutada con 1.1.1.
5. **Portabilidad Windows.** Los CSV procesados requieren LF porque sus hashes
   son de bytes crudos. Se respetó `.gitattributes` ya añadido por NSGA-II; la
   normalización local no cambia contenido semántico ni inventa datos.

## Comparación de resultados existentes

Los tres CSV originales comparten configuración, motor, datos, contrato, K,
escenario y unidades. Se comprueba correspondencia entre réplica y banco de seeds.
Solo se comparan réplicas 31–100. RANDOM aporta 30 instalaciones, GREEDY una y
NSGA-II 49 soluciones. La alternativa ilustrativa `pareto_047` se elige con medias
de búsqueda congeladas por distancia normalizada al ideal, con pesos iguales.
No se escoge usando el mejor desempeño reservado.

RANDOM se promedia entre instalaciones por seed. Los IC bootstrap y diferencias
pareadas usan 70 seeds comunes, no 2 100 réplicas independientes. Son intervalos
puntuales condicionales a instalaciones fijas; no capturan incertidumbre de otra
selección RANDOM o búsqueda NSGA-II. Los autores ya habían inspeccionado el
holdout, así que las conclusiones son descriptivas, no confirmatorias.

Hay 375 IDs candidatos pero 351 coordenadas únicas. El frente contiene 49 IDs de
solución y 32 conjuntos de coordenadas distintos; se conservan ambos conteos y
la app deduplica únicamente la presentación del frente. No se cambia
silenciosamente la factibilidad del contrato ni se descartan filas históricas.

## App y siguientes pasos

La comparación archivada y los experimentos interactivos están separados por
identidad. Todos los escenarios nuevos llaman al mismo `simulate`; RANDOM y
GREEDY proponen ubicaciones, mientras NSGA-II usa ubicaciones del frente guardado.
Las posiciones de viajes se interpolan solo para dibujar; no entran al motor.
El color de recursos usa consumo registrado y regeneración al cierre del día.
La simplificación de polígonos es solo visual, no modifica distancias ni recursos.

Antes de afirmar resultados ecológicos: calibrar recursos por área, regeneración,
demanda, tasas de viajes y forrajeo, alpha/beta, velocidades y relación con clima.
Dryad mide flores/visitas con otro esfuerzo y unidades; no demuestra equivalencia
con RU, polen, néctar ni polinización efectiva. Falta sensibilidad, varias semillas
de optimizador, un conjunto nuevo de validación y una política de colocalización.
