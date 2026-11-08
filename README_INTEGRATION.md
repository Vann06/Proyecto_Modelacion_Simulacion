# Integración de Proyecto 2

Rama: `integracion/project2-comparacion-app`. Integra las historias de `RANDOM`,
`feature/GREEDY` y `feature/NGSA-II` (nombre original de la rama). No reemplaza sus
resultados ni exige repetir la búsqueda histórica.

## Ejecutar en Windows

Desde la raíz de esta rama:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

Abrir la dirección local indicada por Streamlit, normalmente http://localhost:8501.
La comparación está disponible al abrir. En **Mapa y escenario**, pulsar
**Simular escenario**, elegir día y mover minuto. Los cambios de sliders requieren
volver a pulsar el botón; se señala cuando hay cambios pendientes.

Los íconos de abejas representan viajes activos del log, con interpolación visual
lineal entre puntos de salida/llegada. No representan individuos identificados ni
trayectorias GPS observadas. El mapa base opcional necesita Internet; las capas
locales funcionan sin él. Los sliders son supuestos del escenario, no efectos
causales estimados. NSGA-II guardado reevalúa ubicaciones, no ejecuta otra búsqueda.

```powershell
.\.venv\Scripts\python.exe scripts/project2_compare.py
.\.venv\Scripts\python.exe -m unittest discover -s tests/project2 -v
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m bee_sim.project2.strategies.nsga2 search --dry-run
```

La búsqueda nueva usa `results/project2/nsga2_fast`, caché con identidad completa,
checkpoint y presupuesto predeterminado de 3 000 simulaciones nuevas por invocación.
Para continuar se vuelve a invocar; cambiar el presupuesto no cambia los objetivos.
Una generación se guarda solo al completarla; los cálculos de la generación parcial
pueden recuperarse de la caché. El límite se comprueba antes de cada lote: puede
quedar saldo insuficiente para empezar el siguiente lote. Cambiar motor/configuración
requiere otra carpeta/cohorte. `holdout` escribe `holdout_results.csv` en esa carpeta.
No mezclar estas salidas 1.1.1 con los resultados archivados del motor 1.1.0.

## Entregables

- `notebooks/project2/05_baselines.ipynb` a `08_final_results.ipynb`: revisión,
  comparaciones e interpretación, ejecutables sin repetir optimización.
- `results/project2/integration/`: auditoría de identidades, resúmenes, diferencias
  pareadas, IC 95%, figuras, deduplicación física del frente y perfil de rendimiento.
- `docs/project2/INTEGRATION_REVIEW.md`: hallazgos técnicos y limitaciones.
- `app/app.py`: presentación y evaluación interactiva mediante el motor común.

Pendiente: calibración ecológica, sensibilidad, varias semillas del optimizador y
decidir si se prohíben distintas IDs con las mismas coordenadas. Los recursos son
`synthetic_RU`, no néctar/polen medidos. No es una recomendación ecológica validada.
