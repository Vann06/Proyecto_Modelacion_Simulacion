# Supuestos del modelo

Parámetros y decisiones que **no provienen de datos observados**. Se listan aquí
para que el informe pueda declararlos como tales y para que, si más adelante se
consiguen datos de un apiario, se sepa exactamente qué recalibrar.

Cada uno aparece marcado con un comentario `SUPUESTO` en `config/base.yaml`.

---

## 1. Los tres niveles de disponibilidad floral

Nueve valores sin fuente. El nivel fija a la vez tres parámetros:

| Nivel | `mu_flowers` | `search_scale` | `nectar_scale` |
|---|---|---|---|
| baja | 4.0 | 2.5 | 0.020 |
| media | 8.0 | 1.2 | 0.033 |
| alta | 14.0 | 0.7 | 0.045 |

**Lo defendible es la estructura, no los números.** Que un parche pobre tenga
menos flores, menos néctar por flor y además cueste más encontrarlo es una
hipótesis razonable sobre cómo se distribuyen los recursos. Que sean exactamente
4, 8 y 14 flores esperadas no lo es.

Nótese que `search_scale` va en dirección contraria a las otras dos. Esa
inversión es deliberada y es lo que hace que la escasez tenga un costo temporal
además de un costo de rendimiento.

## 2. La forma de la Gamma del tiempo de búsqueda

`foraging.search_shape = 2.5`. Sin fuente. Se eligió mayor que 1 para que la
densidad tenga moda distinta de cero, es decir, para que encontrar el parche de
forma instantánea sea improbable.

## 3. La velocidad de vuelo es constante

`foraging.velocity_km_min = 0.33`, unos 20 km/h. El valor es de orden razonable
para una abeja melífera, pero tratarlo como constante es una simplificación: no
se modela viento, carga ni fatiga.

## 4. Los dos parámetros de la logística de retorno

`return.sensitivity = 3.0` y `return.midpoint_km = 4.0`. Ninguno proviene de
calibración biológica. La función misma es una construcción del modelo.

El valor de `sensitivity` sí tiene ahora un argumento cuantitativo detrás
(decisión D-11): con el valor anterior de 1.2, la colonia perdía el 96% de sus
forrajeras en una sola jornada, porque cada abeja alcanza a hacer unos 41 viajes
y la probabilidad de sobrevivir a todos era 0.9466^41 = 0.105. Subir la
sensibilidad concentra el riesgo alrededor de `d0` y deja de castigar los viajes
cortos.

**Interpretación que debe acompañar a este supuesto:** el no retorno se reporta
como "la abeja no regresó dentro de la jornada simulada", no como mortalidad.

## 5. La distancia y la disponibilidad floral son independientes

El modelo las sortea por separado: un parche lejano no tiene más ni menos
probabilidad de ser rico. En la realidad es plausible que exista correlación,
porque una abeja difícilmente vuela tres kilómetros hacia un parche pobre.

El proyecto no modela esa correlación y en su lugar la fuerza por escenario: eso
es exactamente lo que hace COMBINADO, que junta baja disponibilidad con mayor
distancia.

## 6. La elección de la Weibull para la distancia

`foraging.distance.model = weibull`, forma 2.0. La justificación es pragmática y
no mecanística: Gamma, Lognormal y Weibull cumplen igual los requisitos de forma
(positiva, asimétrica a la derecha, moda distinta de cero), y se eligió Weibull
porque es la única de las tres con acumulada invertible en forma cerrada
(decisión D-05).

La forma 2.0 se mantiene fija en los tres escenarios de distancia; lo que el
escenario mueve es la escala.

## 7. El parche floral es un punto

No hay mapa. Un parche tiene distancia pero no coordenadas ni dirección, y dos
abejas nunca compiten por el mismo parche. El movimiento entre flores dentro del
parche existe como tiempo, no como kilómetros.

## 8. La asignación de forrajeras es determinista

Se toma la primera abeja disponible, no una al azar. Sortearla consumiría
números aleatorios sin agregar realismo y dificultaría reproducir una corrida
paso a paso.

## 9. El número de réplicas

500 por escenario, 6,000 en total para los 12 escenarios. La configuración base
y la campaña final fijan explícitamente 500, valor elegido tras medir el costo.
Medido el costo en 0.25 s por réplica, se optó
por 500 porque el intervalo de confianza de la media ya resulta suficientemente
angosto (ver notebook 02, sección 6); subir a mil lo estrecharía en un factor de
1.41 a cambio de duplicar el tiempo y el espacio en disco.

---

## Lo que NO es un supuesto

Conviene distinguirlo en la discusión del informe, porque son los resultados que
se sostienen aunque se recalibren todos los parámetros de arriba:

- Que el número esperado de eventos de un proceso de Poisson crezca con lambda.
- Que la marginal de flores polinizadas sea `Poisson(mu*p)` cuando las visitas
  son Poisson y el filtro es Bernoulli.
- Que la saturación aparezca cuando la intensidad de salidas supera la capacidad
  de la colonia.
- Que un viaje que no cabe en lo que resta de la jornada no pueda completarse.
