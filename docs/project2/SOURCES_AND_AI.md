# Fuentes, bibliotecas y asistencia de IA

## Datos y referencia del curso

- Davey, M. L. (2023), [Floral resource availability and honeybee flower visitations in Oslo, Norway](https://doi.org/10.5061/dryad.9kd51c5qk), Dryad, CC0. TXT y README locales preservados. Inventario floral 18 julio–4 agosto 2017 según métodos; publicaciones del dataset no son fechas de muestreo.
- Oslo/SPARE, fuentes GIS y URLs REST exactas en `data/project2/sources_spatial.md`. Parques, zonas libres de abejas y servicio de aptitud no son datos Dryad; no se recuperaron valores numéricos de aptitud para estos experimentos.
- UVG, CC3074, Proyecto 2, 2026: PDF de seis páginas, rúbrica de nueve criterios/50 puntos y exposición de máximo 15 min. Nombre/huella del archivo consultado registrados en `rubric_source.json`.

## Técnica adicional: tres fuentes identificables

1. Deb, Pratap, Agarwal y Meyarivan (2002), *A fast and elitist multiobjective genetic algorithm: NSGA-II*, IEEE Transactions on Evolutionary Computation 6(2), 182–197. [DOI 10.1109/4235.996017](https://doi.org/10.1109/4235.996017). Referencia original; el portal editorial no permitió leer el texto completo en esta revisión.
2. [pymoo: NSGA-II, documentación técnica](https://pymoo.org/algorithms/moo/nsga2.html). Selección por frentes, crowding y extremos. Consultada para contraste conceptual; no se usa pymoo como motor de búsqueda.
3. [DEAP: selNSGA2 y herramientas evolutivas](https://deap.readthedocs.io/en/master/api/tools.html#deap.tools.selNSGA2). Referencia de operadores y responsabilidades de evaluación/copia. No se utiliza DEAP en la implementación propia.

Representación propia: conjunto ordenado de K IDs candidatos. Objetivos: maximizar
recurso entregado, minimizar distancia media y presión. Reparación impone catálogo
y K sin IDs duplicados. Selección por rango/crowding, cruce preservando comunes y
mutación por sustitución; ver `nsga2.py` y parámetros YAML (50 individuos, 50 generaciones,
30 réplicas de búsqueda, optimizer_seed 2026). NSGA-II resulta pertinente porque
evita fijar pesos únicos para objetivos en conflicto y entrega alternativas.
GREEDY sirve como contraste interpretable y RANDOM como base sin mejora.
Limitaciones: costo elevado, convergencia no garantizada, estancamiento/diversidad,
objetivos casi constantes y ausencia de calibración ecológica; ver auditoría.

## Software: qué hace la biblioteca y qué hace el proyecto

- NumPy/pandas: cálculos, tablas, RNG PCG64 y bootstrap implementado en el proyecto.
- GeoPandas/Shapely/pyproj: lectura GIS, geometrías y transformación de CRS; filtros,
  política de solapamientos, contratos y motor son del repositorio.
- [FastAPI](https://fastapi.tiangolo.com/): HTTP, OpenAPI y validación Pydantic. El adaptador llama al mismo motor; no contiene una segunda simulación.
- [React](https://react.dev/), TypeScript y [Vite](https://vite.dev/guide/): componentes, tipado, desarrollo/build de interfaz.
- [React Leaflet](https://react-leaflet.js.org/docs/start-setup/) y Leaflet: mapa y capas. Las posiciones de iconos interpolan tiempos registrados; no son trayectorias GPS nuevas.
- Recharts: gráficos; lucide-react: iconos de navegación. SVG de abejas, flores,
  colmena y clima creados para esta interfaz en `components/Art.tsx` y OsloMap.
- OpenStreetMap: mapa base estándar opcional con atribución (https://operations.osmfoundation.org/policies/tiles/). En la revisión visual CARTO devolvió tiles de "API KEY REQUIRED"; se cambió explícitamente solo el mapa base, sin sustituir ninguna fuente GIS. Google Fonts: DM Sans y
  Manrope con fallback de sistema. Estos servicios requieren red y no aportan
  datos ecológicos nuevos al motor.
- Matplotlib: figuras científicas; unittest/Vitest/Testing Library: pruebas;
  Streamlit previo conservado. pypdf: extracción de referencia del curso.

## Uso de inteligencia artificial

Se utilizó Codex/OpenAI para revisión de código/documentos, propuesta de metodología,
implementación React/FastAPI, SVG, scripts de evidencia, pruebas y documentación.
Se ejecutaron pruebas y revisión visual con herramientas automáticas. La asistencia
no constituye una fuente de datos ecológicos ni prueba de validez científica.
No se generaron mediciones, sitios, unidades, autores ni resultados faltantes.
El equipo debe revisar el código, verificar las fuentes, confirmar aportes personales
y declarar este uso en el informe/presentación según las reglas de UVG.
