# Cierre del frontend React: alcance y matriz de aceptación

Rama local `feature/project2-entrega-final`, base `integracion/project2-comparacion-app`
en `dff96a37056b668c48a40080d80783b4f0e817be`. Worktree separado:
`C:\Projects\Proyecto_Modelacion_Simulacion\.build\entrega-final-worktree`.
La investigación personal permanece en su worktree y no se integra por merge.
No hay commit, push, PR ni publicación. No se ejecuta búsqueda NSGA-II ni simulación histórica.

## Auditoría de la base y mejoras

La auditoría inicial leyó App, componentes, API, tipos, visualización, backend,
pruebas y documentación. Ya funcionaban las siete páginas, mapa, reproducción,
frente congelado, comparación con IC, referentes Dryad, sensibilidad archivada,
escenarios exploratorios y descargas. Se conservaron y ampliaron esas funciones.

| Sección | Funcionalidad existente | Mejora realizada | Fuente | Archivos principales | Aceptación | Prioridad |
| --- | --- | --- | --- | --- | --- | --- |
| Inicio | Contexto, fuentes y navegación | Pregunta, justificación de K/horizonte y recorrido con botones | overview, configuración y contrato | App.tsx | Navegar a etapas; no afirmar capacidad real ni calibración | P1 |
| Oslo | Mapa, capas y ficha | Controles independientes de parques/colmenas/radio; selección por lista; superficie exclusiva, recurso inicial y distancias métricas | landscape, resource_patches, logs | OsloMap.tsx, MapControls.tsx, App.tsx, evidence.ts | Capas locales sin mapa base; consulta de parque; distancia punto-punto | P1 |
| Movimiento | Viajes interpolados y reloj | Inspector seleccionable por mapa/lista, eventos reales del log, entregas por colmena, balances y CSV del día/18 días | react_demo o corrida exploratoria | TripResources.tsx, Common.tsx, types.ts | No inventar regreso; balance inicial−consumo+regeneración=final | P0 |
| Optimización | Medias, IC, Pareto e historia | Métricas de solución seleccionada, restricciones, coordenadas duplicadas y cambios descriptivos frente a ambas referencias | comparación archivada y front | EvidencePanels.tsx, evidence.ts | Cambiar solución actualiza métricas y mapa sin buscar ni reutilizar IC ajenos | P0 |
| Validación | Predictores Dryad fuera de muestra | Resumen Dietz, cierre NINA y matriz de nueve métricas | selected_validation y scientific_validation | EvidencePanels.tsx, main.py | 216 registros; RU no comparable; errores Dryad separados | P0 |
| Sensibilidad | 14 condiciones y sliders | Base/condición, media/DE/IC, cambios pareados y desempeño por colmena | sensitivity_v111 | EvidencePanels.tsx, service.py | K3/K8 sin NSGA; base propia 1.1.1; cero no equivale a ausente | P0 |
| Resultados | Cambios y descargas | Recurso y distancia, condiciones, límites y paquete de evidencia organizado | archived_changes y comparación | App.tsx | Cifras coinciden con CSV; mejoras solo simuladas | P1 |

Glosario de siete términos en todas las páginas, ayudas de parámetros, navegación
en exposición y ajustes adaptables. La información por colmena para cada solución
histórica se limita a promedio, mínimo y Jain: no hay cinco entregas individuales
por solución/seed en el archivo utilizado. Las entregas individuales de las demos
1.1.1 se muestran separadas y no sustituyen las medias de evaluación 1.1.0.

## Integridad y separación científica

- Motor y optimizadores intactos. Resultados históricos, GIS, Dryad, sensibilidad y
  demos originales intactos: se comprueban por hashes contra la base.
- Solo cuatro archivos científicos seleccionados: resumen Dietz, decisión NINA,
  correspondencia y procedencia. No se copian los 60 archivos, PDF, rásteres,
  coordenadas inferidas ni registros individuales de investigación.
- `scripts/project2_select_validation.py` documenta la selección y se niega a
  sobrescribir el paquete. Su fuente es un checkout local de investigación.
- La entrega usa los CSV resumidos como entradas. Permite reproducir su lectura,
  presentación y cálculos; **no afirma reproducir la extracción PDF ni la auditoría
  NINA completa**, conservadas localmente. Las huellas de fuentes están en provenance.
- Dietz no es una observación emparejada de nuestras cinco colonias. IC por fecha,
  dependencia y muestreo selectivo limitan el contraste. No hay MAE del motor.
- NINA queda cerrado como NO APTO para ordenar instalaciones por calidad ecológica.
- Dryad conserva sus errores de referentes estadísticos, sin conversión a RU.
- `display_name` repara de forma reversible algunos nombres con mojibake únicamente
  para presentación. `Navn` original permanece en el payload y en los archivos fuente.
- Accesibilidad en la ficha: distancia euclidiana EPSG:25833 entre puntos originales,
  no geometrías simplificadas ni distancia al borde; círculos de radio son ilustrativos.
- Los tiempos del inspector consultan eventos efectivos: un tiempo programado sin
  evento no se presenta como regreso realizado. Las entregas son finales del viaje,
  independientemente del minuto actual de reproducción; no se predicen con animación.

## Verificación por fases

- Base: 8 pruebas frontend y 173 Python aprobadas. La ejecución Python inicial en
  aislamiento se interrumpió al bloquearse; se repitió completa fuera de él.
- Componentes P0: 22 pruebas frontend; 4 pruebas nuevas de endpoints y evidencia.
- Suite de regresión tras P0: 177 Python aprobadas en 90,361 s.
- Ajuste posterior de etiquetas: añade una quinta prueba específica. El resultado
  final y las comprobaciones visuales se registran en `FRONTEND_VERIFICATION.json`.
- TypeScript y Vite compilan sin modificar dependencias. Las pruebas usan la API
  real y archivos del repositorio; las de evidencia parchean simulate para prohibir
  llamadas accidentales. La suite original mantiene sus casos pequeños del motor.

No se atribuye a las pruebas automáticas verificación de mapas o calidad visual;
las interacciones de navegador y capturas se documentan por separado. Los escenarios
exploratorios conservan su API; no son una nueva campaña experimental.

## Reproducir y revisar

La instalación estándar y dos terminales están en README_REACT.md. En esta sesión
se reutilizó el Python ya configurado del checkout de investigación y se ejecutó
`npm ci` en el nuevo worktree, sin copiar resultados ni entorno al repositorio.
Pruebas:

```powershell
$env:PYTHONPATH='src;.'
python -m unittest discover -s tests -v
Set-Location frontend
npm test
npm run build
```

El build puede servirse con FastAPI en loopback. Se verificó la entrega en un
puerto separado del 8000 usado por otra instancia. Los servicios de comprobación
se detienen al finalizar; no se publica un servidor.

## Traslado a informe y presentación

Para Word: incorporar pregunta/alcance, tabla histórica con IC, diferencias pareadas,
sensibilidad con base 1.1.1, tabla Dryad y matriz de equivalencias. Dietz y cierre NINA
son contraste y limitaciones, no validación predictiva lograda. No se editó el Word.

Para exposición: Inicio → Oslo → un viaje y balance → Pareto → comparación →
sensibilidad → validación y conclusiones. Usar demos guardadas; una corrida nueva
es exploración, no prueba de robustez. El modo exposición conserva navegación.
Confirmar nombres/aportes y ensayar los 15 minutos con margen para defensa.

Pendientes científicos conservados: calibración en unidades físicas, operador de
observación, múltiples búsquedas independientes y política física de colocalización.
No se abren aquí nuevas investigaciones ni funcionalidades para resolverlos.
