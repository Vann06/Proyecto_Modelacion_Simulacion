# Pruebas

La suite cubre generadores, motor, métricas, persistencia, experimentos,
comparación de métodos y lectura de campañas.

Desde la raíz del repositorio:

```powershell
$env:PYTHONPATH = "src"
python -m pytest
```

También es compatible con `unittest`:

```bash
python -c "import sys, unittest; sys.path.insert(0, 'src'); result=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('tests')); raise SystemExit(not result.wasSuccessful())"
```
