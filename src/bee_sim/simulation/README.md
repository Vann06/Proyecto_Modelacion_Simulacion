simulation/engine.py coordina el flujo, pero no contiene todas las fórmulas.

Flujo esperado:

leer configuración
crear RNG
crear colonia
crear ambiente

mientras exista tiempo:
    generar salida
    seleccionar abeja disponible
    generar distancia
    generar duración
    generar flores visitadas
    generar polinización
    generar néctar
    generar retorno
    actualizar abeja
    actualizar flores disponibles
    guardar viaje

calcular métricas
guardar resultados