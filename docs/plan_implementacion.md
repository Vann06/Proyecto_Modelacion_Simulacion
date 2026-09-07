# Estado actual de implementación

Este documento reemplaza el plan histórico. Describe únicamente lo que existe
en la versión actual del repositorio y los pasos pendientes de ejecución antes
de producir el informe final.

## 1. Implementación disponible

- Generadores propios: LCG, uniforme, exponencial, Poisson, Bernoulli, Gamma,
  Weibull, Normal, Binomial y Binomial Negativa.
- Dos construcciones equivalentes del proceso de salidas: interarribos
  exponenciales y conteo Poisson con uniformidad condicional.
- Motor de jornada con población finita, disponibilidad floral, distancia,
  visitas, polinización, néctar, duración, retorno y saturación.
- Doce escenarios configurables mediante YAML.
- Persistencia de CSV, configuración y resumen por réplica.
- Validación estadística, comparación de métodos y visualizaciones.
- Notebooks ejecutables para verificación, análisis y figuras.
- Pruebas automatizadas para generadores, motor, métricas, persistencia,
  escenarios, equivalencia y lectura de campañas.

## 2. Campaña experimental

La campaña final contiene 12 escenarios y 500 réplicas por escenario: 6,000
réplicas. Se ejecuta desde la raíz con:

```bash
python scripts/run_experiment.py --campana --n-replicas 500
```

Todos los archivos se escriben de forma plana en `results/runs/`. Cada réplica
produce:

```text
run_XXXX.csv
run_XXXX_config.yaml
run_XXXX_summary.json
```

El YAML compañero identifica el escenario y registra la semilla, índice de
réplica, número total de réplicas y fecha UTC. El archivo
`semillas_campana.json` conserva el conjunto compartido de semillas dispersas.

Los lectores también aceptan la estructura histórica
`results/campana/<escenario>/`, pero no es la salida canónica.

## 3. Análisis y figuras

Después de terminar la campaña se ejecutan, en orden:

1. `notebooks/02_scenario_analysis.ipynb`;
2. `notebooks/03_final_figures.ipynb`.

Ambos leen `results/runs/` y no vuelven a simular. El segundo exporta 12 figuras
a `results/figures/`.

La validación independiente se ejecuta con:

```bash
python scripts/validate_generators.py --n 20000 --replicas 200
```

La equivalencia entre métodos se decide con TOST pareada y un margen práctico
de ±1%. El test de diferencia se conserva como información complementaria.

## 4. Definiciones que debe usar el informe

- `flores_polinizadas`: resultado planificado de todos los viajes iniciados;
- `flores_polinizadas_viajes_que_caben`: viajes completos en tiempo dentro del
  horizonte, sin exigir retorno probabilístico;
- `flores_polinizadas_viajes_completos`: viajes con retorno exitoso.

El informe debe indicar qué definición usa. Las tablas históricas emplean la
primera.

La distancia cambia a la vez la duración y el retorno logístico. Con los 12
escenarios actuales no se puede atribuir causalmente el efecto total a uno solo
de esos mecanismos.

La combinación FLORES-BAJA + DIST-LEJOS no debe interpretarse con una suma que
produce conteos negativos. En escala multiplicativa, la predicción y el valor
observado son prácticamente iguales.

## 5. Documentos vigentes

| Documento | Contenido |
|---|---|
| `docs/model.md` | especificación matemática y orden de generación |
| `docs/methodology.md` | diseño experimental y criterios estadísticos |
| `docs/assumptions.md` | parámetros no calibrados y limitaciones |
| `docs/decisions.md` | decisiones técnicas vigentes |
| `docs/f10_resultados.md` | borrador del informe escrito |

## 6. Pendiente antes de entregar

- Esperar a que termine la campaña actualmente en ejecución.
- Si esa campaña comenzó antes de las correcciones, revisar y aplicar
  `scripts/update_campaign_metadata.py --n-replicas 500` después de que termine;
  esto corrige YAML y agrega las métricas nuevas a los resúmenes desde los CSV.
- Revisar `semillas_campana.json`: la reparación documenta las semillas realmente
  usadas, pero no convierte una campaña ya ejecutada con semillas consecutivas
  en una campaña con semillas dispersas.
- Verificar que existan 6,000 tríos completos de archivos y que no haya corridas
  parciales.
- Ejecutar los notebooks 02 y 03 sobre esa campaña.
- Actualizar las cifras del informe si los nuevos resultados difieren de las
  tablas históricas.
- Insertar o exportar las 12 figuras en el documento final.
- Preparar y revisar por separado la presentación oral.

No debe iniciarse una segunda campaña mientras la actual siga escribiendo en la
misma carpeta.
