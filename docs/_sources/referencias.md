# Referencias y fuentes

Las referencias centrales se verificaron en texto completo; sus revisiones y SHA-256 están en `literature/fulltext_manifest.json`. Los valores transcritos tienen localizador en `literature/verified_extracts.csv`. La consulta dirigida apoya este EDA y no sustituye una revisión sistemática completa.

- Liu, H., Xu, S., Zhao, Z., Kong, L., Kamarthi, H., Sasanur, A. B., Sharma, M., Cui, J., Wen, Q., Zhang, C. y Prakash, B. A. (2024). *Time-MMD: Multi-Domain Multimodal Dataset for Time Series Analysis*. NeurIPS, Datasets and Benchmarks. [arXiv:2406.08627v2](https://arxiv.org/abs/2406.08627v2).
- Tan, M., Merrill, M. A., Gupta, V., Althoff, T. y Hartvigsen, T. (2024). *Are Language Models Actually Useful for Time Series Forecasting?* NeurIPS. [arXiv:2406.16964v2](https://arxiv.org/abs/2406.16964v2).
- Bi, Z., Huang, L., Jin, H., Zeng, Q. y Chen, H. (2025). *NSW-EPNews: A News-Augmented Benchmark for Electricity Price Forecasting with LLMs*. Preprint. [arXiv:2506.11050v1](https://arxiv.org/abs/2506.11050v1).
- Lago, J., Marcjasz, G., De Schutter, B. y Weron, R. (2021). *Forecasting day-ahead electricity prices: A review of state-of-the-art algorithms, best practices and an open-access benchmark*. Applied Energy, 293, 116983. [DOI:10.1016/j.apenergy.2021.116983](https://doi.org/10.1016/j.apenergy.2021.116983).
- Nguyen, H. H., Nguyen, M. H., Nguyen, D. y Le, H. (2026). *Does Text Actually Help? Uncovering and Resolving Text Collapse in Multimodal Time Series Forecasting*. Preprint. [arXiv:2606.19413](https://arxiv.org/abs/2606.19413).
- Su, C., Tian, Y., Song, Y. y Zhang, Y. (2025). *Text Reinforcement for Multimodal Time Series Forecasting*. Preprint. [arXiv:2509.00687](https://arxiv.org/abs/2509.00687).
- Liu, H., Zhou, Y., Sen, R., Prakash, B. A. y Das, A. (2026). *Rethinking Multimodal Time-Series Forecasting Evaluation*. ICML, versión consultada en [arXiv:2607.06973](https://arxiv.org/abs/2607.06973).
- Hyndman, R. J. y Athanasopoulos, G. *Forecasting: Principles and Practice*, tercera edición, versión en línea. [Descomposición](https://otexts.com/fpp3/decomposition.html), [evaluación y herramientas](https://otexts.com/fpp3/toolbox.html). Consulta: 3 de noviembre de 2026.

## Documentación de métodos y datos

- Scikit-learn. [Extracción de tópicos con NMF y LDA](https://scikit-learn.org/stable/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html) y [NMF](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.NMF.html). Se utiliza NMF con TF-IDF, ajustado sólo con entrenamiento; no se utiliza LDA en este EDA.
- NLTK Data / Snowball. Lista lingüística de [palabras funcionales](https://github.com/nltk/nltk_data/tree/gh-pages/packages/corpora), recurso `stopwords/spanish`. La copia exacta, la fuente y sus huellas se guardan en `resources/`.

- Statsmodels. Documentación de [ADF](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html), [KPSS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html), [BDS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.bds.html) y [MSTL](https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.MSTL.html). La versión instalada está fijada en `requirements.lock.txt`.
- XM. [API de datos de XM](https://github.com/EquipoAnaliticaXM/API_XM), [Sinergox](https://sinergox.xm.com.co/) e [informes de operación y mercado](https://www.xm.com.co/nuestra-empresa/informes/informes-de-la-operacion-y-el-mercado).
- IDEAM. [Catálogo de boletines](https://www.ideam.gov.co/sala-de-prensa/boletines).
- Open-Meteo. [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) y [especificación publicada](https://github.com/open-meteo/open-meteo/blob/main/openapi/historical-weather.yml).
- ECMWF/Copernicus Climate Change Service. [ERA5](https://www.ecmwf.int/en/forecasts/dataset/ecmwf-reanalysis-v5).
- Internet Archive. Capturas RSS/sitemaps con fecha real de captura, URI de reproducción y huella indexada conservadas en `data/provenance/`.
- Corpus abiertos: [Babel Briefings](https://huggingface.co/datasets/felixludos/babel-briefings), [colmbian_spanish_news](https://huggingface.co/datasets/hacktoberfest-corpus-es/colmbian_spanish_news) y [Villaitech/colombia-news](https://huggingface.co/datasets/Villaitech/colombia-news). Sólo se seleccionan títulos de los medios acordados; no se incorporan categorías, entailment o cuerpos. Revisiones y hashes en `data/metadata/source_provenance.json`.

## Material aportado por el autor

- *Entregable1DeepLearningProject.pdf*: pautas del curso, especialmente secciones 2.1 y 2.2.B y requisito de implicaciones técnicas. Se revisaron las 34 páginas mediante extracción local. No se redistribuye el documento.
- Exportaciones *SCOPUS_TM_NLP.txt* y *WOS_TM_NLP.txt*. Son resúmenes aportados, con inventario y preselección previos; no equivalen a la verificación de todos sus textos completos.
- *Papers_Time-MMD_y_datasets.xlsx*: lista aportada de trabajos y datasets, contrastada con los textos completos para las afirmaciones utilizadas. Los registros restantes se conservan como apuntes de lectura no verificados.
- Planes internos del programa sobre volatilidad multimodal, riesgo/VaR, energía con recuperación adaptativa y transferencia entre dominios. El plan energético, sección 7.2, respalda el énfasis en cobertura, diccionario, procedencia y sesgos. Son guías internas, no evidencia de resultados publicados ni instrucciones para ejecutar sus proyectos en este repositorio.

El inventario de archivos aportados conserva sus huellas y señala que los documentos privados no se redistribuyen. La selección definitiva de tres baselines y la revisión sistemática exigida para el E1 completo permanecen pendientes.


- Lopes, D. R. (2021). *timeseries-cv*, versión 0.1.5 [software]. Función `split_train_val_forwardChaining`. [PyPI](https://pypi.org/project/timeseries-cv/) · [Repositorio](https://github.com/DidierRLopes/timeseries-cv).
