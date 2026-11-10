# Verificación de la entrega React y evidencia científica

Comprobado el 7 de noviembre de 2026 (Guatemala), rama
`integracion/project2-comparacion-app`, base `1896a6d`. Sin commit ni push nuevos.

| Comprobación | Resultado |
| --- | --- |
| Suite completa Python (Proyecto 1 + Proyecto 2 + API/evidencia) | 173 pruebas aprobadas |
| Pruebas específicas API/evidencia después del ajuste final | 7 aprobadas; incluye build servido por FastAPI |
| Vitest/Testing Library | 8 pruebas aprobadas |
| TypeScript + Vite build | Aprobado; módulos separados para mapa y gráficas |
| Auditoría npm tras actualización de Vitest | 0 vulnerabilidades reportadas |
| Notebook 09 en kernel limpio | Run All aprobado, salidas guardadas |
| Notebooks 01–08 y 06.2 | Fuentes/salidas históricas revisadas y preservadas; no se afirma nueva ejecución Run All de toda la descarga GIS |
| Sensibilidad | 1 200 filas, 14 condiciones; 30 seeds comunes por método/condición disponible; identidad 1.1.1 única |
| Comparación histórica | 70 seeds comunes, identidades 1.1.0 compatibles, porcentajes no definidos con base cero |
| Referentes empíricos | Sin fuga de sitios; 30 bootstrap de ajuste; MAE/RMSE e IC por sitio |
| Revisión visual en Edge | Siete pantallas, play/pausa, mapa/viajes, cambio de solución, escenario sin recursos y diseño de 390 px |
| Preservación | Sin diff en motor, Streamlit, notebooks anteriores ni resultados históricos; solo directorios de evidencia nuevos |

Casos de API: K/tipos/rangos inválidos, configuración ajena, IDs extraños o
duplicados, NSGA-II con K distinto de cinco, solución inexistente, semillas fuera
del banco, exclusión de ejecución concurrente, descargas restringidas, misma seed
reproduce, ausencia de recursos no genera viajes, demo no llama a simulate.

Casos frontend: ausencia antes de salida/después de regreso, interpolación de
ida/búsqueda/forrajeo/retorno, no inventar regreso ausente, consumo desde su evento,
regeneración al cierre, métricas indefinidas, límites visibles y enlaces de descarga.

Hallazgo visual resuelto: CARTO devolvía tiles “API KEY REQUIRED”. Se cambió
explícitamente solo el mapa base a OpenStreetMap estándar con atribución; las
fuentes GIS siguen intactas. Los íconos y el avance son presentación, no nuevos
datos ecológicos. No se descargaron tiles masivamente ni se implementó precarga
offline del proveedor; sin red se desactiva el mapa base y se usan capas locales.

Limitaciones: el PDF disponible no tenía sufijo `(1)`; huella documentada. No se
realizó una búsqueda NSGA-II nueva completa, prueba de carga multiusuario ni
validación ecológica de RU. La defensa humana, nota de rúbrica y contribuciones
individuales no pueden acreditarse mediante estas comprobaciones.
