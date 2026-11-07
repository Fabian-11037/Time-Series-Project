# Matriz consolidada de literatura relevante

23 estudios destacados: seis de precio eléctrico, siete de texto operativo/financiero y diez de métodos generales. Once resultados se contrastaron en texto completo y doce proceden de abstracts. Se mantienen como fuentes de verdad las extracciones y los inventarios originales, sin cambiar frecuencias de baselines.

`relevant_studies.csv` identifica cada estudio, modelo/aporte, caso, resultados, implicación y procedencia. Origen indica países de afiliaciones institucionales verificadas, no nacionalidad ni sede de congreso; puede ser parcial en equipos multicéntricos. El caso de estudio distingue el territorio de los datos. País no verificado y cifras ausentes en abstract no se completan por inferencia. Los metadatos geográficos nuevos no convierten un abstract en revisión de resultados de texto completo.

Las fuentes de países incluyen cabeceras de artículos, programas de congresos y registros institucionales. Países no verificables con fuente primaria (CSConv y Time Fusion Transformers) permanecen sin asignar. Las referencias de congreso RSAM y Forwardformer usan año del volumen de revista 2021 y 2024, respectivamente; los DOI contienen años anteriores. No se combinan métricas, monedas, horizontes ni escalas para producir un ranking global de precisión.

El capítulo 9 se genera con `scripts/consolidated_literature_cells.py`, a partir de esta matriz y las extracciones previas. Tablas y gráficos del capítulo presentan la síntesis; la extracción extensa permanece en `literature/baseline_review/` y `literature/ieee_abstracts_2026-11-06/`.
