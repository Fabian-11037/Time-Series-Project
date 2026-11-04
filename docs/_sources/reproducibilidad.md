# Reproducibilidad y límites

El dataset está versionado en `data/` como CSV comprimidos por año y fuente. Cada archivo tiene conteo y SHA-256 en `data/manifest.json`. No se necesita volver a consultar APIs para reproducir el EDA. La hidrología conserva frecuencia diaria; las noticias son registros de texto y procedencia separados, sin multiplicar filas horarias.

```bash
python -m venv .venv
# Activar .venv según el sistema operativo
python -m pip install -r requirements.lock.txt
python scripts/verify_dataset.py
python -m unittest discover -s tests
python scripts/create_notebooks.py
python scripts/create_literature_notebooks.py
python scripts/run_eda.py
```

`run_eda.py` ejecuta los cuadernos con el intérprete del entorno actual, comprueba errores y construye Jupyter Book 1.0.4. La construcción del libro usa las salidas ya ejecutadas; no vuelve a calcularlas al renderizar. El HTML queda en `docs/index.html`. El tiempo de ejecución depende del equipo, especialmente de STL/MSTL y los diagnósticos temporales.

Las fuentes editables son los generadores en `scripts/` y los análisis en `src/colombia_energy/eda.py`. Las figuras PNG y tablas CSV se generan en `results/`. La bibliografía distingue extracciones verificadas de los inventarios previos de resúmenes.

El manifiesto de prueba se guarda antes del EDA en `data/test_freeze.json`. La lectura de prueba está bloqueada por defecto. El libro analiza entrenamiento y, de forma separada, desplazamientos de validación. El calendario y la cobertura completa se auditan como metadatos; no se usan para optimizar con el objetivo de prueba.

Para E1, `model_policy.py` admite sólo variables numéricas declaradas y calendario conocido: rechaza texto, embeddings, sentimiento y conteos de noticias. Para las fases posteriores, `asof_text.py` distingue los selectores `verified` y `declared_dates`; este último incluye versiones no acreditadas por decisión del autor y compara con disponibilidad supuesta. No inventa fechas de informes sin publicación conocida.

Los archivos brutos extensos de corpus/noticias y los PDF privados no se publican. Los scripts originales de adquisición se conservan en `scripts/acquisition/` como procedencia; sus rutas de salida corresponden al flujo original. `scripts/import_local_downloads.py` documenta la conversión de esa instantánea a las particiones versionadas. Las APIs y archivos web pueden cambiar: una descarga nueva no garantiza reproducir una edición histórica. Las huellas del repositorio identifican la instantánea efectivamente analizada.

La disponibilidad histórica de todas las versiones numéricas no está acreditada. El texto ampliado también puede contener revisiones posteriores. Por tanto, reproducibilidad de la instantánea no equivale a un backtest operativo sin fuga. No se presentan resultados predictivos ni se declara cumplido el Entregable 1 completo.

