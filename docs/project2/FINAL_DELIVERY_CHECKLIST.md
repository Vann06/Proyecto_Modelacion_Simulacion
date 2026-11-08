# Checklist verificable de cierre y presentación — Proyecto 2 UVG

**Rama de integración de referencia:** `integracion/project2-comparacion-app` (commit `dff96a3`). **Cierre científico propuesto:** `feature/project2-cierre-cientifico-08`.

Este checklist separa **evidencia ya publicada**, **verificación pendiente en el equipo** y **material todavía no producido**. No confundir presencia de archivos con aprobación del profesor.

## A. Cierre técnico: ejecutar antes de la entrega

- [ ] Revisar el diff de la rama de cierre e integrarla mediante PR si el equipo aprueba la interpretación científica.
- [ ] Instalar Python 3.10+ y Node 22.20+ en un entorno limpio, según `README_REACT.md`.
- [ ] Ejecutar `python -m unittest discover -s tests -v` con PYTHONPATH `src;.` en Windows (ver README_REACT). Conservar captura/log del resultado. El último registro documental indica 173 pruebas aprobadas, **no certifica una nueva ejecución** en el equipo final.
- [ ] Dentro de frontend: `npm ci`, `npm test`, `npm run build`. Conservar logs; el registro documental previo indica 8 tests frontend y build exitoso.
- [ ] Iniciar FastAPI sirviendo frontend compilado; probar health, overview, mapa, comparación, validación, sensibilidad, demos RANDOM/GREEDY/NSGA-II y descarga CSV.
- [ ] Abrir `notebooks/project2/08_final_results.ipynb` y hacer **Run All**. Revisar `results/project2/final_synthesis/` con tablas y gráficos derivados; confirmar que no modifica la evidencia histórica. Ejecutar también notebook 09 si el equipo lo incluye en anexos.
- [ ] Comprobar visualmente que la animación de viajes, consumo y stock responde al día/minuto y no atribuye abejas GPS ni polinización observada.
- [ ] Revisar superposición real de leyendas, textos y gráficas a 1366×768 y a pantalla de exposición. No utilizar gráficos temporales para comparar condiciones OAT independientes.

## B. Cierre científico — afirmaciones permitidas

- [x] Existe problema real, mapas de Oslo y Dryad verificable.
- [x] Están implementados RANDOM, GREEDY y NSGA-II bajo contrato común, con métricas uniformes.
- [x] Comparación histórica con 70 seeds compartidas (31–100), K=5, motor 1.1.0.
- [x] Evidencia de sensibilidad OAT con 14 condiciones, 1 200 simulaciones, motor 1.1.1 y 30 seeds por método/condición disponible.
- [x] Referentes empíricos independientes con MAE, RMSE, split por trap y bootstrap.
- [x] Se distinguen recursos `synthetic_RU` de flores/m², conteos/min, néctar y polinización efectiva.
- [ ] **No se ha demostrado** validación ecológica directa de simulate() contra Dryad. No marcar como completa sin operador de observación verificable.
- [ ] No afirmar que el frente NSGA-II es óptimo global ni que las ubicaciones son recomendaciones autorizadas de colmenas reales.
- [ ] Mostrar las limitaciones de 375 IDs frente a 351 coordenadas, y los 49 IDs del frente frente a 32 instalaciones físicas.
- [ ] Explicar que el holdout histórico ya fue inspeccionado: análisis descriptivo, no estudio confirmatorio prerregistrado.
- [ ] Explicar que las ubicaciones NSGA-II quedan fijas en sensibilidad, no se reoptimizan para cada escenario.
- [ ] Explicar que cambiar K con oportunidades por colmena fija cambia la demanda total de viajes.

## C. Gráficas y tablas que deben figurar en el informe

1. **Comportamiento del sistema:** mapa/diagrama de flujo diario con colmena, viaje, parche, consumo y regeneración; o figura de recursos por día identificada como sintética.
2. **Comparación principal:** recurso entregado y distancia media por RANDOM/GREEDY/NSGA-II, mismas unidades y cohortes históricas, con IC.
3. **Compromiso multiobjetivo:** frente de Pareto recurso vs distancia, sin contar 49 IDs como 49 configuraciones físicas distintas.
4. **Sensibilidad:** barras por condición o paneles por factor, no una línea temporal falsa.
5. **Referencia real:** MAE/RMSE de referentes Dryad, claramente separados del motor sintético.
6. **Tabla real/base/mejorado:** declarar 'no comparable' o 'no disponible' en las casillas sin equivalencia; no fabricar métricas para cubrir la rúbrica.

El notebook 08 actualizado genera figuras y tablas derivadas en `results/project2/final_synthesis/` al ejecutar Run All.

## D. Informe técnico PDF — aún pendiente como archivo final

- [ ] Portada con UVG **CC3074**, integrantes, grupo, curso y fecha real.
- [ ] Resumen y pregunta de investigación con métrica principal, unidad y dirección.
- [ ] Datos y fuentes: Dryad DOI, fechas de campaña, sitios, GIS Oslo, licencias y límites.
- [ ] Modelo: actores, diagrama, restricciones, ecuaciones, distribución de salidas/eventos y parámetros **sintéticos**.
- [ ] Técnica investigada: fundamentos NSGA-II, cruce, mutación, selección, crowding, parada y fuentes técnicas.
- [ ] Diseño experimental: K, 18 días, tres métodos, seeds comunes, bootstrap, intervalos, identidades/hashes.
- [ ] Resultados: tabla de métricas, diferencias absolutas y porcentuales, Pareto, sensibilidad, incertidumbre.
- [ ] Referencia real: metodología de observaciones Dryad, benchmark empírico, errores, **ausencia de operador del motor**.
- [ ] Discusión y límites: competencia casi cero, escenarios donde GREEDY supera sitios NSGA-II congelados, alcance geográfico/temporal.
- [ ] Conclusiones y recomendaciones acotadas; bibliografía, herramientas, uso de IA.
- [ ] Registro **real** de aportes por integrante (archivos, commits, experimentos) revisado por el equipo.
- [ ] Anexos: enlace a repo, commit de entrega, comandos, pruebas, resultados y capturas.

**Atención:** borradores antiguos que proponen año completo, técnica futura o Streamlit como entrega principal deben reescribirse para coincidir con 18 días, modelos actuales y React/FastAPI. Evitar discrepancias del código del curso.

## E. Diapositivas y demo (máximo 15 minutos)

**No hay todavía diapositivas finales verificadas en esta rama**. Propuesta de 9 pantallas o diapositivas breves:

1. Problema de ubicación de colmenas en Oslo, por qué importa.
2. Fuentes reales: Dryad, GIS, 737 parques y período observado.
3. Entidades del modelo y restricciones; no confundir recursos y sitios candidatos.
4. Flujo diario de eventos y qué se representa como sintético.
5. RANDOM, GREEDY, NSGA-II: representaciones, objetivos y operadores.
6. Resultado histórico con 70 seeds, RU sintéticas y metros, diferencias e IC.
7. Pareto y sensibilidad: mostrar un caso donde GREEDY supera sitios congelados.
8. Validación empírica con MAE y límites: observaciones reales ≠ motor sintético.
9. Conclusiones, limitaciones y siguiente estudio.

**Tiempo orientativo:** contexto 2 min, modelo 2, técnica 3, demo funcional 3, resultados/validación 3, cierre/preguntas 2. Ajustar a cantidad real de integrantes, **todos deben participar** y dominar los conceptos.

**Demo sin sobresaltos:** abrir la aplicación React local ya compilada, usar JSON de demos archivadas, mostrar mapa, un viaje de abejas, Pareto, sensibilidad, validación. Llevar respaldo de gráficas/CSV y capturas; **nunca** iniciar búsqueda NSGA-II de horas durante la presentación.

## F. Preguntas de defensa que todos deben responder

- ¿Por qué 737 parques no significan 737 lugares de colmena?
- ¿Qué diferencia hay entre 375 IDs y 351 coordenadas?
- ¿Qué significa synthetic_RU y por qué no es néctar?
- ¿Qué observó realmente Dryad y en qué período?
- ¿Cómo funciona el evento de salida y selección de parche?
- ¿Por qué RANDOM y GREEDY son comparaciones necesarias?
- ¿Cómo implementaron no dominancia y diversidad en NSGA-II?
- ¿Por qué las 70 seeds no se convierten en 2 100 réplicas independientes?
- ¿Por qué NSGA-II deja de ser la mejor ubicación fija al cambiar el radio?
- ¿Qué demuestran y qué no demuestran los errores MAE con datos reales?
- ¿Qué necesitaríamos medir para validar efectivamente el motor?
- ¿Por qué no puede afirmarse que se mejoró la polinización real de Oslo?

## Estado final a comunicar

**Sí:** software, simulación agregada, optimización, comparaciones reproducibles y sensibilidad documentadas.

**Parcial:** relación cuantitativa del simulador con observaciones reales.

**Pendiente de producción y comprobación humana:** PDF, diapositivas, aportes individuales, ensayo de 15 minutos y prueba en equipo final.

Fuente de cierre: `docs/project2/FINAL_SCIENTIFIC_SYNTHESIS.md` y `notebooks/project2/08_final_results.ipynb`.