# Reproducibilidad

El conjunto de datos se distribuye en `data/` mediante archivos CSV comprimidos por año y fuente. El manifiesto `data/manifest.json` registra conteos y huellas SHA-256. Las series horarias, la hidrología diaria y los documentos conservan sus frecuencias y unidades de observación.

```bash
python -m venv .venv
# Activar .venv según el sistema operativo
python -m pip install -r requirements.lock.txt
python scripts/verify_dataset.py
python -m unittest discover -s tests
python scripts/create_notebooks.py
python scripts/create_literature_notebooks.py
python scripts/run_eda.py
python scripts/verify_book.py
```

`run_eda.py` ejecuta los cuadernos, verifica sus salidas y construye el libro con Jupyter Book 1.0.4. El HTML se almacena en `docs/`. Cada cuaderno contiene las importaciones, las funciones de lectura, los controles temporales y el código que produce sus tablas y figuras. Los generadores de `scripts/` incorporan estas implementaciones como celdas ejecutables, con huellas de las fuentes utilizadas. El código analítico permanece visible. Las tablas y figuras se guardan en `results/`.

## Partición y disponibilidad temporal

El manifiesto `data/test_freeze.json` identifica los archivos de prueba. Los procedimientos analíticos utilizan entrenamiento y diagnósticos separados de validación; las verificaciones del periodo completo comprueban calendario, integridad y procedencia.

El capítulo de validación incluye las funciones que implementan los escenarios `verified` y `declared_dates`. El primero utiliza capturas de versiones documentales verificadas; el segundo utiliza fechas de publicación declaradas y la regla de disponibilidad supuesta. Los informes sin fecha de publicación permanecen en el inventario sin asignación temporal.

Las series numéricas y parte del corpus documental proceden de fuentes retrospectivas. La incertidumbre sobre las versiones y sus fechas efectivas de publicación limita la reconstrucción de un escenario operativo histórico y debe considerarse en el análisis de sensibilidad.

## Procedencia

Los scripts de adquisición se conservan en `scripts/acquisition/`. La conversión de la instantánea analizada se documenta en `scripts/import_local_downloads.py`. Las huellas permiten identificar los archivos utilizados y contrastar futuras actualizaciones de las fuentes. El directorio `literature/` contiene los registros de las extracciones bibliográficas verificadas.
