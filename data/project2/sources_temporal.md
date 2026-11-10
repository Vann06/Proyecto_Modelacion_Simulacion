# Evidencia temporal — Oslo, Proyecto 2

## Fuentes

- Dryad: *Floral resource availability and honeybee flower visitations in Oslo, Norway*. DOI: [10.5061/dryad.9kd51c5qk](https://doi.org/10.5061/dryad.9kd51c5qk). Se usan los dos TXT locales, sin alterarlos; su README está en `raw/oslo/README.md`.
- Davey et al. (2024; publicación en línea en 2023), *Seasonal variation in urban pollen resource use by north temperate European honeybees*, Urban Ecosystems 27:515–529. DOI: [10.1007/s11252-023-01458-1](https://doi.org/10.1007/s11252-023-01458-1). Consulta: 30 de octubre de 2026, Guatemala.

## Alcance de la evidencia externa

El artículo documenta polen recolectado quincenalmente entre junio y septiembre de 2017 y cambios en su composición. Sus métodos sitúan los inventarios florales del 18 de julio al 4 de agosto de 2017, con una visita floral por sitio, y las observaciones de visitas del 18 de julio al 10 de agosto. Esto permite contextualizar el año ausente en fechas florales, conservando una bandera de inferencia.

## Decisiones propias del modelo

El artículo se usa como respaldo temporal y fenológico cualitativo. No se transcriben porcentajes de ADN como abundancia floral, masa de polen o néctar. No se importan nuevos datos de polen ni se asignan factores numéricos externos.

Como análisis exclusivamente exploratorio, el notebook conserva un indicador saturado respecto de la mayor mediana mensual de densidad por sitio de la muestra Dryad. Julio y agosto son proxies de grupos distintos de sitios; no constituyen una trayectoria longitudinal ni demuestran una disminución temporal del 23.9%. Junio y septiembre carecen de estimación puntual: se conserva el dominio admisible [0, 1], sin interpretarlo como intervalo de confianza o evidencia de ausencia. Los desplazamientos early/late y la dispersión lognormal son herramientas de sensibilidad; no son observaciones, calibraciones fenológicas ni recursos diarios automáticos.

## Decisión actualizada: horizonte diario principal

- `calibrated_window`: intersección de las ventanas de inventarios y visitas, 18 de julio–4 de agosto de 2017. Resolución diaria para futura calibración, validación y experimentos principales. El nombre no implica que el modelo ya esté ajustado.
- `observed_visitation_extension`: se conservan las observaciones de visitas hasta el 10 de agosto, sin asumir inventarios florales posteriores al día 4. Pertenecer al intervalo no significa tener una observación cada día.
- `supported_season`: junio–septiembre como contexto cualitativo y sensibilidad; no validación cuantitativa de cuatro meses equivalentes.
- `exploratory_annual`: enero–diciembre como arquitectura futura, sin curva anual ni recursos asignados. Fuera de la ventana principal se distingue extrapolación respaldada estacionalmente de extrapolación exploratoria.

`simulation_calendar.csv` conserva días sin datos como ausencias y separa ventanas de muestreo de fechas con registros efectivos. `annual_calendar.csv` mantiene los campos futuros de recurso y colonia sin parametrizar. `temporal_variable_metadata.csv` clasifica las variables para uso posterior; `temporal_horizons.csv` persiste el alcance. `resource_scenarios.csv` prepara low/reference/high sin fijar multiplicadores. Las tablas mensuales previas quedan etiquetadas como exploratorias. El siguiente módulo validará antes de comparar estrategias o parametrizar R_j(t).
