generators/
Solo genera variables aleatorias.

Ejemplo correcto:

value = exponential_inverse(lam, rng)
Ejemplo incorrecto:

value = bee_departure_time(...)
El generador no debe saber qué significa la muestra.