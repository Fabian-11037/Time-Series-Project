# Contexto para continuar el proyecto

Actualización: 6 de noviembre de 2026. Autores: Fabian José Manrique Morelos y Gloria Bastida. Maestría en Estadística Aplicada, Universidad del Norte.

## 1. Objetivo y estado vigente

Repositorio: https://github.com/Fabian-11037/Time-Series-Project, rama main. Libro: https://fabian-11037.github.io/Time-Series-Project/.

El proyecto estudia el pronóstico del precio nacional horario de bolsa de XM y la integración posterior de series y texto. E1 utiliza exclusivamente variables numéricas y calendario; el corpus documental permanece en el EDA. El proyecto histórico Time-MMD es independiente y sus métricas no se trasladan al caso colombiano.

El dataset y el EDA están disponibles. Se completaron un piloto de 75 ajustes y una búsqueda de 192 configuraciones/4800 ajustes. El benchmark confirmatorio sigue pendiente. La fuente estructurada del alcance es project_scope.json.

## 2. Datos

- data/numeric/hourly/{año}.csv.gz: 227928 horas, 2000–2025; precio, demanda real/comercial y 24 variables meteorológicas de ocho ciudades.
- data/numeric/hydrology/{año}.csv.gz: 9497 días; llenado, reserva útil, capacidad útil y aportes.
- data/text/: 561072 titulares de prensa y 7629 entradas IDEAM/XM; cobertura parcial.
- data/metadata/: diccionario, procedencia, cobertura y disponibilidad.
- data/manifest.json: snapshot 2026-11-03, filas, bytes y SHA-256; data/test_freeze.json mantiene las huellas de 2022–2025.

Ciudades: Bogotá, Medellín, Cali, Barranquilla, Cartagena, Bucaramanga, Pereira y Cúcuta. ERA5 representa puntos de rejilla y no estaciones. La precipitación urbana no representa lluvia en cuencas aportantes; esa ampliación no está descargada. Conservar anomalías de llenado y versiones originales.

La disponibilidad textual declarada usa available_at_assumed; con fecha de día ingresa a las 00:00 del día siguiente en Colombia. available_at_verified exige respaldo de la versión exacta. Se permiten textos de disponibilidad histórica no verificada con su advertencia. No inventar fechas para las 406 entradas XM sin publicación recuperada. No clasificar temas manualmente ni agregar etiquetas al corpus.

## 3. Validación y disponibilidad

Desarrollo 2000–2021, cinco folds expansivos split_train_val_forwardChaining. Las validaciones consecutivas abarcan conjuntamente 2018–2021, sin equivaler a cinco años. Horizonte 24 h, paso 24 h, origen diario a las 00:00 de Colombia. Las etiquetas que cruzan cortes se purgan. Cada escalador utiliza sólo las filas únicas de entrada del entrenamiento de su fold.

Contexto base del piloto: 168 h. Búsqueda: 24/72/168/336 h, con orígenes comunes determinados por 336 h. Las variables horarias se desplazan 24 h; la hidrología se incorpora dos días después del inicio del día de referencia mediante unión hacia atrás. Son supuestos retrospectivos, no horarios certificados; XM y ERA5 pueden contener revisiones. No usar observaciones futuras realizadas como pronósticos disponibles.

La configuración es configs/training_pipeline.json; cortes y preparación en results/pipeline/. La función auditada de timeseries-cv 0.1.5 está en src/colombia_energy/forward_chaining.py, con atribución en third_party/timeseries-cv/. No instalar sus dependencias incompatibles sobre el entorno bloqueado.

El periodo 2022–2025 queda excluido del EDA y de la búsqueda. Los accesos a valores están bloqueados por defecto. No presentar integridad de archivos como certificación de independencia; cualquier evaluación final requiere protocolo específico y justificación de su independencia.

## 4. Modelos y métrica

MAE en COP/kWh es la métrica principal; RMSE y R² son secundarias. Para cada semilla se agrupan todas las horas objetivo de los mismos orígenes de los cinco folds; después se informa media/DE entre semillas, sin ensemble. La DE de inicialización no representa incertidumbre temporal. Referencias: Ugurlu 2018 §4.1, DOI 10.3390/en11051255; Lago 2021 §§5.4–5.4.2, DOI 10.1016/j.apenergy.2021.116983. El MAE conserva la unidad y pérdida lineal; la comparación semanal aporta reducción porcentual equivalente a 100(1-rMAE), no MASE.

| Familia | Candidato | Historia | Regularización | MAE de selección |
|---|---|---:|---:|---:|
| CNN1D | C3: dos convoluciones, 64 filtros, kernel 5 | 24 h | 1e-4 | 24,1547569 |
| LSTM | L2: una capa, 64 unidades | 72 h | 0,001 | 24,6244379 |
| MLP | M3: densas 256–128 | 24 h | 0,001 | 24,9919268 |

Parámetros: CNN1D 43224, LSTM 27928 y MLP 263576. Los tamaños son adaptaciones colombianas, no réplicas exactas de artículos. Piloto: 30 épocas fijas, cinco semillas y cinco folds. Búsqueda: cuatro arquitecturas por familia, cuatro historias, cuatro lambdas; 64 configuraciones/1600 ajustes por familia, cinco semillas 11037–11041. Dropout 0,1, Adam 0,001, salida positiva Softplus; objetivo dividido por DE de entrenamiento sin centrar. L2 explícito sobre matrices, sin sesgos y weight_decay=0.

Parada: mínimo 20 y máximo 200 épocas, paciencia 15, mejora relativa del MAE de validación de 0,2 %; se restaura el checkpoint de menor MAE absoluto. La validación también selecciona candidatos y genera optimismo. El umbral de parada no es δ ni significancia. No se afirma superioridad estadística o equivalencia.

Resultados: results/pilot_pytorch_gfx1030/ y results/variant_search/. Se distribuyen métricas, curvas y 75 predicciones de candidatos seleccionados en selected_predictions.zip y su manifiesto. No todos los pesos ni los 5,4 GB completos de entrenamiento están en Git. No reentrenar automáticamente para reconstruir el libro.

Las fuentes históricas están en resources/experiment_sources/manifest.json. La versión original del protocolo de variantes se localiza mediante resources/protocol_history.json; su huella experimental no corresponde a la edición documental actual. No modificar las configuraciones ni resultados históricos para hacer coincidir una edición posterior.

## 5. EDA y libro

El EDA numérico cubre 192864 horas de desarrollo 2000–2021 y 37 entradas: precio, dos demandas, 24 meteorológicas, cuatro hidrológicas y seis funciones cíclicas de calendario. Se auditan cinco folds y cuatro contextos frente a fold_audit.json. La cobertura diagnóstica de 168 h usa 8027 ventanas admisibles y 192792 filas únicas; sus descripciones se calculan directamente con desarrollo. Los agregados no sustituyen escaladores de cada fold.

Los cortes 2000–2017 / 2018–2021 se conservan para desplazamiento y vocabulario documental de referencia, no como partición única activa. MI usa 12000 horas deterministas; MSTL horaria se limita a 2021, con perfiles/espectro y STL diaria de todo desarrollo. Identificar esos límites de cálculo.

El resumen documental de desarrollo contiene 484289 documentos elegibles; primera disponibilidad recuperada 2004-01-20, sin cobertura continua desde 2000. TF-IDF/NMF conservan ajuste en la muestra protocolizada de 2000–2017; se proyecta y resume todo desarrollo sin reajustar con validación. Los tópicos se aprenden y no se etiquetan manualmente.

Generadores activos: scripts/create_notebooks.py; scripts/create_literature_notebooks.py, que utiliza consolidated_literature_cells.py; scripts/create_model_notebook.py. Las fuentes analíticas de eda.py, headline_eda.py y runtime.py se incorporan íntegramente como celdas visibles. El código puramente editorial usa remove-input; no hide-input ni importaciones privadas que oculten cálculos. Mantener lenguaje académico y evitar aclaraciones conversacionales.

## 6. Literatura

literature/baseline_review/: 20 textos completos, 16 estudios puntuales de precio, dos probabilísticos, uno de regulación/capacidad y una revisión secundaria; 90 registros de modelos. Frecuencias por estudio–familia sólo para comparadores evaluados: LSTM 7/16, MLP/DNN 6/16, CNN 2/16; CNN empata con CNN-LSTM y Transformer, y sólo una fuente confirma 1D. No sumar propuestas, componentes o ablaciones. Cinco candidatos sin texto completo verificado. Revisión focalizada, sin doble revisión independiente.

literature/ieee_abstracts_2026-11-06/: cinco exportaciones aportadas, 438 registros únicos; 12 prioritarios y ocho de apoyo, cuatro registros retractados/avisos excluidos. Hay 28 coincidencias de título con el inventario previo; las cadenas originales faltan. Los resultados nuevos permanecen como evidencia de abstract, sin aumentar frecuencias verificadas de baselines.

literature/consolidated/relevant_studies.csv: 23 estudios destacados, seis eléctricos, siete de texto operativo/financiero y diez generales; once con resultados en texto completo y doce en abstract. País de origen significa afiliación verificada y se distingue del territorio del dataset. CSConv y Time Fusion Transformers no tienen origen verificado. El capítulo 9 contiene tres tablas, matriz de evidencia y gráfico de frecuencias. Los módulos baseline_review_cells.py e ieee_abstract_cells.py son históricos e inactivos: no concatenarlos otra vez.

Prioridades de lectura: IEEE428/280 para texto operativo; MTS-Mixers, CSConv, DDformer y Forwardformer para métodos numéricos; AGESL, HAN–LSTM, BELT y fusión dinámica para texto. Las pérdidas de transmisión no equivalen a precios; la atención no demuestra causalidad. NSW-EPNews retira noticias y temperatura conjuntamente en su ablación: no aísla NLP.

## 7. Ejecución y verificación

Clonar el repositorio y crear un entorno nuevo Python 3.12. Instalar requirements.lock.txt y requirements-pytorch-cpu.txt para documentación. Consultar EJECUCION.md para GPU CUDA/ROCm. Windows/Linux usan bloqueo msvcrt/fcntl; --device auto|cpu|gpu|cuda:N y --threads registran dispositivo. Las nuevas ejecuciones emplean carpetas separadas con sufijo _portable. No copiar entornos ni rutas absolutas entre equipos.

Reproducción: python scripts/verify_dataset.py; python -m unittest discover -s tests; python scripts/prepare_pipeline.py; ejecutar los tres generadores; python scripts/run_eda.py; python scripts/verify_book.py. El ejecutor documental local usa IPython/nbclient sin TCP; --kernel-mode tcp es alternativa. El libro tiene once cuadernos y se publica desde docs/. No se inicia entrenamiento al ejecutar sus celdas documentales.

## 8. Pendientes y continuidad

E1 no está completo: quedan pendientes dimensionamiento, cálculo de IC/tamaños de efecto, ejecución de contrastes con multiplicidad, análisis por horizonte, residuos, robustez, costos completos y evaluación independiente. El protocolo ya fija δ y el tratamiento temporal de la inferencia. No tratar cinco folds por cinco semillas como 25 réplicas independientes. Cinco semillas no garantizan potencia. El usuario seleccionó δ = 2 % de reducción relativa del MAE como criterio operativo intermedio de investigación, sin atribuirle una calibración económica ni una prescripción de la literatura.

Faltan conciliación Scopus 615/562, cadenas y fechas originales, flujo completo y resolución de especificaciones según E1 §3.2. Las 192 configuraciones no acreditan automáticamente el protocolo condicional remitido al E2. Usar primero predicciones existentes para diagnósticos exploratorios; nuevas ejecuciones requieren un protocolo establecido antes de obtener sus resultados.

Las retiradas editoriales y de artefactos quedan registradas en Git; el historial no se reescribe. Mantener las comprobaciones de integridad, disponibilidad y exclusión de periodos en cada ejecución. Actualizar este contexto al modificar el proyecto.

Verificación vigente: once cuadernos, 17 páginas HTML, cero errores y enlaces locales rotos; 34 comprobaciones (33 correctas y una omitida por ausencia de GPU). Los 359 archivos protegidos de datos, literatura y resultados de validación conservan sus SHA-256. Evidencia: results/repository_cleanup_verification.json y results/book_verification.json.


## 9. Protocolo y unidades de evaluación, 6 de noviembre de 2026

Fuentes vigentes: PROTOCOLO_BENCHMARK_2026-11-06.md y configs/benchmark_protocol.json, incorporadas en 8.3/8.4 mediante scripts/benchmark_protocol_cells.py. MAE principal, δ = 2 % elegido por el usuario, α familiar = 0,05, potencia objetivo ≥ 0,80 y tres comparaciones con Holm. Unidad de evaluación: origen diario de 24 precios; bootstrap emparejado por bloques móviles de 14 días, 5000 réplicas, semilla 20261106 y sensibilidad 7/28 días. Remuestreo dentro de fold, sin cruce de huecos y con los mismos índices entre modelos. Se promedian pérdidas entre semillas y se caracteriza la inicialización por separado. El dimensionamiento y el bloque independiente siguen pendientes.

Los IC95 % marginales se distinguen de los simultáneos Bonferroni (98,333 % por par). El umbral de relevancia puntual es g≥0,02; la afirmación de mejora superior al margen requiere límite inferior simultáneo mayor que 0,02. δ y las longitudes se mantienen como decisiones de diseño, sin atribuirlas a un umbral económico de la literatura. La redacción del libro se limita a las definiciones y reglas metodológicas.

Verificación: once cuadernos y 17 páginas, cero errores y enlaces locales rotos; 369 archivos protegidos conservan sus huellas. Evidencia: results/benchmark_protocol_verification.json. Los generadores leen el documento y su configuración; mantener sus huellas y contenido coherentes al editar.
