# Oslo Pollinator Lab — React + FastAPI

Entrega local en `integracion/project2-comparacion-app`. Streamlit, notebooks 01–08,
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
`C:\Projects\Proyecto_Modelacion_Simulacion\.build\integration-worktree`.
La rama del directorio original permanece separada; no contiene estos cambios.
`frontend/package-lock.json` fija las dependencias JS. Los paquetes científicos
usados quedan registrados en `results/project2/scientific_validation/environment.json`.

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

La comparación histórica usa motor **1.1.0**. Sensibilidad y demos visuales usan
**1.1.1**; los JSON de demo se generaron explícitamente una vez, no al abrir la app.
La semilla común por defecto es réplica 31. Cambiar parámetros y revaluar una
solución NSGA-II guardada no es reoptimizarla. K diferente de cinco requiere otro
frente; la API rechaza truncar o completar sus sitios. Sitios manuales exigen K
IDs válidos y distintos; el contrato aún permite IDs con coordenadas coincidentes.

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
- `notebooks/project2/08_final_results.ipynb`: síntesis final con tablas, diferencias pareadas, Pareto y sensibilidad, en la rama de cierre científico.
- `docs/project2/FINAL_SCIENTIFIC_SYNTHESIS.md`: interpretación consolidada para el informe.
- `docs/project2/FINAL_DELIVERY_CHECKLIST.md`: pruebas locales, PDF, diapositivas y defensa pendientes.

Faltan calibración del motor en unidades observadas, más optimizer seeds,
correspondencia espacial trap/parque e informe/diapositivas finales del equipo.
Ninguna animación ni mejora en RU reemplaza esos requisitos científicos.
