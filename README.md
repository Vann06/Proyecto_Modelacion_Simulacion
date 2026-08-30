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

La estructura permite ejecutar diferentes configuraciones sin modificar el código principal.

### Condición base

Representa una jornada bajo parámetros intermedios de actividad, distancia y disponibilidad floral.

### Pocas flores

Reduce la disponibilidad floral para observar su efecto sobre flores visitadas, polinización, néctar, duración y eficiencia.

### Muchas flores

Incrementa la disponibilidad floral para analizar cómo cambia el rendimiento global.

### Flores cercanas

Las zonas florales se encuentran a menor distancia de la colmena.

### Flores lejanas

Las zonas florales se encuentran a mayor distancia, permitiendo analizar su efecto sobre duración, distancia total, viajes completados, retorno y polinización.

### Variación de población activa

Permite modificar la cantidad de abejas activas para estudiar cómo cambia el desempeño general de la colonia.

---

# Arquitectura del repositorio

```text
proyecto-abejas-polinizacion/
│
├── README.md
├── requirements.txt
├── .gitignore
├── pyproject.toml
│
├── config/
│   ├── base.yaml
│   ├── escenario_pocas_flores.yaml
│   ├── escenario_muchas_flores.yaml
│   ├── escenario_cercano.yaml
│   └── escenario_lejano.yaml
│
├── src/
│   └── bee_sim/
│       ├── __init__.py
│       ├── generators/
│       │   ├── __init__.py
│       │   ├── uniform.py
│       │   ├── exponential.py
│       │   ├── poisson.py
│       │   ├── bernoulli.py
│       │   ├── binomial.py
│       │   └── lcg.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── bee.py
│       │   ├── trip.py
│       │   ├── colony.py
│       │   └── environment.py
│       ├── simulation/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── departures.py
│       │   ├── flowers.py
│       │   ├── pollination.py
│       │   ├── nectar.py
│       │   ├── travel.py
│       │   ├── return_model.py
│       │   └── metrics.py
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── validation.py
│       │   ├── experiments.py
│       │   └── comparison.py
│       └── visualization/
│           ├── __init__.py
│           ├── plots.py
│           └── animation.py
│
├── scripts/
│   ├── run_simulation.py
│   ├── run_experiments.py
│   └── validate_generators.py
│
├── tests/
│   ├── test_exponential.py
│   ├── test_poisson.py
│   ├── test_bernoulli.py
│   ├── test_binomial.py
│   ├── test_return_model.py
│   └── test_simulation.py
│
├── notebooks/
│   ├── 01_validacion_generadores.ipynb
│   └── 02_analisis_resultados.ipynb
│
├── data/
│   ├── raw/
│   └── processed/
│
├── results/
│   ├── tables/
│   ├── figures/
│   └── runs/
│
├── docs/
│   ├── modelo.md
│   ├── metodologia.md
│   ├── supuestos.md
│   └── decisiones.md
│
└── presentation/
    └── assets/
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
- `travel.py`: calcula desplazamientos y duración.
- `return_model.py`: determina el retorno.
- `metrics.py`: calcula métricas de cada corrida.

## `analysis/`

Contiene la parte estadística.

- `validation.py`: validación de muestras.
- `experiments.py`: ejecución de escenarios y repeticiones.
- `comparison.py`: comparación de métodos y configuraciones.

## `visualization/`

Contiene la representación visual de resultados:

- histogramas;
- gráficos comparativos;
- curvas de distancia;
- gráficas de polinización;
- gráficas de retorno;
- comparación de escenarios;
- animación de la simulación.

La visualización no modifica la lógica del motor.

---

# Métricas principales

Cada corrida puede producir:

- número total de salidas;
- tiempo promedio entre salidas;
- viajes iniciados;
- viajes completados;
- distancia total recorrida;
- distancia promedio por viaje;
- flores visitadas;
- flores polinizadas;
- porcentaje de polinización;
- néctar recolectado;
- duración promedio de los viajes;
- tasa de retorno;
- flores polinizadas por viaje;
- flores polinizadas por unidad de tiempo;
- flores polinizadas por unidad de distancia.

---

# Reproducibilidad

Todas las simulaciones deben utilizar una semilla controlada.

Ejemplo:

```python
rng = np.random.default_rng(seed)
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

- Python 3.11 o superior
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
```

---

# Ejecución

## Simulación individual

```bash
python scripts/run_simulation.py --config config/base.yaml
```

## Experimentos

```bash
python scripts/run_experiments.py
```

## Validación de generadores

```bash
python scripts/validate_generators.py
```

## Pruebas

```bash
pytest
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

- `runs/`: resultados individuales.
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

- `modelo.md`: variables y relaciones del sistema.
- `metodologia.md`: procedimiento experimental.
- `supuestos.md`: supuestos utilizados para simplificar el sistema.
- `decisiones.md`: decisiones técnicas y metodológicas relevantes.

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
10. La simulación y el análisis estadístico se mantienen separados de la animación.

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
- Vianka Vanessa Castro Ordoñez — 23201

---

# Uso académico

Repositorio desarrollado con fines académicos para el curso CC2017 – Modelación y Simulación de la Universidad del Valle de Guatemala.

El modelo corresponde a una representación simplificada con fines de modelación computacional y análisis estadístico y no debe interpretarse como una reproducción completa del comportamiento biológico de una colonia real.
