# Revisión focalizada de modelos de referencia

6 de noviembre de 2026. Textos completos examinados: 20. Estudios empíricos: 19; principal puntual: 16. Cinco candidatos permanecen sin texto íntegro verificado. Revisión posterior a los experimentos exploratorios, por un único proceso de extracción; no es una búsqueda exhaustiva de la disciplina.

| Familia | Estudios puntuales | Frecuencia | Sin preprints | Corpus ampliado |
|---|---:|---:|---:|---:|
| LSTM | 7/16 | 43,75 % | 6/14 | 9/19 |
| MLP/DNN | 6/16 | 37,50 % | 6/14 | 8/19 |
| CNN independiente | 2/16 | 12,50 % | 2/14 | 4/19 |

CNN empata con CNN-LSTM y Transformer. La elección de CNN1D combina la evidencia de comparadores con una estructura simple y patrones locales, complementarios a memoria LSTM e interacciones densas. Sólo una fuente principal confirma explícitamente CNN1D; la otra no especifica la dimensión. No se suman propuestas, componentes o ablaciones a sus familias. Cada estudio cuenta como máximo una vez por familia, aunque evalúe MLP y DNN o varios tamaños.

- [Protocolo y decisiones](PROTOCOLO.md) y [búsqueda/recuperación](BUSQUEDA.md).
- [Estudios, fuentes, SHA y calidad](studies.csv).
- [Extracciones: 90 registros de modelos](extractions.csv).
- [Cribado individual de 83 títulos/resúmenes heredados](screening_inherited.csv).
- [Registro complementario: 25 candidatos y estado de recuperación](retrieval_registry.csv).
- [Frecuencias completas, denominadores y pertenencia por estudio](baseline_frequencies.csv).
- [Resumen de conteos](review_summary.json).

Recalcular con `python scripts/update_baseline_frequencies.py` desde la raíz del repositorio. El cálculo completo y sus controles también están visibles en `book/09_literatura.ipynb`. La matriz de presencia, configuraciones, resultados, auditoría de calidad y fórmulas de complejidad se generan en el JBook. Las copias de textos completos permanecen en caché local ignorada; los datos publicados permiten localizar y verificar cada afirmación sin redistribuir artículos.
