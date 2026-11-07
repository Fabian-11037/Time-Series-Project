# Reproducibilidad

El conjunto de datos se distribuye en `data/` mediante archivos CSV comprimidos por año y fuente. El manifiesto `data/manifest.json` registra conteos y huellas SHA-256. Las series horarias, la hidrología diaria y los documentos conservan sus frecuencias y unidades de observación.

```bash
python -m venv .venv
# Activar .venv según el sistema operativo
python -m pip install -r requirements.lock.txt
python -m pip install -r requirements-pytorch-cpu.txt
python scripts/verify_dataset.py
python -m unittest discover -s tests
python scripts/create_notebooks.py
python scripts/create_literature_notebooks.py
python scripts/create_model_notebook.py
python scripts/run_eda.py
python scripts/verify_book.py
```

`run_eda.py` ejecuta los cuadernos, verifica sus salidas y construye el libro con Jupyter Book 1.0.4. El HTML se almacena en `docs/`. Cada cuaderno contiene las importaciones, las funciones de lectura, los controles temporales y el código que produce sus tablas y figuras. Los generadores de `scripts/` incorporan estas implementaciones como celdas ejecutables, con huellas de las fuentes utilizadas. El código analítico permanece visible. Las tablas y figuras se guardan en `results/`.

## Partición y disponibilidad temporal

El diseño de entrenamiento aplica cinco folds forward chaining al periodo de desarrollo 2000–2021. La validación comienza en 2018 y sus bloques consecutivos cubren hasta el cierre de 2021. La configuración y preparación se reproducen con `python scripts/prepare_pipeline.py`. Cada fold ajusta su propio escalador y preserva el periodo de prueba 2022–2025.


El manifiesto `data/test_freeze.json` identifica los archivos de prueba. Los procedimientos analíticos utilizan entrenamiento y diagnósticos separados de validación; las verificaciones del periodo completo comprueban calendario, integridad y procedencia.

El capítulo de validación incluye las funciones que implementan los escenarios `verified` y `declared_dates`. El primero utiliza capturas de versiones documentales verificadas; el segundo utiliza fechas de publicación declaradas y la regla de disponibilidad supuesta. Los informes sin fecha de publicación permanecen en el inventario sin asignación temporal.

Las series numéricas y parte del corpus documental proceden de fuentes retrospectivas. La incertidumbre sobre las versiones y sus fechas efectivas de publicación limita la reconstrucción de un escenario operativo histórico y debe considerarse en el análisis de sensibilidad.

## Procedencia

Los scripts de adquisición se conservan en `scripts/acquisition/`. La conversión de la instantánea analizada se documenta en `scripts/import_local_downloads.py`. Las huellas permiten identificar los archivos utilizados y contrastar futuras actualizaciones de las fuentes. El directorio `literature/` contiene los registros de las extracciones bibliográficas verificadas.

## Modelos numéricos

El capítulo de modelos se genera con `scripts/create_model_notebook.py` y se ejecuta con `python scripts/run_eda.py --chapters 10_modelos --no-build`. Sus celdas incluyen el código de preparación temporal, arquitectura y entrenamiento, y verifican las métricas desde artefactos existentes sin repetir la búsqueda. El entrenamiento exige el entorno PyTorch registrado en `results/variant_search/environment.json`; Jupyter Book permanece en la versión 1.0.4. Las fuentes y el registro experimental se identifican mediante huellas en `configuration.json`.

La búsqueda compara 192 configuraciones mediante 4800 ajustes en desarrollo 2000–2021. Los orígenes se comparten entre contextos y cada fold ajusta sus escaladores sólo con entrenamiento. El periodo 2022–2025 se evaluó previamente para configuraciones iniciales y no se reevalúa en esta búsqueda. Las métricas de selección no equivalen a errores de prueba de los candidatos seleccionados.


## Sistemas operativos y dispositivos

El libro se ejecuta por CPU en Windows y Linux con las dependencias fijadas. La selección de dispositivo y el bloqueo de ejecuciones se incluyen como código en el capítulo de modelos. El entrenamiento utiliza `--device auto`, `--device cpu` o `--device gpu`; la GPU requiere una instalación CUDA/ROCm compatible. La configuración registra sistema, versiones y dispositivo. Las nuevas ejecuciones se separan de los resultados históricos y mantienen la separación entre desarrollo y evaluación final. Las instrucciones completas están en [la guía de ejecución](https://github.com/Fabian-11037/Time-Series-Project/blob/main/EJECUCION.md).
