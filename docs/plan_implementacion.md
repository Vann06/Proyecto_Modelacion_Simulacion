# Plan de implementación

Estado de avance del proyecto y qué falta exactamente por hacer. Este archivo se
actualiza cuando una fase se cierra.

La especificación del modelo está en `docs/model.md` y las decisiones de diseño,
con su alternativa descartada y su porqué, en `docs/decisions.md`.

---

## 0. Cómo poner a correr el repositorio

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux o macOS
source .venv/bin/activate

pip install -r requirements.txt
```

**El paquete vive en `src/`, así que hay que decírselo a Python:**

```bash
# Linux o macOS
PYTHONPATH=src python scripts/run_simulation.py --config config/base.yaml

# Windows PowerShell
$env:PYTHONPATH="src"; python scripts/run_simulation.py --config config/base.yaml
```

**Los notebooks se abren desde la carpeta `notebooks/`**, porque usan rutas
relativas (`../src`, `../config`):

```bash
cd notebooks
jupyter lab
```

Comprobación rápida de que todo quedó bien instalado:

```bash
PYTHONPATH=src python -c "from bee_sim.config import cargar, resumen; print(resumen(cargar('config/base.yaml')))"
```

---

## 1. Avance por fase

| Fase | Qué cubre | Estado | Depende de |
|---|---|---|---|
| F0 | Generadores de variables aleatorias | **completa** | nada |
| F1 | Configuración: YAML y cargador | **completa** | nada |
| F2 | Modelos de datos | **completa** | F1 |
| F3 | Los seis módulos de paso del viaje | **completa** | F0, F1 |
| F4 | Motor y métricas | **completa** | **F3 completa** |
| F5 | Persistencia de resultados | pendiente | F4 |
| F6 | Experimentos y campaña | pendiente | F5 |
| F7 | Validación y comparación de métodos | **completa** | F0 |
| F8 | Figuras | **completa** | F5 |
| F9 | Pruebas automatizadas | **parcial: motor y métricas cubiertos** | avanza junto con F3 y F4 |
| F10 | Informe y presentación | pendiente | F6 y F8 para la parte de resultados |

### Mapa de dependencias

```
F0 generadores ──┬─► F3 pasos del viaje ─► F4 motor ─► F5 persistencia ─► F6 campaña ─┐
                 │        (RUTA CRÍTICA)                                              │
F1 config ─► F2 modelos ─┘                                                            ├─► F10 informe
                                                                                      │
F0 ─► F7 validación y comparación ────────────────────────────────────────────────────┤
                                                                                      │
F5 ─► F8 figuras ─────────────────────────────────────────────────────────────────────┘

F9 pruebas: se escribe en paralelo con F3 y F4, no al final
```

** F0 y F7 están completas.** La siguiente fase pendiente es F8, persistencia.

---

## 2. Convención para todo el código nuevo

Los módulos ya escritos establecen estas reglas. Respetarlas evita que el motor
tenga que adaptarse a cada firma distinta.

1. **`cfg` penúltimo, `rng` último.** Toda función que sortee algo termina con
   `(..., cfg, rng)`. Toda función determinista termina con `(..., cfg)`.
2. **Nadie lee archivos.** La configuración llega ya cargada como diccionario.
   Solo `config.py` y los scripts de `scripts/` tocan el disco.
3. **Nadie imprime.** Los módulos devuelven valores; imprimir es de los scripts
   y los notebooks.
4. **Validar los argumentos y fallar con `ValueError`** y un mensaje que diga qué
   está mal y qué se esperaba.
5. **Los generadores no saben de abejas.** `generators/` produce números;
   `simulation/` les pone significado.
6. **Docstring con el método y la decisión.** Cada función dice qué método de
   generación usa y, si corresponde, a qué decisión de `docs/decisions.md`
   responde.

---

## 3. Lo que ya está en el repositorio

### Código verificado

```
src/bee_sim/config.py                 carga, herencia entre escenarios y validación
src/bee_sim/generators/               lcg, uniform, exponential, poisson,
                                      bernoulli, continuous
src/bee_sim/models/                   bee, colony, environment, trip
src/bee_sim/analysis/validation.py    nueve validaciones estadísticas
src/bee_sim/simulation/departures.py  Métodos A y B
src/bee_sim/simulation/distance.py    Weibull, tiempo de vuelo, p_ret(D)
src/bee_sim/simulation/flowers.py     flores visitadas, Poisson y Binomial Negativa
src/bee_sim/simulation/pollination.py flores polinizadas por convolución
config/                               base.yaml y siete escenarios
```

### Notebooks entregables

| Notebook | Contenido | Estado |
|---|---|---|
| `00_verificacion_del_motor.ipynb` | verificación de las seis etapas construidas | ejecutado, 16 de 16 comprobaciones conformes |
| `01_generator_validation.ipynb` | validación estadística de los nueve generadores | ejecutado, 9 de 9 con p > 0.05 |
| `02_scenario_analysis.ipynb` | análisis de escenarios | pendiente, requiere F6 |
| `03_final_figures.ipynb` | figuras finales del informe | pendiente, requiere F8 |

### Hallazgos registrados

- **Bug corregido en el generador Poisson.** `math.exp(-mu)` desborda a cero para
  mu grande, lo que dejaba la búsqueda acumulada en un bucle infinito. El Método
  B necesita `Poisson(λT) = Poisson(1200)`, así que el caso no era hipotético. Se
  resolvió aplicando la propiedad de división del Poisson: la suma de m variables
  `Poisson(mu/m)` independientes es `Poisson(mu)`. Consecuencia a documentar en
  el informe: el Método B ya no consume un uniforme para N sino seis, lo que
  afecta la comparación de costo contra el Método A.
- **Calibración de `active_bees` para BASE.** El barrido de saturación mostró
  61% de salidas perdidas con 30 forrajeras y 2.3% con 90. BASE quedó en 90 para
  que la saturación se estudie en el escenario ABEJAS-BAJA y no contamine la
  condición de referencia.
- **La validación por adelgazamiento quedó operativa.** La marginal de flores
  polinizadas resultó `Poisson(mu*p)` con media 5.213 y varianza 5.268 contra el
  teórico 5.200. Valida de forma simultánea el generador Poisson, el Bernoulli y
  el encadenamiento entre ambos. Solo es válida con un nivel de disponibilidad
  fijo: sobre la mezcla de tres niveles del escenario BASE la marginal es
  sobredispersa y la propiedad no aplica.
- **Los escenarios con disponibilidad fija no consumen uniformes** al resolver
  `A_f`. Las comparaciones entre escenarios deben hacerse sobre distribuciones
  agregadas, no viaje por viaje.
- **Varias métricas son casi la misma gráfica.** A nivel de viaje, `F` contra `X`
  correlaciona 0.90 y `F` contra `Q` correlaciona 0.92. Graficarlas por separado
  muestra tres veces la misma figura. En cambio `F` contra la duración del viaje
  correlaciona 0.085, y esa ausencia de relación sí es un resultado, porque dos
  mecanismos se cancelan.

---

## 4. F3. Los tres módulos de paso restantes

**Estado: completa.** Los tres módulos descritos a continuación ya están implementados.

**Paralelizable.** Los tres son independientes entre sí. Cada uno es una función
corta que lee parámetros de la configuración y llama a un generador ya probado.
No hay matemática nueva: toda vive en `generators/`.

### `simulation/nectar.py`

```python
def recolectar(flores_visitadas, escala_nectar, cfg, rng) -> float
```

Suma de `flores_visitadas` variables `Gamma(cfg['nectar']['shape'], escala_nectar)`,
generadas por aceptación y rechazo. Usa `generators.continuous.suma_gammas`.

Dos cosas que no se pueden equivocar:

- **Se acumula sobre las flores VISITADAS, no sobre las polinizadas.** La abeja
  toma néctar de la flor haya cuajado o no (decisión D-03).
- **Se genera flor por flor y se suma.** Con una sola Gamma de forma proporcional
  a `F` fallaría cuando `F = 0`, porque la forma sería cero (decisión D-04).

`escala_nectar` viene de `Environment.escala_nectar(nivel)`.

### `simulation/trip_duration.py`

```python
def tiempo_busqueda(escala_busqueda, cfg, rng) -> float
def tiempo_forrajeo(flores_visitadas, cfg, rng) -> float
def duracion_total(t_vuelo, t_busqueda, t_forrajeo) -> float
```

- `tiempo_busqueda`: una `Gamma(cfg['foraging']['search_shape'], escala_busqueda)`
  por aceptación y rechazo. Es el único lugar del motor que usa ese método para
  una variable propia del modelo.
- `tiempo_forrajeo`: suma de `flores_visitadas` exponenciales con media
  `cfg['foraging']['time_per_flower_mean']`. Usa
  `generators.exponential.suma_exponenciales`.
- `duracion_total`: suma las tres piezas. **No es una Gamma y no se sortea de
  golpe** (decisión D-01). El tiempo de vuelo lo calcula
  `distance.tiempo_vuelo`, que ya existe.

`escala_busqueda` viene de `Environment.escala_busqueda(nivel)`.

### `simulation/return_model.py`

```python
def cabe_en_jornada(t_salida, duracion, cfg) -> bool
def sobrevive_distancia(distancia_km, cfg, rng) -> bool
def retorna(t_salida, duracion, distancia_km, cfg, rng) -> tuple[bool, float]
```

`retorna` devuelve `(returned, p_ret)`, y `returned` exige que se cumplan **las
dos** condiciones. La probabilidad ya la calcula `distance.probabilidad_retorno`;
aquí solo falta el volado Bernoulli y la condición de horizonte.

Mantenerlas separadas permite reportar cuánto del no retorno viene de cada causa,
que es lo que hace defendible esa sección del informe: la condición de horizonte
sale de la estructura del modelo, mientras que la logística es un supuesto.

**Terminado cuando:** cada función corre con una configuración y un `rng`, y
respeta su invariante: `Q >= 0`, `Q = 0` si y solo si `F = 0`, todos los tiempos
positivos, y `duracion_total >= t_vuelo`.

---

## 5. F4. Motor y métricas

**Estado: completa.** Se implementaron el motor, el resumen y la verificación
de invariantes, con pruebas en `tests/test_engine.py` y `tests/test_metrics.py`.

```python
# simulation/engine.py
def simular_jornada(cfg, rng, run_id=0) -> list[Trip]

# simulation/metrics.py
def resumir(viajes, colonia, cfg) -> dict
def verificar_invariantes(viajes, cfg) -> None
```

El motor coordina, no calcula. El pseudocódigo está en
`src/bee_sim/simulation/README.md` y el orden exacto de generación en
`docs/model.md`, sección "Orden de generación dentro de un viaje".

Las dos piezas que no son azar y suelen olvidarse ya están implementadas: la
asignación de abeja disponible en `models/colony.py` y la actualización de
`available_at` en `models/bee.py`. El motor solo tiene que llamarlas.

`verificar_invariantes` recorre los viajes llamando a `Trip.validar()`, que ya
existe, y además comprueba que los identificadores sean únicos dentro de la
réplica.

**Terminado cuando:** una jornada corre completa, `verificar_invariantes` pasa
sin excepciones, y dos corridas con la misma configuración y semilla producen
listas de viajes idénticas campo por campo.

### Uso de F4 sin persistencia

Con `src` en `PYTHONPATH` y desde la raíz del repositorio:

```python
from bee_sim.config import cargar
from bee_sim.generators import crear_fuente
from bee_sim.simulation.engine import simular_jornada
from bee_sim.simulation.metrics import resumir, verificar_invariantes

cfg = cargar("config/base.yaml")
rng = crear_fuente(cfg["simulation"]["rng_source"], cfg["simulation"]["seed"])
viajes = simular_jornada(cfg, rng, run_id=0)
verificar_invariantes(viajes, cfg)
resumen_jornada = resumir(viajes, viajes.colonia, cfg)
```

La salida es `Jornada`, una subclase de `list` que conserva la colonia final en
`viajes.colonia`. Esto permite mantener la firma acordada y contar las salidas
no atendidas sin reconstruirlas a partir de los viajes ni guardar estado global.
El motor no escribe archivos ni reinicia el generador recibido.

Los identificadores de viaje son únicos dentro de la réplica; el identificador
de réplica se repite en sus registros, y una abeja puede realizar varios viajes
sin solaparse y siempre que haya retornado del anterior.

Las métricas separan néctar recolectado y entregado. Las tasas son fracciones y
devuelven `None` si su denominador es cero. Tiempo y distancia totales se etiquetan
como **planificados**, ya que el modelo no registra dónde ni cuándo se pierde una
abeja. No se inventa una trayectoria realizada ni se trunca el rendimiento.
El no retorno se divide en fuera de horizonte y fallo de distancia dentro del
horizonte; el registro actual no permite recuperar el resultado Bernoulli de
los viajes que terminarían fuera de jornada.

Validación: ocho escenarios, fuentes LCG y NumPy, métodos de salida A y B,
repetición por semilla, variante Binomial Negativa, saturación, retiro,
casos vacíos y métricas contrastadas con valores calculados a mano.
Las pruebas usan `unittest` y también son compatibles con `pytest`:

```powershell
$env:PYTHONPATH="src"
python -B -m unittest discover -s tests -v
```

`scripts/run_simulation.py` y la exportación de resultados siguen pendientes
para F5; el ejemplo anterior ejecuta directamente la API de F4.

---

## 6. F5. Persistencia

```
scripts/run_simulation.py --config config/base.yaml --seed 2026 --out results/runs
scripts/export_results.py --runs results/runs --out results/tables
```

Cada corrida deja tres archivos:

```
results/runs/run_0001.csv           una fila por viaje, columnas de models/trip.py
results/runs/run_0001_config.yaml   la configuración exacta con que corrió
results/runs/run_0001_summary.json  el resumen que devuelve metrics.resumir
```

La regla de `results/README.md` no se negocia: nunca guardar solo la gráfica. Las
columnas del CSV ya están fijadas por `models/trip.py`, no hay que inventarlas.

**Terminado cuando:** una corrida deja los tres archivos, y tomando únicamente el
`_config.yaml` guardado se puede reproducir la corrida y obtener un CSV idéntico.

---

## 7. F6. Experimentos y campaña

```python
# experiments/scenarios.py
ESCENARIOS = {...}                      # nombre -> ruta del YAML
def cargar_escenario(nombre) -> dict

# experiments/runner.py
def correr_escenario(nombre, n_replicas, semillas) -> list[dict]
def correr_campana(n_replicas) -> dict
```

El conjunto de semillas se fija una vez y se registra, para que todos los
escenarios se comparen sobre la misma suerte.

**Terminado cuando:** la campaña corre de punta a punta sobre los diez
escenarios, el conjunto de semillas queda registrado en un archivo, y el tiempo
total está medido con 50 réplicas antes de subir a 1,000.

---

## 8. F7. Validación y comparación de métodos — completa


`analysis/validation.py` estaba escrito y probado, y el notebook 01 ya lo
ejecutaba. Se agrego lo que faltaba:

```python
# scripts/validate_generators.py
# llama a las nueve funciones de validation.py, agrega tiempo de ejecucion,
# imprime la tabla y exporta results/tables/validacion_generadores.csv|.json
# y results/tables/comparacion_metodos.json

# analysis/comparison.py
def comparar_metodos_salidas(cfg, n_replicas, semillas) -> dict
def comparar_normal_polar_vs_rechazo(n, semilla) -> dict

# analysis/summaries.py
def resumir_replicas(resumenes) -> dict     # media, sd, percentiles, IC 95%
def resumir_escenarios(por_escenario) -> dict
```

`comparar_metodos_salidas` corre M-A y M-B **con el mismo lambda, el mismo
horizonte y el mismo conjunto de semillas**, y reporta para cada uno: número de
salidas (media y desviación), prueba de ajuste de los interarribos, uniformes
consumidos y tiempo de ejecución.

**Hallazgo verificado al implementarlo:** el LCG tiene estructura de reticula
(ya documentada en `generators/lcg.py`), y semillas consecutivas (2026, 2027,
2028, ...) sesgan sistematicamente el conteo del Metodo B. Con 200 replicas de
semillas consecutivas, el Metodo B dio una media de 1185.6 salidas contra una
teorica de 1200 (el Metodo A no se vio afectado, dio 1204.4). Con semillas
bien dispersas (`np.random.default_rng(base).integers(0, 2**31, size=n)`)
ambos dan ~1200-1202 sin sesgo, confirmado tambien con 3000 replicas donde
ambos convergen sin sesgo detectable. `comparar_metodos_salidas` valida el
rango de las semillas recibidas y falla si luce sospechosamente angosto.

**Terminado.** La tabla de validación tiene las columnas que pide el informe,
y la comparación M-A contra M-B reporta las cuatro medidas con semillas
compartidas. Verificado: `PYTHONPATH=src python scripts/validate_generators.py`
corre en menos de 2 segundos con n=20000 y 200 réplicas, y los 9 generadores
dan p > 0.05.

---

## 9. F8. Figuras — completa

`visualization/plots.py` consume resultados guardados y **nunca vuelve a
simular**. Cada función recibe un DataFrame o un diccionario y devuelve una
figura de matplotlib.

Las once figuras del informe y las dos adicionales para la presentación están
implementadas (`fig01` a `fig11`, más `fig_extra_ocupacion_jornada` y
`fig_extra_tiras_replicas`). Se probaron las 13 contra datos reales generados
con `scripts/run_experiment.py --campana` (320 corridas, 8 escenarios x 40
réplicas):

- `fig03` (saturación) muestra la meseta documentada en la sección 3 de este
  plan: con 30/90/150 abejas activas las salidas atendidas pasan de 510 a
  1179 a 1199 sobre una demanda de 1199, confirmando que BASE (90) ya está
  cerca del techo.
- `fig06` (tasa de polinización) requiere corridas con distinto `p_success`,
  que no están entre los ocho escenarios oficiales: se generaron aparte
  variando `pollination.p_success` directamente con el motor, y la tasa
  observada calca la recta identidad.
- `fig08` (distancia contra retorno) calca la logística teórica calculada con
  los mismos `sensitivity` y `midpoint_km` de la configuración.
- `fig10` confirma la joroba invertida con datos reales: la duración media del
  viaje es más corta en disponibilidad 'media' (13.9 min) que en 'baja' (15.6)
  o 'alta' (14.7).

**Terminado.** Cada figura se regenera desde un CSV guardado sin correr el
motor, y el pie de cada una nombra el mecanismo que muestra.

---

## 10. F9. Pruebas

Prioridad por riesgo, no por cobertura. Archivos según `tests/README.md`:

| Orden | Archivo | Qué protege |
|---|---|---|
| 1 | `test_engine.py` | invariantes del motor y reproducibilidad con semilla fija |
| 2 | `test_departures.py` | los dos métodos producen listas ordenadas dentro del horizonte |
| 3 | `test_pollination.py` | `X <= F` siempre, y el adelgazamiento con nivel fijo |
| 4 | `test_nectar.py` | `Q >= 0`, y `Q = 0` si y solo si `F = 0` |
| 5 | `test_return_model.py` | las dos condiciones del retorno por separado |
| 6 | `test_poisson.py`, `test_exponential.py` | momentos teóricos y el caso de mu grande |

El caso de mu grande en `test_poisson.py` no es opcional: es el bug que ya se
encontró una vez y una prueba evita que vuelva.

**Terminado cuando:** `pytest` corre limpio y cubre los seis archivos.

---

## 11. F10. Informe y presentación

**Este es el entregable que se califica.** El documento
`Informe_Modelacion_Abejas_Polinizacion.docx` está completo hasta Metodología.
Falta:

| Sección del informe | Qué falta | Depende de |
|---|---|---|
| Resultados | 9 tablas, todas en "Pendiente" | F6 |
| Resultados | 11 figuras por insertar | F8 |
| Análisis y discusión | redactar | F6 y F8 |
| Conclusiones | entre cuatro y seis, cada una citando el escenario que la sustenta | F6 |
| Recomendaciones | derivadas de resultados | F6 |
| Apéndice de supuestos | transcribir `docs/assumptions.md` | escribir assumptions.md |
| Anexo 4 | enlace de la presentación en Canva | armar la presentación |
| Anexo 5 | URL del repositorio | ya existe, solo pegarla |
| Portada | faltan dos carnés de integrantes | nada |

También hay que actualizar la sección "Distribuciones a implementar" del informe,
porque las decisiones acordadas cambiaron respecto de lo que quedó escrito ahí:
la duración del viaje se construye y no se sortea, la distancia usa Weibull, y el
néctar cuelga de las flores visitadas. Todo eso está en `docs/decisions.md` con
su justificación.

La presentación debe incluir la pregunta central, el modelo, los métodos de
generación, la validación, los escenarios principales, resultados, conclusiones y
una demostración breve.

**Terminado cuando:** no queda ningún "Pendiente" en el documento y los dos
anexos tienen su enlace.

---

## 12. Reparto sugerido para cuatro personas

| Persona | Se encarga de | Puede empezar | Bloqueos |
|---|---|---|---|
| **B** | F3, los tres módulos de paso | de una | ninguno. **Es la ruta crítica** |
| **A** | F4 motor, F5 persistencia | de una, con reservas | puede escribir la estructura del motor, pero no lo cierra hasta que B termine |
| **C** | F7 validación y comparación, F9 pruebas | de una | ninguno |
| **D** | F8 figuras, F10 informe | de una | puede redactar metodología, supuestos y la presentación desde ahora; las figuras esperan a F5 |

**Recomendación para A y B:** que A escriba `engine.py` llamando a las tres
funciones de B con sus firmas ya acordadas (están en la sección 4), aunque
todavía no existan. Cuando B las entregue, el motor debería correr sin cambios.
Por eso las firmas están escritas aquí y no se deben improvisar.

**Sugerencia de orden para C:** empezar por `scripts/validate_generators.py`, que
no depende de nada y produce una tabla que el informe ya tiene reservada. Después
las pruebas, que se pueden ir escribiendo conforme B entrega módulos.

---

## 13. Commits sugeridos

```
feat: add random variable generators with own LCG source
feat: add statistical validation of generators
feat: add departure generation methods A and B
fix: split large mu in poisson generator to avoid underflow
feat: add scenario configuration with inheritance and validation
feat: add data models for bee, colony, environment and trip
feat: add distance model and flight time
feat: add flower count and pollination steps
docs: add model specification, design decisions and implementation plan
docs: add executed notebooks for engine and generator verification
```

---

## 14. Limpieza pendiente

- El archivo `requiremets.txt`, con el nombre mal escrito, sigue en el
  repositorio. Ya existe `requirements.txt` correcto; conviene eliminar el viejo
  una vez que nadie lo referencie.
- El README describe archivos que la estructura no tiene (`binomial.py`,
  `travel.py`, `experiments.py`, carpetas `data/` y `presentation/`). Conviene
  alinearlo con la estructura real, que ya está definida.
- El README pide Python 3.11 o superior; el código corre sin problema en 3.10.
- El README lista dos integrantes y el informe lista cuatro.

---

## 15. Parámetros sin fuente

Siguen siendo supuestos de modelo y deben quedar declarados como tales en
`docs/assumptions.md`, que aún está vacío:

- `search_shape` y las tres `search_scale` del tiempo de búsqueda
- si la velocidad de vuelo se mantiene constante o se sortea
- `sensitivity` y `midpoint_km` de la logística de retorno
- los nueve valores de los tres niveles de disponibilidad floral
- la independencia entre distancia y disponibilidad floral: el modelo no las
  correlaciona, y en la realidad probablemente lo estén
- el número final de réplicas, que depende de medir el costo

En `config/base.yaml` cada uno de estos aparece marcado con un comentario
`SUPUESTO`, de modo que escribir `assumptions.md` es transcribir esa lista.
