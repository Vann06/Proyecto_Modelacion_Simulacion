# Modelo de simulación: distribuciones, métodos e inversas

Documento de referencia acordado por el equipo. Reconcilia el informe con el
prototipo y fija, para cada variable, qué distribución se usa, con qué método se
genera y si hay inversa cerrada.

Regla general: **ningún método está de adorno**. Cada técnica vista en clase
(inversa algebraica, inversa discreta, aceptación y rechazo, composición,
convolución) tiene al menos un uso justificado dentro del motor.

---

## 0. Base uniforme

| | |
|---|---|
| Variable | `U ~ Uniforme(0,1)` |
| Para qué | Materia prima de todo lo demás |
| Método | LCG propio: `x_{n+1} = (a·x_n + c) mod m`, `U = x/m` |
| Parámetros | `a = 1664525`, `c = 1013904223`, `m = 2^32` (Numerical Recipes) |
| Inversa | No aplica, es el punto de partida |

**Uso operativo:** el LCG se usa en la sección de validación de generadores y en
la corrida de comparación contra el generador estándar del lenguaje. Para la
campaña experimental completa se usa NumPy vectorizado por costo computacional
(ver sección 10).

**Validación:** media 0.5, varianza 1/12, Kolmogorov-Smirnov contra U(0,1),
autocorrelación de retardo 1 a 10, y diagrama de dispersión `U_i` vs `U_{i+1}`
para detectar estructura de retícula (los LCG generan puntos alineados en planos,
es su debilidad conocida).

---

## 1. Salidas de la colmena: los dos métodos a comparar

Ambos métodos deben producir **el mismo objeto**: una lista ordenada de tiempos
de salida dentro de `[0, day_minutes]`. Esto es lo que los hace comparables.

### Método A: interarribos exponenciales (transformada inversa)

```
T_i ~ Exponencial(lambda)
F(t) = 1 - e^(-lambda·t)
=> T = -ln(1 - U) / lambda
```

Se acumulan los `T_i` hasta rebasar `day_minutes`. Los tiempos acumulados son los
tiempos de salida.

- Inversa: **sí, derivada algebraicamente**. Es una de las dos que se muestran
  con despeje completo en el informe.

### Método B: conteo Poisson directo + uniformidad condicional

```
N ~ Poisson(lambda · day_minutes)
```

Inversa discreta por búsqueda acumulada: se acumula `p(0), p(0)+p(1), ...` con
la recurrencia `p(k) = p(k-1)·mu/k` y se devuelve el primer `k` cuya acumulada
supera `U`.

**Pieza crítica:** `N` dice cuántas abejas salieron, no cuándo. Se usa la
propiedad de uniformidad condicional del proceso de Poisson: dado que ocurrieron
`N = n` eventos en `[0, T]`, esos `n` tiempos se distribuyen como `n` uniformes
independientes en `(0, T)`, ordenados de menor a mayor.

```
generar N por inversa discreta
generar N uniformes en (0, day_minutes)
ordenar
```

Sin este paso M-B no sirve como motor de simulación, solo como conteo.

**Alternativa documentada:** método de Knuth (multiplicar uniformes hasta bajar
de `e^(-mu)`). Se implementa para comparar tiempo de ejecución contra la
búsqueda acumulada.

**Comparación M-A vs M-B:** mismo `lambda`, mismo conjunto de semillas, mismo
número de réplicas. Se comparan distribución de `N` por intervalo (chi cuadrada),
distribución de interarribos (Kolmogorov-Smirnov contra la Exponencial teórica) y
tiempo de ejecución.

---

## 2. Asignación de la salida a una abeja

No es una variable aleatoria. Cada salida se asigna a la primera forrajera con
`available_at <= t_salida`. Si ninguna está libre, la salida se descarta y se
registra como salida no atendida.

Esto es lo que hace que `active_bees` (abejas activas) sea un factor real del
experimento: con pocas abejas, el proceso de Poisson genera salidas que nadie
puede atender, y ahí aparece la saturación que plantea la hipótesis del informe.

---

## 3. Distancia al parche floral

| | |
|---|---|
| Variable | `D ~ Weibull(k_D, lambda_D)` |
| Unidad | km |
| Inversa | **Sí, cerrada y derivable** |

```
F(x) = 1 - e^(-(x/lambda_D)^k_D)
=> D = lambda_D · (-ln(1 - U))^(1/k_D)
```

- `k_D` (forma) fijo en 2. Con `k_D = 2` la densidad tiene moda distinta de cero
  y cola a la derecha, que es justo lo que se quería: la abeja rara vez encuentra
  el parche pegado a la colmena, y a veces vuela mucho más lejos del promedio.
- `lambda_D` (escala) es lo que mueve el escenario: DIST-CERCA, DIST-INTERMEDIA,
  DIST-LEJOS.

**Justificación honesta:** es pragmática, no mecanística. Se elige Weibull sobre
Gamma o Lognormal porque tiene inversa cerrada y da una segunda derivación
algebraica al informe. Debe declararse como supuesto de modelo en la sección de
amenazas a la validez.

---

## 4. Disponibilidad floral

| | |
|---|---|
| Variable | `A_f ∈ {baja, media, alta}` |
| Inversa | Discreta trivial: comparar `U` contra la acumulada (0.3 / 0.8 / 1.0) |

**Tratamiento dual, según el escenario:**

- En BASE se **sortea por viaje**, representando un paisaje heterogéneo donde
  unos parches son ricos y otros pobres. Aquí sí es variable aleatoria y usa la
  inversa categórica.
- En FLORES-BAJA y FLORES-ALTA se **fija**. Aquí es parámetro, no variable, y no
  se genera nada.

`A_f` no actúa sobre una sola cosa. Escala tres parámetros a la vez:

| `A_f` | `mu_F` (flores visitadas) | `theta_q` (néctar por flor) | `theta_b` (tiempo de búsqueda) |
|---|---|---|---|
| baja | bajo | bajo | **alto** (cuesta más encontrar) |
| media | base | base | base |
| alta | alto | alto | bajo |

El efecto sobre `theta_b` es lo que hace que la escasez cueste tiempo y no solo
rendimiento, que es lo que plantea la hipótesis del informe.

---

## 5. Flores visitadas por viaje

| | |
|---|---|
| Variable | `F ~ Poisson(mu_F(A_f))` |
| Variante | `F ~ Binomial Negativa(mu_F, r)` para sobredispersión |
| Inversa | Discreta por búsqueda acumulada, misma rutina del punto 1 |

**Variante por composición (Binomial Negativa):**

```
lambda' ~ Gamma(forma = r, escala = mu_F / r)
F       ~ Poisson(lambda')
```

Con esta parametrización `E[F] = mu_F` y `Var[F] = mu_F + mu_F^2 / r`. Cuando
`r → ∞` se recupera la Poisson. La ventaja: el escenario solo mueve `mu_F` y `r`
queda como control independiente de la sobredispersión, así la comparación entre
escenarios no mezcla dos efectos.

Interpretación de la sobredispersión: hay viajes muy buenos y muy malos, más
variabilidad de la que una Poisson pura permite.

---

## 6. Flores efectivamente polinizadas

| | |
|---|---|
| Variable | `X = suma de F ensayos Bernoulli(p_pol)` |
| Inversa | Bernoulli trivial: `U < p_pol ? 1 : 0` |
| Inversa binomial | **No se usa** |

**Por qué no inversa binomial:** `F` es aleatorio y cambia en cada viaje, así que
el parámetro de la Binomial cambia en cada viaje. Una inversa binomial exigiría
recalcular la función acumulada con cada `F` distinto. La suma de Bernoulli
respeta el anidamiento (`X | F ~ Binomial(F, p_pol)`) y hace visible el método.

**Validación analítica exacta (aprovecharla en el informe):** si
`F ~ Poisson(mu_F)` y cada visita poliniza con probabilidad `p_pol`, entonces la
marginal de `X` es exactamente `Poisson(mu_F · p_pol)`. Es la propiedad de
adelgazamiento (thinning: filtrar un Poisson con una moneda produce otro
Poisson). Da una prueba chi cuadrada contra un valor teórico conocido sin
necesidad de calibrar nada.

---

## 7. Néctar recolectado

| | |
|---|---|
| Variable | `Q = suma de F variables q_i` |
| Por flor | `q_i ~ Gamma(k_q, theta_q(A_f))`, `k_q` no entero |
| Método | **Aceptación y rechazo** (Marsaglia-Tsang) |
| Inversa | No existe cerrada (la acumulada es la función gamma incompleta) |

Dos decisiones importantes:

1. **Q se acumula sobre `F` (flores visitadas), no sobre `X` (polinizadas).** Una
   abeja recolecta néctar de la flor la haya polinizado efectivamente o no. Son
   eventos distintos y atarlos genera una correlación artificial.
2. **Se genera por flor y se suma**, no como una Gamma con forma `k ≈ F`. Si
   `F = 0` la forma sería cero y la Gamma no existe. Sumando por flor, `F = 0`
   da `Q = 0` de forma natural, y la suma sigue siendo convolución exacta.

Marsaglia-Tsang usa una Normal por dentro, generada por método polar. Para
`k_q < 1` se usa el truco de aumento: generar con `k_q + 1` y multiplicar por
`U^(1/k_q)`.

---

## 8. Duración del viaje

**No se genera como Gamma marginal. Se construye por partes.**

```
T_viaje = T_ida + T_busqueda + T_forrajeo + T_regreso
```

| Componente | Modelo | Método |
|---|---|---|
| `T_ida = T_regreso = D / V` | determinista dado `D` | ninguno |
| `T_busqueda ~ Gamma(k_b, theta_b(A_f))` | `k_b` no entero | **aceptación y rechazo** |
| `T_forrajeo = suma de F variables H_i` | `H_i ~ Exponencial(lambda_h)` | inversa, **convolución** |

`V` (velocidad de vuelo) es constante configurable. Opcionalmente
`V ~ Normal(mu_V, sigma_V)` truncada, generada por método polar.

**Por qué así y no `T_viaje ~ Gamma(k, theta)`:** la fórmula del informe tiene un
número aleatorio de sumandos (`F` es aleatorio), así que técnicamente es una suma
aleatoria, no una Gamma de forma fija. Construirlo por partes además acopla la
duración con la distancia y con las flores visitadas, que es lo que exigen las
hipótesis sobre distancia y disponibilidad.

**Resultado explotable:** ajustar una Gamma a la marginal empírica de `T_viaje` y
mostrar que se parece, sin haberla impuesto. Es un buen hallazgo para la
discusión: la forma Gamma emerge de la estructura, no se asume.

`T_busqueda` es además el hogar legítimo del método de aceptación y rechazo
dentro del motor. Sin él, todo el motor sería inversa y convolución.

---

## 9. Retorno a la colmena

Dos condiciones, ambas deben cumplirse:

1. **Condición dura (temporal):** `t_salida + T_viaje <= day_minutes`. El viaje
   tiene que caber en la jornada.
2. **Condición estocástica (distancia):** `R ~ Bernoulli(p_ret(D))` con

```
p_ret(D) = 1 / (1 + e^(a·(D - d0)))
```

Inversa trivial de Bernoulli. `a` controla la sensibilidad a la distancia y `d0`
el punto de inflexión, ambos en configuración.

```
returned = (cabe en la jornada) AND (R == 1)
```

Si `returned`, la abeja vuelve a estar disponible en
`available_at = t_salida + T_viaje`. Si no, sale de la fuerza de forrajeo por el
resto del día.

**Advertencia obligatoria en el informe:** `p_ret(D)` es una construcción del
modelo sin calibración biológica. Sus parámetros son supuestos, no datos.

---

## 10. Costo computacional

Cada viaje consume del orden de 50 a 100 uniformes. Con ~1,000 viajes por
jornada, 1,000 réplicas y 10 escenarios se llega a más de 5×10^8 llamadas a
`uniform()`. En Python puro con el LCG eso son horas.

Plan:

- LCG propio en la validación de generadores y en la comparación M-A vs M-B, que
  es donde importa demostrarlo.
- NumPy vectorizado (bloques de uniformes) para la campaña completa.
- Medir el costo real con 50 réplicas antes de comprometerse a 1,000.

---

## Tabla resumen

| # | Variable | Distribución | Inversa | Método de generación |
|---|---|---|---|---|
| 0 | `U` | Uniforme(0,1) | no aplica | LCG propio |
| 1a | `T_salida` | Exponencial(lambda) | **cerrada, derivada** | transformada inversa |
| 1b | `N_salida` | Poisson(lambda·T) | discreta | búsqueda acumulada + uniformidad condicional |
| 3 | `D` | Weibull(k_D, lambda_D) | **cerrada, derivada** | transformada inversa |
| 4 | `A_f` | Categórica | discreta trivial | comparación contra acumulada |
| 5 | `F` | Poisson(mu_F) / NegBin | discreta | búsqueda acumulada / **composición** Gamma-Poisson |
| 6 | `X` | Binomial(F, p_pol) | no se usa | **convolución** de Bernoulli |
| 7 | `q_i`, `Q` | Gamma(k_q, theta_q) | no existe | **aceptación y rechazo** + convolución |
| 8a | `T_busqueda` | Gamma(k_b, theta_b) | no existe | **aceptación y rechazo** (Marsaglia-Tsang) |
| 8b | `H_i`, `T_forrajeo` | Exponencial(lambda_h) | cerrada | inversa + **convolución** |
| 9 | `R` (retorno) | Bernoulli(p_ret(D)) | trivial | comparación contra `p` |

## Cobertura de métodos

| Método | Dónde se usa |
|---|---|
| Inversa derivada algebraicamente | Exponencial (`T_salida`, `H_i`), Weibull (`D`) |
| Inversa discreta por búsqueda | Poisson (`N`, `F`), categórica (`A_f`) |
| Inversa trivial | Bernoulli (`P_i`, `R`) |
| Aceptación y rechazo | Gamma (`T_busqueda`, `q_i`), Normal polar dentro de Marsaglia-Tsang |
| Composición | Binomial Negativa (mezcla Gamma-Poisson), aumento de forma en Marsaglia-Tsang |
| Convolución | `X` (suma de Bernoulli), `T_forrajeo` (suma de exponenciales), `Q` (suma de Gammas) |

---

## Orden de generación dentro de un viaje

El orden importa, porque hay dependencias:

```
1. t_salida        (M-A o M-B, generado antes del bucle de viajes)
2. asignar abeja disponible   -> si no hay, salida no atendida
3. A_f             (sorteada en BASE, fija en escenarios controlados)
4. D               (Weibull; lambda_D lo fija el escenario)
5. F               (Poisson/NegBin con mu_F(A_f))
6. X               (suma de F Bernoulli(p_pol))
7. Q               (suma de F Gammas con theta_q(A_f))
8. T_busqueda      (Gamma con theta_b(A_f))
9. T_forrajeo      (suma de F exponenciales)
10. T_viaje = 2·D/V + T_busqueda + T_forrajeo
11. R              (Bernoulli(p_ret(D)))
12. returned = (t_salida + T_viaje <= day_minutes) AND R
13. registrar viaje, actualizar available_at de la abeja
```

## Invariantes a verificar en cada corrida

- `X <= F` siempre
- `Q >= 0`, `Q = 0` si y solo si `F = 0`
- `D > 0`, `T_viaje > 0`
- ningún viaje inicia después de `day_minutes`
- `run_id`, `bee_id`, `trip_id` únicos dentro de cada réplica
- misma semilla, configuración y entorno compatible producen los mismos
  resultados numéricos

## Alcance de la métrica de polinización

El resumen conserva tres definiciones para evitar confundir viajes iniciados con
actividad completada dentro del horizonte:

- `flores_polinizadas`: resultado planificado de todos los viajes iniciados;
- `flores_polinizadas_viajes_que_caben`: viajes cuya duración completa cabe en
  la jornada, aunque la abeja falle el retorno probabilístico;
- `flores_polinizadas_viajes_completos`: únicamente viajes con retorno exitoso.

El primer indicador se mantiene por compatibilidad con las tablas existentes.
Cuando se afirme estrictamente "durante la jornada", debe usarse el segundo o
explicarse de forma explícita el alcance del indicador.
