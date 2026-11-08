# Guion de exposición — máximo 15 minutos

Ensayar con reloj. Los roles 1–5 son lugares para nombres reales, no atribuciones
inventadas. Si hay menos integrantes, distribuir bloques manteniendo participación
de todos. Cada integrante debe poder explicar el motor, unidades y limitaciones.

| Tiempo | Responsable a confirmar | Pantalla / acción | Mensaje verificable |
| --- | --- | --- | --- |
| 0:00–2:00 | Integrante 1 | Inicio, contexto y fuentes | 737 parques; 375 IDs y 351 coordenadas; problema de ubicación y recurso compartido |
| 2:00–4:00 | Integrante 2 | Oslo, seleccionar parque, restricciones | Un parque restringido puede aportar recurso; distancia métrica y recurso sintético por área |
| 4:00–7:00 | Integrante 3 | Optimización, mover solución Pareto | Mismo motor y seeds; explicar RANDOM, GREEDY, NSGA-II, no dominancia y crowding; no óptimo universal |
| 7:00–10:00 | Integrante 4 | Abejas, play/pausa, minuto 10, día; sensibilidad | Mostrar un viaje y stock, luego 30 réplicas por condición; una corrida con sliders es exploración |
| 10:00–13:00 | Integrante 5 | Validación y resultados, descargar CSV | Errores por sitios reservados, estratificación floral empeora; RU no es flores/néctar; cambios de recurso son simulados |
| 13:00–15:00 | Todos | Conclusión breve y preguntas | Qué mejoró, cuánto, condiciones, incertidumbre y pendientes; dejar tiempo real de defensa |

Antes de exponer: instalar, compilar, probar endpoints, precargar la app, descargar
CSV/figuras, confirmar fuentes/mapa base o desactivarlo, tener notebook 09 ejecutado
como respaldo. No iniciar NSGA-II de 50 generaciones en la demostración. El modo
demostración usa tres JSON guardados de motor 1.1.1; la comparación usa CSV 1.1.0.

Preguntas para ensayar: ¿por qué no convertir RU a néctar?, ¿qué hace comparables
los métodos?, ¿por qué 70 seeds y no 2 100 independientes?, ¿por qué K cambia
oportunidades totales?, ¿qué significa presión casi cero?, ¿cómo reservarían datos
nuevos?, ¿por qué convergencia de una métrica no demuestra convergencia del frente?

Completar antes de entregar: nombres, aportes verificables (archivos/experimentos),
responsable de cada bloque y resultado del ensayo. No atribuir automáticamente el
código generado con ayuda de IA como contribución individual sin revisión.
