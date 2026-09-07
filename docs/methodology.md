# Metodología experimental

## 1. Propósito

La campaña estima el comportamiento del modelo de forrajeo y polinización bajo
12 configuraciones. Cada configuración representa una jornada de 600 minutos y
se repite 500 veces para describir la variabilidad entre jornadas.

## 2. Unidad de simulación

La unidad mínima es un viaje. Las oportunidades de salida se generan mediante
un proceso de Poisson. Si existe una forrajera disponible, el motor genera el
nivel del parche, la distancia, las flores visitadas, las polinizaciones, el
néctar, los tiempos de búsqueda y forrajeo y el retorno. Si no existe una abeja
disponible, la salida se registra como perdida.

Una réplica es una jornada completa. Un escenario es un conjunto de réplicas con
la misma configuración. La campaña contiene los siguientes escenarios:

- referencia;
- población baja y alta;
- disponibilidad floral baja y alta;
- distancia cercana y lejana;
- intensidad de salidas baja y alta;
- probabilidad de polinización baja y alta;
- combinación de baja disponibilidad y distancia lejana.

## 3. Control del azar

La configuración base utiliza el LCG implementado en el proyecto. En la versión
actual, las semillas de las réplicas se generan de forma dispersa a partir de una
semilla maestra y se guardan en `results/runs/semillas_campana.json`. El mismo
conjunto se reutiliza en los escenarios. Una campaña iniciada con una versión
anterior puede conservar semillas consecutivas; ese hecho debe declararse y no
puede corregirse cambiando los metadatos después de simular.

Usar la misma semilla no implica que dos escenarios consuman cada uniforme para
el mismo evento. Por ejemplo, fijar la disponibilidad floral evita un sorteo que
sí ocurre en BASE. Por eso los escenarios se comparan mediante sus distribuciones
agregadas y no viaje por viaje.

Cada configuración persistida registra la semilla realmente usada, el escenario,
el índice de réplica, el total de réplicas solicitado y la fecha UTC de creación.
Las campañas iniciadas con la versión anterior pueden recuperar esos metadatos
desde `semillas_campana.json` mediante `scripts/update_campaign_metadata.py`.
El mismo proceso agrega a los resúmenes las métricas temporales calculadas desde
los CSV, sin volver a simular ni alterar los registros por viaje.

## 4. Persistencia

Cada réplica produce tres archivos en `results/runs/`:

- `run_XXXX.csv`: una fila por viaje;
- `run_XXXX_config.yaml`: configuración y metadatos exactos;
- `run_XXXX_summary.json`: métricas agregadas de la jornada.

Los lectores de análisis también aceptan la disposición histórica
`results/campana/<escenario>/`, pero la carpeta plana es la disposición canónica.

## 5. Validación de generadores

Las variables continuas se contrastan mediante Kolmogorov-Smirnov y las
discretas mediante chi-cuadrado con agrupación de colas. También se comparan
media y varianza observadas con sus valores teóricos. El LCG se revisa mediante
momentos, KS y autocorrelaciones con retardos de 1 a 10.

La cadena Poisson-Bernoulli se valida mediante adelgazamiento: si
`F ~ Poisson(mu)` y `X | F ~ Binomial(F, p)`, entonces
`X ~ Poisson(mu*p)`.

## 6. Comparación de métodos

Los métodos A y B del proceso de salidas se ejecutan con el mismo horizonte,
intensidad y conjunto de semillas. Cada método se contrasta con el proceso
teórico y se comparan tiempo de ejecución y consumo de uniformes.

La equivalencia práctica se evalúa con una prueba TOST pareada y un margen
predefinido de ±1% del número teórico de salidas. El p-valor de una prueba de
diferencia se reporta como información complementaria, pero no se interpreta
como prueba de equivalencia.

## 7. Resumen de escenarios

Para cada métrica se calculan media, desviación estándar, error estándar e
intervalo de confianza aproximado del 95%. Las comparaciones se limitan a los
niveles configurados; no se generalizan a condiciones biológicas no calibradas.

La combinación de disponibilidad y distancia se interpreta tanto en escala
aditiva como multiplicativa. Debido a que la respuesta es un conteo no negativo,
una predicción aditiva negativa se considera evidencia de que esa escala no es
adecuada, no evidencia de que los factores se refuercen.

## 8. Alcance temporal de la polinización

El resumen distingue:

- polinización planificada en todos los viajes iniciados;
- polinización en viajes cuya duración cabe en la jornada;
- polinización en viajes con retorno exitoso.

El informe debe nombrar explícitamente cuál definición presenta. El modelo no
registra todavía el instante exacto de cada visita floral, por lo que no puede
determinar qué fracción de un viaje que cruza el horizonte ocurrió antes del
cierre.

## 9. Reproducción

Desde la raíz del repositorio:

```bash
python scripts/validate_generators.py --n 20000 --replicas 200
python scripts/run_experiment.py --campana --n-replicas 500
```

Después se ejecutan `notebooks/02_scenario_analysis.ipynb` y
`notebooks/03_final_figures.ipynb`. Ninguno de esos notebooks vuelve a ejecutar
la campaña.
