# Ampliación del EDA al conjunto utilizado por los entrenamientos

6 de noviembre de 2026. Solicitud: incluir toda la información utilizada en entrenamiento. Esta actualización es posterior al piloto, a la evaluación inicial y a la búsqueda de variantes; describe los datos y no modifica sus protocolos históricos.

## Alcance

El EDA numérico utiliza desarrollo completo, 2000-01-01 inclusive a 2022-01-01 exclusivo, hora de Colombia: 192864 horas y 8036 días hidrológicos. Se actualizan calidad, rangos, distribución, anomalías, cambios de régimen, perfiles estacionales, espectro, estacionariedad, dependencia, meteorología y asociaciones hidrológicas. La comparación diagnóstica entre 2000–2017 y 2018–2021 se conserva como comparación entre periodos disjuntos, distinta de la validación expansiva vigente.

El capítulo 6 reconstruye las 37 entradas mediante el mismo constructor del pipeline: precio, dos demandas, 24 variables meteorológicas, cuatro hidrológicas y seis funciones cíclicas de calendario. Se describen horas únicas de entrada y etiquetas, diferenciándolas de la repetición en ventanas. Se reproducen los cinco folds y los contextos de 24/72/168/336 horas, con orígenes comunes determinados por la historia máxima en la búsqueda. Se contrastan conteos, columnas y fechas con `results/variant_search/fold_audit.json`. La cobertura diagnóstica de todo desarrollo comprende 8027 ventanas admisibles de 168 horas y 192792 filas únicas de entrada. Su descripción se calcula con desarrollo y no depende de artefactos de evaluación externa.

Los agregados de todo desarrollo son diagnósticos retrospectivos; no se reutilizan como escaladores operativos de folds anteriores. El entrenamiento sigue estimando su preprocesamiento con las filas de su propio pasado. No se modifica `data.SPLITS`, la función de forward chaining, la configuración, pesos o resultados experimentales. Prueba 2022–2025 permanece excluida de la exploración de valores y contenido.

## Cobertura textual y ajustes

Se describe conjuntamente todo texto con disponibilidad supuesta en 2000–2021, preservando cuarentena y regla del día siguiente. Se incluyen frecuencias y bigramas completos, composición anual por fuente y proyecciones de tópicos por fuente/fold. Los tópicos conservan vocabulario, IDF y componentes aprendidos en el periodo inicial 2000–2017, y los documentos posteriores se proyectan sobre esa referencia común. No se reajusta con validación ni se agregan atributos textuales al E1 numérico. La cobertura por fold representa historia documental disponible; no afirma que las redes hayan usado titulares.

La integridad, resúmenes y correlaciones usan todas las observaciones de desarrollo. La información mutua conserva una muestra determinista de 12000 horas y el ajuste TF-IDF/NMF una muestra con límites por año y total; estas aproximaciones se identifican en el libro. La STL diaria usa todo desarrollo; la MSTL horaria muestra 2021 como último año completo para acotar el costo. Los perfiles y el espectro incorporan todo 2000–2021.

## Reproducción

Regenerar los cuadernos con `create_notebooks.py`, `create_literature_notebooks.py` y `create_model_notebook.py`; ejecutar `python scripts/run_eda.py` y `python scripts/verify_book.py`. Todo el código analítico está en las celdas visibles. Evidencia numérica: `results/eda_training_scope.json`; textual: `results/headlines/development_audit.json`. Las tablas nuevas usan sufijo `_desarrollo` o prefijo `eda_`; los archivos `_train` previos conservan el diagnóstico histórico y no se confunden con los nuevos resúmenes publicados.
