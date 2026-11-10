# Contraste empírico de Oslo y límites de validación

## Pregunta y procedencia

¿Qué tan bien se pueden representar las observaciones de flores y actividad con
referentes estadísticos simples, y qué falta para validar el simulador de colmenas?
Se usan exclusivamente los TXT originales de [Dryad, Davey (2023)](https://doi.org/10.5061/dryad.9kd51c5qk),
conservados sin cambios. La publicación describe inventarios florales del 18 de
julio al 4 de agosto de 2017. El archivo de visitas llega al 10 de agosto.
Los hashes completos están en `results/project2/scientific_validation/metadata.json`.

| Concepto | Procedencia | Unidad y alcance |
| --- | --- | --- |
| Flores | 593 filas, 100 traps; 115 etiquetas vegetales | Conteo escrito; densidad derivada flores/m² |
| Visitas/actividad | 1 297 filas, 101 identificadores, 29 etiquetas de polinizador | Suma de registros volando/sentados; no individuos únicos ni polinización |
| Geografía | GIS de parques y restricciones | 737 polígonos; 375 IDs candidatos, 351 coordenadas únicas |
| Recurso | Reparto sintético por área exclusiva | synthetic_RU, sin equivalencia biológica |
| Viajes | Motor estocástico agregado | Viajes iniciados por colonia/día; distancias de ida en m |

La referencia dice 100 localidades, pero el TXT de visitas tiene 101 IDs: se
reporta la discrepancia, sin eliminar el identificador adicional por conveniencia.
En 577 filas florales el año no está escrito: se contextualiza a 2017 con la
publicación, conservando una bandera explícita. No es un año observado en el TXT.
Las campañas de GIS tienen fechas distintas: geografía real no implica reconstrucción
exacta del paisaje ni restricciones legales de 2017.

## Operador de observación: no identificable con estos archivos

No hay tabla trap → geometría GIS, población finita de obreras, detectabilidad,
observación de retornos por colmena ni relación flores → RU. Una flor no tiene
rendimiento constante demostrado, y una observación de abeja no es necesariamente
un viaje distinto. Por ello **no se implementa una conversión del motor a Dryad**.

| Métrica equivalente | Referencia real | Motor base | Motor con ubicaciones mejoradas |
| --- | --- | --- | --- |
| Flores/m² de transecto | Disponible | No produce esta unidad | No produce esta unidad |
| Conteos registrados/min de sesión candidata | Disponible con restricciones | No modela detección ni este esfuerzo | No modela detección ni este esfuerzo |
| Recurso entregado en synthetic_RU | No medido | Simulado | Simulado |
| Polinización efectiva | No medida | No implementada | No implementada |

No se rellena esta tabla con números incompatibles para aparentar cumplimiento.
El criterio 7 de la rúbrica queda parcialmente pendiente respecto del **motor**.

## Experimento empírico independiente y reproducible

`python scripts/project2_scientific_validation.py` crea referentes estadísticos
separados de `simulate`. No modifica parámetros del motor ni instala colmenas.

1. Leer UTF-8/CP1252 sin reemplazar caracteres y recortar espacios. Conservar
   duplicados exactos (4 florales, 6 de visitas): no sabemos si son mediciones
   distintas. Esto es una limitación, no se afirma independencia de filas.
2. Flores: agrupar trap/fecha, sumar conteos y dividir por ancho_cm/100 × largo_m,
   contando el área una vez. Exigir dimensiones consistentes y todos los conteos
   no negativos/no ausentes. Quedan 99 unidades y se excluye una incompleta.
   Se asume que las filas taxonómicas comparten el transecto; no se extrapola al parque.
3. Actividad: clave trap/fecha/inicio/fin/observadores, suma volando+sentados;
   duración estrictamente positiva, conteos completos y temperatura única.
   Se rechazan sesiones solapadas dentro de trap/fecha. De 238 sesiones candidatas,
   216 son elegibles y 22 se excluyen. No hay solapamientos en esta reconstrucción.
   Se trabaja con todos los taxones registrados, no solo Apis. El indicador es
   **conteos registrados por minuto de sesión candidata**, no tasa de visitas floral
   biológicamente validada ni abundancia individual única.
4. Separación 80/20 por trap, semilla 20261107: 79 sitios de ajuste y 20 de evaluación
   para cada referente. Las sesiones del mismo trap nunca se reparten entre ambos.
   Se guardan IDs, split, observaciones y predicciones; no se ajusta con evaluación.
5. Referencia base: media global de densidad o actividad en ajuste. Alternativa:
   media por mes para flora y por bins de temperatura fijados a priori (≤15, 15–20,
   >20 °C) para actividad. Estratos no vistos usan explícitamente la media global.
   Son modelos empíricos simples; no son una mejora del motor ecológico.
6. Treinta ajustes bootstrap por sitios de entrenamiento con seeds 31–60 del banco
   registran incertidumbre de ajuste, no simulaciones independientes del mundo.
   MAE/RMSE de predicciones puntuales usan todos los sitios de ajuste; IC percentiles
   de 2 000 bootstrap por sitios de evaluación, seed 17. Cada sitio pesa igual;
   varias sesiones no convierten un sitio en múltiples réplicas independientes.
   Los IC son condicionales al ajuste y al split; no incluyen todo el error de diseño.

| Referente | MAE base | MAE estratificada | RMSE base | RMSE estratificada | Unidad |
| --- | ---: | ---: | ---: | ---: | --- |
| Flores | 10,227 | 11,106 | 11,788 | 12,701 | flores/m² |
| Actividad | 0,9251 | 0,8425 | 1,1266 | 1,0554 | conteos registrados/min |

Estratificar por mes **empeora** la predicción floral en estos sitios excluidos.
Los bins de temperatura reducen los errores puntuales de actividad en este split;
no prueban causalidad, una respuesta térmica calibrada ni mejora universal.
Los IC, dispersión, 30 réplicas y gráficos se conservan en el directorio de evidencia.
Las observaciones sin muestreo no se interpretan como ceros.

## Cómo completar la validación del motor

Conseguir la correspondencia espacial trap/parque, esfuerzo y taxones consistentes,
conteos de visitas por flor/intervalo, colonia/población y observaciones de viajes.
Elegir un proceso de observación con detección y reavistamiento; medir polen/néctar
si se desean esas unidades. Separar sitios/tiempos nuevos antes de calibrar.
Entonces ajustar parámetros con entrenamiento y evaluar base/intervención en
unidades observadas con al menos 30 seeds y errores agrupados por sitio.
Hasta entonces no usar Dryad para multiplicar el área total de Oslo por una densidad
muestral ni afirmar validación de ubicaciones, polinización o capacidad de carga.
