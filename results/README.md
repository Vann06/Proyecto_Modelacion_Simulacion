# Resultados

La disposición canónica de una campaña es plana:

```text
results/
├── runs/
│   ├── semillas_campana.json
│   ├── run_0001.csv
│   ├── run_0001_config.yaml
│   └── run_0001_summary.json
├── tables/
└── figures/
```

Cada réplica conserva el CSV de viajes, la configuración exacta y el resumen.
El YAML registra escenario, semilla realmente utilizada, índice de réplica,
número de réplicas solicitado y fecha UTC.

Los notebooks 02 y 03 identifican el escenario mediante el YAML compañero y
también pueden leer la estructura histórica con una subcarpeta por escenario.
Para no mezclar ejecuciones, seleccionan las 500 corridas más recientes de cada
escenario.

Nunca se debe conservar únicamente una gráfica: todas las figuras deben poder
reconstruirse desde los archivos de `runs/`. Las carpetas voluminosas se ignoran
en Git; antes de entregar el informe debe verificarse que sus figuras hayan sido
exportadas o incorporadas al documento final.
