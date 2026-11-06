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

El inventario de archivos aportados conserva sus huellas y señala que los documentos privados no se redistribuyen. La selección de las tres familias se fundamenta en la revisión focalizada de textos completos del capítulo 9; la búsqueda sistemática exhaustiva y su conciliación permanecen pendientes.


- Lopes, D. R. (2021). *timeseries-cv*, versión 0.1.5 [software]. Función `split_train_val_forwardChaining`. [PyPI](https://pypi.org/project/timeseries-cv/) · [Repositorio](https://github.com/DidierRLopes/timeseries-cv).

## Fundamentos de las arquitecturas numéricas

- Goodfellow, I., Bengio, Y. y Courville, A. (2016). *Deep Learning*. MIT Press. [Redes de propagación hacia delante](https://www.deeplearningbook.org/contents/mlp.html) y [redes convolucionales](https://www.deeplearningbook.org/contents/convnets.html).
- Hochreiter, S. y Schmidhuber, J. (1997). Long Short-Term Memory. *Neural Computation*, 9(8), 1735–1780. [Texto completo](https://www.bioinf.jku.at/publications/older/2604.pdf).
- PyTorch. Documentación de [LSTM](https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html), [Conv1d](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv1d.html) y [Softplus](https://docs.pytorch.org/docs/stable/generated/torch.nn.Softplus.html). Las ecuaciones y convenciones implementadas se contrastan con esta documentación; las versiones efectivamente ejecutadas se registran en los artefactos experimentales.


- Lago, J., De Ridder, F. y De Schutter, B. (2018). Forecasting spot electricity prices: Deep learning approaches and empirical comparison of traditional algorithms. *Applied Energy*, 221, 386–405. [DOI](https://doi.org/10.1016/j.apenergy.2018.02.069) · [Texto completo](https://jesuslago.com/wp-content/uploads/Lago2018b.pdf).


## Estudios de precio eléctrico: extracción de baselines

El corpus y sus decisiones se documentan en el capítulo 9 y `literature/baseline_review/`. Se distinguen pronóstico puntual, probabilístico, mercado relacionado y revisión secundaria. Los identificadores arXiv corresponden a preprints.

- Ugurlu et al. (2018). *Electricity Price Forecasting Using Recurrent Neural Networks*. [10.3390/en11051255](https://mdpi-res.com/d_attachment/energies/energies-11-01255/article_deploy/energies-11-01255.pdf).
- Kuo y Huang (2018). *An Electricity Price Forecasting Model by Hybrid Structured Deep Neural Networks*. [10.3390/su10041280](https://mdpi-res.com/d_attachment/sustainability/sustainability-10-01280/article_deploy/sustainability-10-01280.pdf).
- Ghimire et al. (2024; online 2023). *Two-step deep learning framework with error compensation technique for short-term, half-hourly electricity price forecasting*. [10.1016/j.apenergy.2023.122059](https://burjcdigital.urjc.es/server/api/core/bitstreams/584ad847-68b7-4ef1-b8fb-08db68f8eeee/content).
- Ghimire et al. (2025). *Half-hourly electricity price prediction model with explainable-decomposition hybrid deep learning approach*. [10.1016/j.egyai.2025.100492](https://opus.lib.uts.edu.au/bitstream/10453/190017/2/1-s2.0-S2666546825000242-main.pdf).
- Zhang et al. (2023). *Electricity price forecast based on the STL-TCN-NBEATS model*. [10.1016/j.heliyon.2023.e13029](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9938466/fullTextXML).
- Wang et al. (2026). *Short-Term Electricity Price Forecasting via a Reinforcement Learning-Based Dynamic Soft Ensemble Strategy*. [10.3390/en19030761](https://mdpi-res.com/d_attachment/energies/energies-19-00761/article_deploy/energies-19-00761.pdf).
- Elashhab et al. (2026), preprint v1. *Deep Learning for Cross-Border Electricity Price Forecasting: A Comparative Study*. [arXiv:2608.17091v1](https://arxiv.org/pdf/2608.17091v1).
- Laitsos et al. (2024). *Data-Driven Techniques for Short-Term Electricity Price Forecasting through Novel Deep Learning Approaches with Attention Mechanisms*. [10.3390/en17071625](https://mdpi-res.com/d_attachment/energies/energies-17-01625/article_deploy/energies-17-01625.pdf).
- Michalakopoulos et al. (2026). *Less Is More: Data-Driven Day-Ahead Electricity Price Forecasting with Short Training Windows*. [10.3390/en19020376](https://mdpi-res.com/d_attachment/energies/energies-19-00376/article_deploy/energies-19-00376.pdf).
- Radziukyniene et al. (2026). *A Multi-Parallel Hybrid Neural Network Model for Short-Term Electricity Price Forecasting Under High Market Volatility*. [10.3390/app16083865](https://mdpi-res.com/d_attachment/applsci/applsci-16-03865/article_deploy/applsci-16-03865.pdf).
- Mubarak et al. (2024). *Day-Ahead electricity price forecasting using a CNN-BiLSTM model in conjunction with autoregressive modeling and hyperparameter optimization*. [10.1016/j.ijepes.2024.110206](https://research-repository.griffith.edu.au/server/api/core/bitstreams/f793f553-1e34-4690-ac7a-5822034e7878/content).
- Wang et al. (2024). *Novel Custom Loss Functions and Metrics for Reinforced Forecasting of High and Low Day-Ahead Electricity Prices Using Convolutional Neural Network–Long Short-Term Memory (CNN-LSTM) and Ensemble Learning*. [10.3390/en17194885](https://mdpi-res.com/d_attachment/energies/energies-17-04885/article_deploy/energies-17-04885.pdf).
- Hornek et al. (2025), preprint v2. *Benchmarking Pre-Trained Time Series Models for Electricity Price Forecasting*. [arXiv:2506.08113v2](https://arxiv.org/pdf/2506.08113v2).
- Lu et al. (2026). *A Novel Probabilistic Electricity Price Forecasting Framework with Multi-Factorial Cross-Correlation Embedding and Patch Processing*. [10.3390/en19102438](https://mdpi-res.com/d_attachment/energies/energies-19-02438/article_deploy/energies-19-02438.pdf).
- Lipiecki y Weron (2026), preprint v1. *Foundation models for electricity price forecasting and battery arbitrage: Can they replace market-specific forecasting models?*. [arXiv:2609.00089v1](https://arxiv.org/pdf/2609.00089v1).
- Jasiński (2025). *A Review of Recent Trends in Electricity Price Forecasting Using Deep Learning Techniques*. [10.3390/en18246422](https://mdpi-res.com/d_attachment/energies/energies-18-06422/article_deploy/energies-18-06422.pdf).
- Khalid et al. (2020; online 2019). *Electricity Load and Price Forecasting Using Jaya-Long Short Term Memory (JLSTM) in Smart Grids*. [10.3390/e22010010](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7516403/fullTextXML).
- Zamee et al. (2024). *Self-Supervised Adaptive Learning Algorithm for Multi-Horizon Electricity Price Forecasting*. [10.1109/ACCESS.2024.3389039](https://opus.lib.uts.edu.au/bitstream/10453/181427/2/Self-Supervised_Adaptive_Learning_Algorithm_for_Multi-Horizon_Electricity_Price_Forecasting.pdf).
