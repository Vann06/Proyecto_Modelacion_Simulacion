# Auditoría histórica Oslo — estado de esta rama

Rama `feature/project2-validacion-historica-oslo`, desde `integracion/project2-comparacion-app`
en `dff96a3`. No se modificaron los 299 archivos existentes verificados; todos los
entregables de esta fase son nuevos. No hay commit, PR, merge ni simulación histórica.

**Resultado científico: detenerse en el punto de control.** Se extrajeron 506 filas
del anexo de Dietz con coincidencia entre dos lectores PDF y 20 filas cotejadas
visualmente. Hay 216 registros en la ventana 18 julio–4 agosto 2017. Faltan CRS/datum
y posiciones originales verificadas para inicializar el escenario histórico sin
convertir hipótesis en hechos. La diferencia de orígenes inferidos de Ullevål (~3 m)
frente a ~20 cm descritos también requiere aclaración.

Esto no vuelve inútiles los datos: se entregan distribuciones descriptivas,
bootstrap por día, auditoría de errores y cobertura **condicional** de parques.
Además se encontró un GeoTIFF numérico oficial NINA, con resúmenes aproximados
para 686 parques mediante overview publicado; no se convirtió a recursos del motor.

## Abrir evidencia

- `notebooks/project2/09_historical_data_audit.ipynb`: 27 celdas, Run All aprobado.
- `docs/project2/HISTORICAL_VALIDATION.md`: diagnóstico, métodos, tablas e interpretación.
- `results/project2/historical_validation/`: CSV, gráficas, decisión y verificación.
- `data/project2/processed/historical_foraging.csv`: 506 filas preservadas con banderas.
- `data/project2/processed/historical_hives.csv`: orígenes algebraicos, **no sitios verificados**.

El módulo está en `src/bee_sim/analysis/project2_historical_audit.py` para no cambiar
el hash del motor, que incluye todos los `.py` dentro de `src/bee_sim/project2/`.
Los notebooks previos, aplicaciones y resultados de optimización siguen intactos.

## Repetir en Windows

Desde `C:\Projects\Proyecto_Modelacion_Simulacion\.build\integration-worktree`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-historical.txt
.\.venv\Scripts\python.exe scripts/project2_historical_validation.py audit --download-source
.\.venv\Scripts\python.exe scripts/project2_nina_numeric_audit.py
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

El PDF se descarga únicamente a `.build/historical/` (ignorado). La extracción
verifica SHA256, conteos por tabla/colonia, fechas, coincidencia entre lectores y
fixture visual. El notebook puede leer evidencia exportada sin PDF ni red; indica
claramente si no repitió la extracción. Para verificarla localmente se necesita
la caché y PyMuPDF. La prueba específica de extracción se omite explícitamente si
el PDF no está disponible: no se presenta como aprobada en ese caso.

La auditoría NINA usa lecturas parciales HTTP del COG, nunca el TIFF completo de
1,6 GB; la caché numérica reducida (~5,4 MB) tampoco se incorpora a Git. Se conserva
atribución CC-BY 4.0, metadatos y limitaciones de resolución, sentido del índice y
valores fuera de la leyenda nominal. No normalizar ni recortar valores para ajustar
conclusiones.

## Verificación y trabajo pendiente

Pasaron 183 pruebas Python, incluidas diez nuevas. Notebook histórico ejecutado
desde un kernel limpio. `protected_files_check.csv` verifica los 299 archivos de
la base; `verification.json` separa aprobación técnica de viabilidad científica.
React no cambió: no se crearon pantallas ni se afirma un nuevo build de interfaz.

No se generaron métricas simuladas, errores observado/simulado, resultados por seed
ni Jaccard reproducido. `requested_outputs_status.csv` explica cada ausencia.
El comando `simulate` rechaza continuar con la auditoría actual.

Próximo paso humano: obtener CRS/datum, posiciones originales o proyecto R/QGIS,
aclarar anomalías/separación, solicitar superficies de probabilidad y revisar derechos
de reutilización antes de publicación. Después se podrá diseñar la interfaz separada
K=3 y banco independiente de al menos 30 seeds por configuración.
No es necesario repetir NSGA-II ahora. Los cambios ecológicos solo están propuestos
y las conclusiones de optimización conservan su alcance estrictamente sintético.
