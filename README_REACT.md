# Oslo Pollinator Lab — React + FastAPI

Entrega local en `feature/project2-entrega-final`, desde `integracion/project2-comparacion-app`
en `dff96a3`. Streamlit, notebooks 01–08,
motor y resultados históricos se conservan. No se inicia NSGA-II completo desde la
interfaz ni al cargar datos. La API llama al motor Python; JavaScript únicamente
interpela visualmente intervalos de viajes registrados y representa sus stocks.

## Instalación en Windows

Requisitos: Python 3.10+ y Node.js 22.20+ (entorno comprobado). Desde la raíz de
**este checkout**, no desde otro worktree:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Set-Location frontend
npm ci
Set-Location ..
```

El checkout de esta sesión es
`C:\Projects\Proyecto_Modelacion_Simulacion\.build\entrega-final-worktree`.
La rama del directorio original permanece separada; no contiene estos cambios.
`frontend/package-lock.json` fija las dependencias JS. Los paquetes científicos
usados quedan registrados en `results/project2/scientific_validation/environment.json`.

Para revisar este worktree con el Python ya disponible en esta máquina, sin crear
otro entorno, después de `npm run build` en `frontend`:

```powershell
Set-Location C:\Projects\Proyecto_Modelacion_Simulacion\.build\entrega-final-worktree
& C:\Projects\Proyecto_Modelacion_Simulacion\.build\integration-worktree\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8011
```

Abrir http://127.0.0.1:8011. Esta alternativa reutiliza solo el intérprete y las
bibliotecas; carga código y datos del worktree de entrega. La instalación estándar
anterior sigue siendo la opción portable. El servidor de comprobación de la sesión
se detiene al terminar; no se modifica la instancia que pueda existir en el 8000.

## Desarrollo: dos terminales

Terminal 1, raíz:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
Set-Location frontend
npm run dev
```

Abrir http://127.0.0.1:5173. Vite envía `/api` al puerto 8000. Documentación HTTP:
http://127.0.0.1:8000/docs. Ambos servicios escuchan solo en loopback.

## Presentación con una sola terminal

```powershell
Set-Location frontend
npm run build
Set-Location ..
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Compilar **antes** de iniciar FastAPI; abrir http://127.0.0.1:8000. No hace falta
Vite en este modo. Fuentes tipográficas y mapa base requieren Internet, pero hay
fuentes de sistema y el filtro Mapa base permite usar las capas locales sin tiles.
No publicar este servidor de demostración directamente en Internet: no implementa
usuarios, cola durable ni almacenamiento de experimentos multiusuario.

## Pantallas y procedencia

1. Inicio: pregunta, fuentes, entidades y diagrama del flujo científico.
2. Oslo: 737 parques, geometrías exclusivas de recurso, seis zonas restringidas,
   candidatos, colmenas, filtros y ficha de parque al seleccionarlo.
3. Movimiento: logs guardados, play/pausa, velocidad visual, día/minuto, búsqueda,
   forrajeo, regreso, stock y contexto de temperatura cuando hay sesiones.
4. Optimización: 70 seeds comunes, nueve métricas, IC, cambios absolutos/porcentuales,
   frente interactivo, ubicaciones y evolución de búsqueda. No un ganador universal.
5. Validación: referentes empíricos fuera de muestra y comparación explícitamente
   no disponible entre RU/viajes y mediciones de Dryad.
6. Sensibilidad: 1 200 réplicas archivadas + controles para **una** corrida nueva
   exploratoria. Su resultado solo vive en memoria de la pestaña; no se sobreescribe
   evidencia. Guardar parámetros/provenance del panel para reproducirla.
7. Resultados: conclusiones acotadas, descargas y modo exposición.

El cierre incorpora un inspector de eventos por viaje, balances de recursos de los
18 días y descargas de logs filtrados. El comparador de soluciones conserva la
comparación oficial y distingue IDs de coordenadas. Sensibilidad dispone de base/
condición, diferencias, IC y desempeño por colmena sin nuevas simulaciones.

Validación usa solo cuatro archivos en `results/project2/selected_validation/`:
resumen Dietz (216 registros), cierre NINA NO APTO, matriz de correspondencia y
procedencia. La extracción PDF y las auditorías completas permanecen en la rama
local de investigación. Los errores Dryad siguen perteneciendo a referentes
estadísticos independientes. No se trasladan rásteres ni ubicaciones inferidas.
Los detalles de alcance, aceptación y pruebas están en
`docs/project2/FRONTEND_DELIVERY.md` y `FRONTEND_VERIFICATION.json`.

La comparación histórica usa motor **1.1.0**. Sensibilidad y demos visuales usan
**1.1.1**; los JSON de demo se generaron explícitamente una vez, no al abrir la app.
La semilla común por defecto es réplica 31. Cambiar parámetros y revaluar una
solución NSGA-II guardada no es reoptimizarla. El modo histórico conserva K=5;
la API rechaza truncar o completar sus sitios. El modo rápido genera su propio frente con K variable. Sitios manuales exigen K
IDs válidos y distintos; el contrato aún permite IDs con coordenadas coincidentes.

## NSGA-II rápido en Configura una pregunta

Disponible en los mismos controles de Movimiento y Sensibilidad: seleccionar NSGA2,
Modo NSGA-II → Nueva optimización rápida, ajustar K/escenario y pulsar Ejecutar
búsqueda rápida. No se dispara al mover sliders. Población 8, cinco generaciones,
dos réplicas de búsqueda (1–2), cruce 0.90, mutación 0.20 y seed 2026 fijos.
Reutiliza `run_nsga2`, `SimulationEvaluator`, reparación, caché y checkpoints;
no modifica el motor ni busca con las 70 seeds de evaluación histórica.

La API inicia un proceso controlado, permite **un trabajo a la vez por servidor
local de un solo worker**, máximo 96 simulaciones y 15 minutos. No usar `--workers`
para este servidor de demostración. Al detenerlo termina su proceso de búsqueda.
Una búsqueda interrumpida no publica el frente provisional como definitivo.

Endpoints: `POST /api/quick-nsga2`, `GET /api/quick-nsga2/{job_id}` y
`POST /api/quick-nsga2/{job_id}/simulate` (solution_id y replication_id 31–100).
Los archivos de cada UUID quedan en `results/project2/quick_nsga2/`, ignorados por
Git: solicitud, metadatos/huellas, evaluación, checkpoint, frente, historia y
simulaciones individuales. Ningún resultado histórico se sobrescribe.

Seleccionar un punto solo muestra sus K ubicaciones. Simular solución seleccionada
usa el escenario **guardado al iniciar la búsqueda**, aunque después cambien los
sliders. Los viajes y métricas individuales son distintos del promedio de las dos
seeds de búsqueda. No es un óptimo global ni una nueva comparación científica
contra los resultados de 70 réplicas.

Verificación real y tiempos: `python scripts/project2_verify_quick_nsga.py`
(cinco búsquedas acotadas, no es necesario al abrir la app). Reporte en
`docs/project2/QUICK_NSGA_VERIFICATION.json`. Pruebas de interfaz con un frente real
ya calculado: `scripts/project2_verify_quick_ui.cjs`; ese ensayo no repite NSGA-II.

## Reproducir evidencia (no necesario para abrir)

```powershell
.\.venv\Scripts\python.exe scripts/project2_scientific_validation.py
.\.venv\Scripts\python.exe scripts/project2_sensitivity.py --workers 4
.\.venv\Scripts\python.exe scripts/project2_prepare_demo.py
```

Sensibilidad y preparación de demo rechazan sobrescribir las cohortes existentes.
Para otra cohorte se debe cambiar explícitamente la carpeta de salida en una copia
versionada del script; no borrar resultados históricos. El primer script regenera
solo sus derivados de auditoría, nunca Dryad ni CSV históricos.

## Pruebas

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Set-Location frontend
npm test
npm run build
npm audit
```

El navegador debe comprobar también mapas/animación: los tests numéricos no prueban
renderizado WebGL/SVG. La UI usa Leaflet y limita a 400 los íconos de viajes activos,
con conteo explícito; polígonos simplificados solo para presentación. La reproducción
se detiene al final del día y al cambiar de pantalla. Las velocidades del player
cambian únicamente el reloj visual, nunca las reglas del motor.

## Documentación científica

- `docs/project2/REAL_WORLD_VALIDATION.md`: metodología, errores y límites empíricos.
- `docs/project2/SCIENTIFIC_AUDIT.md`: identidad, notebooks, IC y frente.
- `docs/project2/SENSITIVITY_RESULTS.md`: diseño, parámetros e interpretación.
- `docs/project2/RUBRIC_MATRIX.md`: los nueve criterios oficiales, sin inventar nota.
- `docs/project2/DEMO_SCRIPT.md`: guion de 15 minutos y participación del equipo.
- `docs/project2/SOURCES_AND_AI.md`: bibliotecas, referencias y uso de IA.
- `notebooks/project2/09_scientific_evidence.ipynb`: lectura ejecutable de evidencia nueva.

Faltan calibración del motor en unidades observadas, más optimizer seeds,
correspondencia espacial trap/parque e informe/diapositivas finales del equipo.
Ninguna animación ni mejora en RU reemplaza esos requisitos científicos.
