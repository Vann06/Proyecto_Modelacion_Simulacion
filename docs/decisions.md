# Decisiones técnicas y metodológicas

Registro de las decisiones tomadas al conciliar el informe con el prototipo.
Cada entrada dice qué se decidió, contra qué alternativa, y por qué. La
especificación resultante está en `docs/model.md`.

---

## D-01. La duración del viaje se construye, no se sortea

**Decisión:** `T_viaje = 2·D/V + T_busqueda + T_forrajeo`, con `T_forrajeo` como
suma de `F` exponenciales.

**Alternativa descartada:** `T_viaje ~ Gamma(k, theta)` como distribución
marginal directa.

**Por qué:** con `F` aleatorio la fórmula del informe es una suma aleatoria (el
número de sumandos también es una variable aleatoria), no una Gamma de forma
fija. Además, sortear la marginal rompería la conexión entre distancia y
duración, que es una de las preguntas de investigación del proyecto.

**Consecuencia aprovechable:** se puede ajustar una Gamma a la marginal empírica
de `T_viaje` y mostrar que la forma emerge de la estructura sin haberla impuesto.

---

## D-02. El tiempo de búsqueda entra al modelo como Gamma por rechazo

**Decisión:** agregar `T_busqueda ~ Gamma(k_b, theta_b(A_f))` con `k_b` no
entero, generada con Marsaglia-Tsang.

**Por qué:** al decidir D-01, el motor se quedaba sin ningún uso real del método
de aceptación y rechazo (todo era inversa y convolución). `T_busqueda` ya estaba
mencionado en el informe pero no modelado, así que no es relleno. Además conecta
la escasez floral con costo en tiempo, no solo con menor rendimiento.

---

## D-03. El néctar cuelga de flores visitadas, no de polinizadas

**Decisión:** `Q = suma sobre las F flores visitadas`.

**Alternativa descartada:** acumular sobre `X` (polinizadas), como hacía el
prototipo.

**Por qué:** recolectar néctar y polinizar efectivamente son eventos distintos.
Una abeja toma néctar de la flor independientemente del resultado reproductivo.
Atarlos crea una correlación artificial entre dos métricas que el informe reporta
por separado.

---

## D-04. El néctar se genera por flor y se suma

**Decisión:** `q_i ~ Gamma(k_q, theta_q)` por flor, `Q = suma`.

**Alternativa descartada:** una sola `Gamma` con forma `k ≈ F`.

**Por qué:** si `F = 0` la forma sería cero y la Gamma no está definida. Sumando
por flor, `F = 0` produce `Q = 0` de forma natural y la suma sigue siendo
convolución exacta.

---

## D-05. La distancia usa Weibull

**Decisión:** `D ~ Weibull(k_D = 2, lambda_D)`, con `lambda_D` fijado por el
escenario.

**Alternativa descartada:** Gamma o Lognormal.

**Por qué:** las tres cumplen el requisito de ser positivas y asimétricas a la
derecha, pero solo Weibull tiene inversa cerrada. Eso da al informe una segunda
derivación algebraica además de la Exponencial, que es lo que se evalúa.

**Limitación declarada:** la elección es pragmática, no mecanística. Debe
aparecer como supuesto en la sección de amenazas a la validez.

---

## D-06. El Método B necesita uniformidad condicional

**Decisión:** M-B genera `N ~ Poisson(lambda·T)` y luego `N` uniformes en
`(0, T)` que se ordenan para obtener los tiempos de salida.

**Por qué:** el conteo por sí solo no dice cuándo sale cada abeja, y sin tiempos
de salida no se puede simular la jornada ni limitar cuántos viajes caben. La
propiedad de uniformidad condicional del proceso de Poisson resuelve esto de
forma exacta. Sin este paso, M-B no sería comparable con M-A como motor completo,
solo como generador de conteos.

---

## D-07. La disponibilidad floral tiene tratamiento dual

**Decisión:** `A_f` se sortea por viaje en el escenario BASE y se fija en los
escenarios FLORES-BAJA y FLORES-ALTA.

**Por qué:** en los escenarios controlados es un factor experimental, no una
variable aleatoria, y sortearla contaminaría la comparación. En BASE, sortearla
representa un paisaje heterogéneo y permite usar la inversa categórica de forma
legítima.

---

## D-08. La Binomial Negativa se parametriza por media y forma

**Decisión:** `lambda' ~ Gamma(forma = r, escala = mu_F/r)`, luego
`F ~ Poisson(lambda')`.

**Por qué:** con esta parametrización `E[F] = mu_F` exactamente, así que los
escenarios florales mueven solo la media y `r` queda como control independiente
de la sobredispersión. Con la parametrización clásica `(r, p)` un cambio de
escenario movería media y varianza a la vez, mezclando dos efectos.

---

## D-09. El retorno combina condición dura y estocástica

**Decisión:** `returned = (t_salida + T_viaje <= day_minutes) AND Bernoulli(p_ret(D))`.

**Por qué:** son dos causas distintas de no retorno. La primera es contable (el
viaje no cabe en la jornada) y sale de la estructura del modelo. La segunda es el
riesgo asociado a la distancia y es un supuesto sin calibración. Separarlas
permite reportar cuánto del no retorno viene de cada causa.

---

## D-10. LCG para validación, NumPy para la campaña

**Decisión:** el LCG propio se usa en la validación de generadores y en la
comparación M-A vs M-B. La campaña experimental completa usa NumPy vectorizado.

**Por qué:** la campaña completa supera 5×10^8 llamadas a `uniform()`, que en
Python puro son horas de cómputo. El valor académico del LCG está en demostrarlo
y medirlo, no en atravesar con él 10,000 corridas.

**Control:** medir el costo real con 50 réplicas antes de fijar el número final.

---

## D-11. La sensibilidad de la logística de retorno sube de 1.2 a 3.0

**Decisión:** `return.sensitivity` pasa de 1.2 a 3.0. `midpoint_km` se queda en 4.0.

**Alternativa descartada:** subir `midpoint_km` a 6 u 8 km.

**Por qué:** con `a = 1.2` la corrida de BASE terminaba con 4 forrajeras vivas de
90. No era un error del código: cada abeja alcanza a hacer unos 41 viajes en una
jornada de 600 minutos, y con una probabilidad de retorno media de 0.9466 por
viaje, sobrevivir el día tiene probabilidad 0.9466^41 = 0.105. La repetición
castiga muchísimo.

El defecto de fondo de una pendiente suave es que filtra riesgo hacia distancias
donde no debería haberlo: con `a = 1.2`, una abeja que volara cero kilómetros
tenía 0.8% de probabilidad de no volver. Subir `a` concentra el riesgo alrededor
de `d0` y deja de castigar los viajes cortos.

**Por qué no se movió `midpoint_km`:** desplazar la curva a la derecha también
resuelve la supervivencia, pero aplana la diferencia entre escenarios de
distancia, que es una de las preguntas de investigación. Con `d0 = 8` la
separación de la tasa de retorno entre DIST-CERCA y DIST-LEJOS cae de 0.223 a
0.008, o sea que la hipótesis sobre distancia se queda sin nada que medir. Subir
`a` conserva esa separación en 0.185.

**Efecto medido** (escenario BASE, semilla 2026, misma corrida antes y después):

| | a = 1.2 | a = 3.0 |
|---|---|---|
| abejas vivas al cierre | 4 de 90 | **53 de 90** |
| tasa de retorno por viaje | 0.930 | 0.970 |
| no retorno por horizonte | 30 | 33 |
| no retorno por distancia | 56 | **4** |
| néctar entregado | 560.7 ml | 588.8 ml |

**Consecuencia interpretativa.** Con el valor nuevo, la causa dominante de no
retorno pasa a ser el horizonte de la jornada y no la logística. Eso es más
defendible en el informe, porque el horizonte sale de la estructura del modelo
mientras que la logística sigue siendo un supuesto sin calibración.

**Sigue siendo un supuesto.** Los dos parámetros no provienen de datos. Lo que
cambia es que ahora existe un argumento cuantitativo de por qué esos valores y
no otros.

---

## Pendientes de decisión

- Valor de `k_b` y `theta_b` base para `T_busqueda` (no hay fuente, quedan como
  supuestos configurables).
- Si `V` (velocidad de vuelo) se mantiene constante o se sortea Normal truncada.
- Valores de `a` y `d0` de la logística de retorno.
- Número final de réplicas, tras medir costo.
