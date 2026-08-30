Cada corrida debe guardar:

results/runs/run_0001.csv
results/runs/run_0001_config.yaml
results/runs/run_0001_summary.json
Nunca guardar únicamente una gráfica.

La gráfica siempre debe poder reconstruirse desde los datos.

11. Semillas
Crear el RNG una sola vez desde la configuración.

rng = np.random.default_rng(seed)
Pasarlo a los módulos que lo necesiten.

No crear semillas aleatorias escondidas dentro de funciones.