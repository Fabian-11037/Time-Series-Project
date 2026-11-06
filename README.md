# Time-Series-Project

Dataset, análisis exploratorio y modelos numéricos de pronóstico del precio eléctrico colombiano. Autores: **Fabian José Manrique Morelos y Gloria Bastida**, Maestría en Estadística Aplicada, Universidad del Norte.

## Datos disponibles

Periodo numérico: 2000–2025, hora de Colombia.

| Bloque | Filas | Contenido |
|---|---:|---|
| Horario | 227.928 | Precio nacional de bolsa y dos demandas de XM; temperatura, humedad y precipitación de ocho ciudades. 27 variables numéricas. |
| Hidrología diaria | 9.497 | Llenado, reserva útil, capacidad útil y aportes del SIN. |
| Titulares de prensa | 561.072 | Siete medios seleccionados; 115.480 con fecha declarada en 2020–2025. |
| Informes oficiales | 7.629 | 7.223 entradas del IDEAM y 406 títulos/nombres de archivos de XM. |

Los datos están **incluidos en este repositorio**, comprimidos por año/fuente para facilitar su descarga: [numéricos](data/numeric/), [texto](data/text/), [diccionario](data/metadata/data_dictionary.csv), [manifiesto de huellas](data/manifest.json). No requieren consultar las APIs para reproducir este EDA.

Medios: El Tiempo, El Espectador, Semana, Portafolio, La República, El Colombiano y Dinero.

El capítulo de texto incorpora **frecuencias, bigramas, diversidad léxica, tópicos NMF, evolución temporal y cambio del vocabulario**. El vocabulario y los tópicos se ajustan sólo con prensa de entrenamiento y se congelan para proyectar validación. [Protocolo](PROTOCOLO_EDA_TITULARES.md).

El histórico editorial es **parcial**. La [cobertura mensual](data/metadata/coverage_2000_2025_by_month_source.csv) distingue publicación declarada, captura comprobada y periodo de referencia. Un cero no demuestra que el medio no publicara noticias.

## Jupyter Book

El libro contiene once cuadernos ejecutados, referencias y reproducción. Incluye calidad, distribución y anomalías, cambios de régimen, STL/MSTL, ADF/KPSS conjuntos, ACF/PACF, espectro, ARCH/BDS, covariables, cobertura textual y controles temporales. Cada análisis termina en decisiones de preprocesamiento, arquitectura, validación y riesgos.

- [Cuadernos y fuentes del libro](book/), con código analítico completo en celdas ejecutables y visibles.
- [HTML construido](docs/): abrir `docs/index.html` tras descargar/clonar el repositorio.
- [Tablas y figuras generadas](results/).
- [Protocolo del EDA](PROTOCOLO_EDA.md).
- [Síntesis bibliográfica y extracciones verificadas](literature/).

Esta versión presenta la construcción del dataset, el análisis exploratorio, la síntesis bibliográfica y la búsqueda de modelos numéricos de pronóstico.

## Disponibilidad y fuga temporal

El escenario de fechas declaradas incluye versiones documentales recuperadas retrospectivamente. Hay 568.294 registros fechados utilizables bajo reglas de disponibilidad declaradas; el escenario estricto conserva 62.572 versiones con captura comprobada. Los 406 títulos de XM sin publicación fechada se preservan sin asignar una fecha inventada. Un registro contradictorio permanece en cuarentena.

El escenario ampliado usa la hora declarada con zona, o las 00:00 del día siguiente cuando sólo existe el día. Estos supuestos no certifican la versión histórica y pueden introducir fuga por revisiones. El escenario estricto usa la captura de la versión exacta y nunca la retrofecha al mes del informe.

Las series actuales de XM y ERA5 son retrospectivas: no se han acreditado todos los horarios de publicación ni las ediciones numéricas originales. Las covariables se alinean de acuerdo con su disponibilidad al origen de pronóstico.

El pipeline de entrenamiento utiliza **cinco folds forward chaining sobre 2000–2021**, con entrenamiento expansivo y bloques de validación posteriores a partir de 2018. El periodo **2022–2025 permanece reservado para prueba**, con [huellas congeladas](data/test_freeze.json). Los contrastes entre 2000–2017 y 2018–2021 del EDA conservan su función diagnóstica. La configuración se registra en [configs/training_pipeline.json](configs/training_pipeline.json).

## Continuidad y entrenamiento

[Contexto del proyecto y pasos para continuar](CONTEXTO_PROYECTO.md). El pipeline se prepara con `python scripts/prepare_pipeline.py`; la integración de modelos se documenta en [PIPELINE.md](PIPELINE.md).

## Reproducir

Requiere Python 3.12. Crear/activar un entorno virtual y ejecutar:

```bash
python -m pip install -r requirements.lock.txt
python scripts/verify_dataset.py
python -m unittest discover -s tests
python scripts/create_notebooks.py
python scripts/create_literature_notebooks.py
python scripts/run_eda.py
```

El análisis usa únicamente los archivos versionados. Para construir el HTML sin recalcular cuadernos ya ejecutados: `python scripts/run_eda.py --build-only`.

Los scripts de adquisición se conservan en `scripts/acquisition/`. La conversión de la instantánea analizada se documenta en `scripts/import_local_downloads.py`.

## Fuentes y bibliografía

Se verificaron en texto completo Time-MMD, Tan et al., NSW-EPNews, Lago et al., REST-TS, TeR-TSF y TimesX. El inventario previo de Scopus/WoS y la lista aportada se distinguen de esos resultados verificados. La conciliación entre el inventario anterior y la exportación actual de Scopus se documenta como una limitación de trazabilidad.

[Referencias del libro](book/referencias.md) · [Fuentes, atribuciones y condiciones](DATA_SOURCES.md).

## Modelos numéricos

Se completaron 4800 ajustes de 192 configuraciones MLP, LSTM y CNN1D con cinco folds temporales y cinco semillas. El capítulo incluye predictores, diagramas, fundamentos matemáticos, código del pipeline y comparación con repetición semanal. [Libro público](https://fabian-11037.github.io/Time-Series-Project/10_modelos.html).

| Mejor configuración por familia | Contexto | Ridge | MAE de validación (COP/kWh) |
|---|---:|---:|---:|
| CNN1D: dos capas, 64 filtros, kernel 5 | 24 h | 1e-4 | 24.155 |
| LSTM: una capa, 64 unidades | 72 h | 1e-3 | 24.624 |
| MLP: densas 256 y 128 | 24 h | 1e-3 | 24.992 |

Dropout fijo 0.1, salida Softplus positiva y parada anticipada por MAE. Referencia semanal: MAE 40.157 COP/kWh. Las métricas se utilizan para seleccionar arquitectura y época; no son una evaluación externa imparcial. Prueba 2022–2025 fue consultada previamente para configuraciones iniciales y no se reevalúa en esta búsqueda.

Se versionan las métricas de los 4800 ajustes y las predicciones/curvas de las tres configuraciones seleccionadas (75 ejecuciones). Las predicciones se distribuyen en `results/variant_search/selected_predictions.zip`, con huellas individuales en `selected_predictions_manifest.json`. Los checkpoints y el resto de artefactos de entrenamiento permanecen en el archivo local; no se incluyen los 5.4 GB completos en Git. Los scripts permiten regenerarlos. El libro se reconstruye con las predicciones seleccionadas, sin necesidad de pesos ni GPU.

Para reconstrucción documental, instalar `requirements.lock.txt` y después `requirements-pytorch-cpu.txt`, generar los cuadernos con los tres generadores de `scripts/` y ejecutar `scripts/run_eda.py`. El generador nuevo es `scripts/create_model_notebook.py`. Para entrenamiento AMD, usar el entorno PyTorch/ROCm registrado en los artefactos, no el paquete CPU documental.


Ejecución en Windows/Linux y entrenamiento CPU/GPU: [EJECUCION.md](EJECUCION.md). La evidencia dirigida para la extracción de arquitecturas se encuentra en `literature/baseline_evidence_2026-11-06.csv` y en el capítulo de literatura.
