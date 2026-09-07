# Simulación Estocástica del Forrajeo y Polinización de Abejas

## Descripción

Este repositorio contiene una simulación estocástica del comportamiento de forrajeo de una colonia de abejas melíferas.

El sistema representa una jornada en la que las abejas salen de la colmena, se desplazan hacia zonas florales, visitan flores, realizan eventos de polinización, recolectan néctar y regresan a la colmena.

El modelo incorpora distintas fuentes de aleatoriedad para estudiar cómo cambia el comportamiento general de la colonia bajo diferentes condiciones de actividad, distancia y disponibilidad floral.

El propósito es construir un modelo simplificado, reproducible y estadísticamente analizable que permita aplicar métodos de generación de variables aleatorias y comparar su comportamiento dentro de un sistema real.

---

## Pregunta principal

**¿Cuánto puede polinizar una colonia de abejas durante una jornada y cómo cambian sus resultados de forrajeo cuando varían las condiciones del entorno?**

El análisis considera principalmente:

- cantidad de abejas o viajes que salen de la colmena;
- tiempo entre salidas;
- cantidad de flores visitadas por viaje;
- duración de cada viaje;
- probabilidad de polinización;
- cantidad de néctar recolectado;
- distancia recorrida;
- retorno de las abejas;
- disponibilidad de flores.

---

## Objetivo general

Diseñar e implementar una simulación estocástica del comportamiento de forrajeo de una colonia de abejas que permita analizar la interacción entre las salidas de la colmena, los viajes realizados, las flores visitadas, la polinización, la recolección de néctar, la distancia y las condiciones de disponibilidad floral.

## Objetivos específicos

- Modelar las salidas de abejas durante una jornada mediante variables aleatorias.
- Representar el tiempo entre salidas utilizando distribuciones apropiadas.
- Simular la cantidad de flores visitadas durante cada viaje.
- Estimar la cantidad de flores efectivamente polinizadas.
- Representar la recolección de néctar durante los viajes.
- Incorporar la distancia recorrida como parte del comportamiento de forrajeo.
- Analizar la duración de los viajes.
- Representar probabilísticamente el retorno de las abejas.
- Comparar escenarios con diferentes niveles de disponibilidad floral.
- Validar estadísticamente los generadores utilizados.
- Comparar métodos de generación de variables aleatorias.
- Generar resultados reproducibles mediante semillas controladas.

---

## Variables principales de la simulación

| Variable | Descripción |
|---|---|
| Salidas | Cantidad de abejas o viajes que inician durante un intervalo. |
| Tiempo entre salidas | Tiempo transcurrido entre dos eventos consecutivos de salida. |
| Distancia | Distancia entre la colmena y la zona floral seleccionada. |
| Flores visitadas | Cantidad de flores visitadas durante cada viaje. |
| Polinización | Cantidad de visitas que terminan en una polinización efectiva. |
| Néctar | Cantidad de néctar recolectado durante cada viaje. |
| Duración del viaje | Tiempo total desde la salida hasta el retorno. |
| Retorno | Indica si el viaje termina con regreso a la colmena dentro del horizonte simulado. |
| Disponibilidad floral | Condición del entorno: pocas, medias o muchas flores disponibles. |

---

## Distribuciones y métodos utilizados

La simulación utiliza diferentes distribuciones de probabilidad según el tipo de variable modelada:

- **Uniforme:** generación base de números pseudoaleatorios y variables dentro de intervalos.
- **Exponencial:** tiempos entre eventos, como las salidas de las abejas.
- **Poisson:** conteo de eventos dentro de un intervalo y variables de conteo.
- **Bernoulli:** eventos con dos resultados posibles, como polinización o no polinización.
- **Binomial:** cantidad de éxitos obtenidos después de varias visitas a flores.
- **LCG:** generador congruencial lineal propio para comparar generación pseudoaleatoria.

La lógica matemática se mantiene separada de la lógica específica de las abejas para facilitar su validación y reutilización.

---

## Flujo general de la simulación

```text
Configuración
      ↓
Inicialización de semilla
      ↓
Generación de salidas
      ↓
Generación de distancia
      ↓
Viaje hacia la zona floral
      ↓
Generación de flores visitadas
      ↓
Eventos de polinización
      ↓
Recolección de néctar
      ↓
Cálculo de duración del viaje
      ↓
Evaluación del retorno
      ↓
Registro del viaje
      ↓
Cálculo de métricas
      ↓
Análisis estadístico
```

---

## Escenarios de simulación

La campaña contiene 12 configuraciones sin modificar el código principal:

- `base`: condición de referencia;
- `bees_low` y `bees_high`: 30 y 150 forrajeras activas;
- `flowers_low` y `flowers_high`: disponibilidad floral fija baja y alta;
- `distance_near` y `distance_far`: menor y mayor escala de distancia;
- `lambda_low` y `lambda_high`: menor y mayor intensidad de salidas;
- `pollination_low` y `pollination_high`: probabilidad de polinización de 0.40 y 0.85;
- `combined`: baja disponibilidad junto con distancia lejana.

---

# Arquitectura del repositorio

```text
Proyecto_Modelacion_Simulacion/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   ├── base.yaml
│   └── *.yaml                    # once variaciones que heredan de BASE
├── src/
│   └── bee_sim/
│       ├── generators/
│       │   ├── uniform.py, lcg.py
│       │   ├── exponential.py, poisson.py, bernoulli.py
│       │   └── continuous.py
│       ├── models/
│       │   ├── bee.py, colony.py, environment.py
│       │   └── trip.py
│       ├── simulation/
│       │   ├── engine.py, departures.py, distance.py
│       │   ├── flowers.py, pollination.py, nectar.py
│       │   ├── trip_duration.py, return_model.py
│       │   └── metrics.py
│       ├── analysis/
│       │   ├── validation.py, comparison.py, summaries.py
│       │   └── campaign_io.py
│       ├── experiments/
│       │   ├── scenarios.py
│       │   └── runner.py
│       └── visualization/
│           └── plots.py
├── scripts/
│   ├── run_simulation.py
│   ├── run_experiment.py
│   ├── validate_generators.py
│   └── export_results.py
├── tests/                       # pruebas unitarias y de integración
├── notebooks/
│   ├── 00_verificacion_del_motor.ipynb
│   ├── 01_generator_validation.ipynb
│   ├── 02_scenario_analysis.ipynb
│   └── 03_final_figures.ipynb
├── results/
│   ├── runs/                    # CSV, configuración y resumen por réplica
│   ├── tables/                  # salidas de validación y tablas consolidadas
│   └── figures/                 # figuras regenerables desde runs/
├── docs/
│   ├── model.md, methodology.md
│   ├── assumptions.md, decisions.md
│   ├── f10_resultados.md
│   └── presentacion.md
└── data/
```

---

# Responsabilidad de los módulos

## `config/`

Contiene los parámetros de cada escenario. Los parámetros experimentales se almacenan fuera del código para cambiar las condiciones sin modificar el motor.

Ejemplo:

```yaml
simulation:
  seed: 42
  day_minutes: 480
  replications: 1000

colony:
  active_bees: 100

departures:
  lambda_per_min: 0.20

foraging:
  distance_model: fixed
  distance_km: 2.0
  flower_availability: medium

pollination:
  p_success: 0.70

return:
  model: logistic
```

Los valores utilizados deben identificarse como datos documentados o como supuestos del modelo.

## `generators/`

Contiene únicamente métodos de generación de variables aleatorias.

Ejemplos:

```python
exponential_inverse(...)
poisson_knuth(...)
bernoulli(...)
binomial(...)
lcg(...)
```

No debe contener lógica específica de abejas.

## `models/`

Representa las estructuras principales del sistema.

- `bee.py`: estado de una abeja.
- `trip.py`: información de un viaje.
- `colony.py`: información de la colonia.
- `environment.py`: condiciones del entorno.

Un viaje puede registrar:

```text
bee_id
trip_id
departure_time
distance_km
flowers_visited
flowers_pollinated
nectar_collected
trip_duration
return_probability
returned
```

## `simulation/`

Contiene la lógica del sistema.

- `engine.py`: coordina una ejecución completa.
- `departures.py`: administra las salidas.
- `flowers.py`: modela flores disponibles y visitadas.
- `pollination.py`: determina eventos de polinización.
- `nectar.py`: modela la recolección de néctar.
- `distance.py` y `trip_duration.py`: calculan desplazamiento y duración.
- `return_model.py`: determina el retorno.
- `metrics.py`: calcula métricas de cada corrida.

## `analysis/`

Contiene la parte estadística.

- `validation.py`: validación de muestras.
- `comparison.py`: comparación de métodos y configuraciones.
- `campaign_io.py`: lectura de campañas planas o históricas.

## `experiments/`

- `scenarios.py`: catálogo de los 12 escenarios.
- `runner.py`: ejecución en memoria de escenarios y repeticiones.

## `visualization/`

Contiene la representación visual de resultados:

- histogramas;
- gráficos comparativos;
- curvas de distancia;
- gráficas de polinización;
- gráficas de retorno;
- comparación de escenarios.

La visualización no modifica la lógica del motor.

---

# Métricas principales

Cada corrida puede producir:

- número total de salidas;
- tiempo promedio entre salidas;
- viajes iniciados;
- viajes completados;
- distancia total planificada;
- distancia promedio por viaje;
- flores visitadas;
- flores polinizadas;
- porcentaje de polinización;
- néctar recolectado;
- duración promedio de los viajes;
- tasa de retorno;
- flores polinizadas por viaje;
- flores polinizadas en viajes que caben dentro de la jornada;
- flores polinizadas en viajes con retorno exitoso;
- flores polinizadas por unidad de tiempo;
- flores polinizadas por unidad de distancia.

---

# Reproducibilidad

Todas las simulaciones deben utilizar una semilla controlada.

Ejemplo:

```python
rng = crear_fuente(cfg["simulation"]["rng_source"], cfg["simulation"]["seed"])
```

La semilla debe provenir del archivo de configuración.

Cada conjunto de resultados debe conservar:

```text
semilla
escenario
parámetros
número de repeticiones
fecha de ejecución
```

---

# Instalación

## Requisitos

- Python 3.10 o superior
- `pip`
- entorno virtual recomendado

Crear entorno:

```bash
python -m venv .venv
```

Activar en Windows:

```bash
.venv\Scripts\activate
```

Activar en Linux/macOS:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

---

# Dependencias principales

```txt
numpy
pandas
scipy
matplotlib
pytest
pyyaml
jupyterlab
```

---

# Ejecución

## Simulación individual

```bash
python scripts/run_simulation.py --config config/base.yaml
```

## Experimentos

```bash
python scripts/run_experiment.py --campana --n-replicas 500
```

Si una campaña fue iniciada con una versión anterior del script, sus YAML y
resúmenes pueden actualizarse al terminar sin volver a simular. Primero se
revisa y luego se aplica:

```bash
python scripts/update_campaign_metadata.py --n-replicas 500
python scripts/update_campaign_metadata.py --n-replicas 500 --apply
```

## Validación de generadores

```bash
python scripts/validate_generators.py
```

## Pruebas

Ejecute las pruebas con `src/` en la ruta de importación. En PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m pytest
```

En Bash:

```bash
PYTHONPATH=src python -m pytest
```

---

# Resultados

Los resultados se organizan en:

```text
results/
├── tables/
├── figures/
└── runs/
```

- `runs/`: resultados individuales de todos los escenarios en una carpeta
  plana. Cada CSV se asocia con su escenario mediante el YAML compañero.
- `tables/`: tablas consolidadas.
- `figures/`: gráficas generadas.

La información presentada en el informe debe provenir directamente de los resultados producidos por el código.

---

# Validación estadística

Los generadores deben evaluarse antes de interpretar los resultados de la simulación.

La validación puede considerar:

- media;
- varianza;
- desviación estándar;
- histogramas;
- comparación con valores teóricos;
- pruebas de bondad de ajuste;
- autocorrelación para generadores pseudoaleatorios propios.

Entre las pruebas consideradas:

- Kolmogorov-Smirnov para distribuciones continuas;
- chi-cuadrado para distribuciones discretas.

---

# Comparación de métodos

La comparación considera:

- comportamiento estadístico;
- ajuste a la distribución objetivo;
- estabilidad con diferentes tamaños de muestra;
- reproducibilidad;
- tiempo de ejecución;
- facilidad de implementación.

Los métodos deben ejecutarse bajo condiciones equivalentes.

---

# Convenciones de código

## Variables y funciones

```text
snake_case
```

Ejemplo:

```python
generate_departure_times()
simulate_trip()
calculate_metrics()
```

## Clases

```text
PascalCase
```

Ejemplo:

```python
Bee
Trip
Colony
Environment
```

## Archivos

```text
snake_case.py
```

Evitar nombres ambiguos como:

```text
prueba.py
cosas.py
final.py
final2.py
```

---

# Git y control de versiones

Ramas recomendadas:

```text
main
develop
feature/generators
feature/simulation-engine
feature/distance-return
feature/statistical-validation
feature/visualization
```

Flujo:

```text
feature/*
    ↓
develop
    ↓
main
```

`main` debe conservar únicamente versiones funcionales y reproducibles.

---

# Convención de commits

Ejemplos:

```text
feat: add inverse exponential generator
feat: implement poisson generator
feat: add pollination model
feat: add nectar collection model
feat: add distance dependent return model
test: validate exponential generator
test: validate poisson distribution
docs: document simulation architecture
fix: prevent trips outside simulation horizon
```

---

# Pruebas

Las pruebas automatizadas se almacenan en:

```text
tests/
```

Cada módulo matemático debe verificar:

- comportamiento esperado;
- parámetros inválidos;
- reproducibilidad;
- consistencia estadística básica.

Ejecutar:

```bash
pytest
```

---

# Documentación

La carpeta `docs/` mantiene la documentación técnica complementaria.

- `model.md`: variables y relaciones del sistema.
- `methodology.md`: procedimiento experimental.
- `assumptions.md`: supuestos utilizados para simplificar el sistema.
- `decisions.md`: decisiones técnicas y metodológicas relevantes.
- `f10_resultados.md`: informe final con las 6,000 réplicas de la campaña.
- `presentacion.md`: guion de 12 diapositivas, notas orales y cobertura de la rúbrica.

---

# Principios de diseño

1. Los generadores aleatorios no contienen lógica de abejas.
2. El motor de simulación no genera gráficas.
3. Las visualizaciones consumen resultados del motor.
4. Los parámetros experimentales se encuentran en archivos de configuración.
5. Las semillas se controlan.
6. Los resultados son reproducibles.
7. Las funciones matemáticas pueden probarse de forma aislada.
8. Cada corrida conserva información suficiente para reconstruir el experimento.
9. Los supuestos se documentan.
10. La simulación y el análisis estadístico se mantienen separados de las visualizaciones.

---

# Flujo de trabajo

```text
Configuración
      ↓
Generadores aleatorios
      ↓
Modelos de datos
      ↓
Motor de simulación
      ↓
Registro de resultados
      ↓
Validación estadística
      ↓
Experimentos
      ↓
Comparación
      ↓
Visualización
      ↓
Informe y presentación
```

---

# Entregables asociados al repositorio

El repositorio sirve como soporte para:

- código funcional de la simulación;
- métodos de generación de variables aleatorias;
- pruebas y validación estadística;
- configuraciones experimentales;
- resultados de las ejecuciones;
- gráficas;
- documentación del modelo;
- análisis reproducible;
- recursos utilizados en la presentación.

---

# Contexto académico

**Universidad del Valle de Guatemala**  
Facultad de Ingeniería  
Departamento de Ciencias de la Computación  

**Curso:** CC2017 – Modelación y Simulación  
**Sección:** 20  
**Docente:** Ing. Pablo Koch  

**Tema:** Simulación estocástica del comportamiento de forrajeo y polinización de abejas.

---

# Integrantes

- Ricardo Arturo Godínez Sánchez — 23247
- Vianka Vanessa Castro Ordoñez — 23201v
- Diego Javier López Reinoso - 23747 
- Paula Daniela de León Godoy - 23202 

---

# Uso académico

Repositorio desarrollado con fines académicos para el curso CC2017 – Modelación y Simulación de la Universidad del Valle de Guatemala.

El modelo corresponde a una representación simplificada con fines de modelación computacional y análisis estadístico y no debe interpretarse como una reproducción completa del comportamiento biológico de una colonia real.
