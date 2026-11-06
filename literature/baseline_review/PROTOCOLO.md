# Protocolo de extracción de baselines

Fecha: 6 de noviembre de 2026. Revisión documental posterior a los experimentos exploratorios; no es un preregistro de entrenamiento.

Pregunta: ¿qué familias numéricas simples se emplean realmente como referencias comparativas para pronosticar precios mayoristas de electricidad?

Universo de partida: los 83 registros preseleccionados en el inventario heredado, la lista de textos ya consultados y una búsqueda pública complementaria específica de precio eléctrico. Se conservan separados sus flujos; no se convierten los conteos heredados 855/668/83 en una búsqueda nueva. La discrepancia Scopus 615/562 permanece documentada.

Ámbito principal: estudios empíricos y benchmarks con precio eléctrico continuo como objetivo, datos reales y modelos numéricos de Deep Learning, publicados o disponibles en texto completo entre 2018 y el 6 de noviembre de 2026. La pregunta exige que el problema principal del estudio sea el precio eléctrico. Los trabajos de demanda, finanzas, clasificación, revisiones sin experimento y métodos generales de series temporales se registran como contexto o se excluyen de la frecuencia principal. Las fechas online prevalecen sobre el año nominal de un número futuro.

Se verifican en texto completo el objetivo, el protocolo de partición, la presencia del modelo en un experimento comparativo y la localización de sus resultados. Las insuficiencias de arquitectura o protocolo se marcan expresamente; un estudio inaccesible no aporta ausencias ni frecuencias verificadas. No se infiere una evaluación a partir de citas o de listas de trabajos relacionados.

Unidad de conteo: estudio único, identificado por DOI o arXiv; versiones y duplicados entre bases se colapsan. Una familia aporta como máximo una presencia por estudio, aunque tenga varios tamaños, semillas, mercados o tablas. Se distingue modelo propuesto, comparador, componente, ablación y mera mención. Sólo comparadores numéricos evaluados aportan la frecuencia principal. Un benchmark comparativo sin arquitectura original propia puede aportar todas sus referencias evaluadas.

Taxonomía: MLP/DNN feed-forward simple se agrupa como familia densa; LSTM unidireccional, BiLSTM, GRU y RNN simple se conservan separadas; CNN y TCN se conservan separadas. La dimensión de CNN se registra explícitamente: la familia convolucional genérica no se equipara automáticamente a CNN1D. Los tamaños de un mismo modelo preentrenado se colapsan, conservando nombres/versiones arquitectónicas diferentes. Un híbrido CNN-LSTM, CNN-GRU o con descomposición no aporta automáticamente una presencia a sus componentes. N-BEATS/N-HiTS y Transformers se registran como arquitecturas específicas, sin inflar la familia MLP o CNN por sus capas internas. Se presenta sensibilidad de agrupaciones, cuando corresponda.

La selección considera conjuntamente recurrencia observada, profundidad/parametrización y sesgos inductivos complementarios. Se muestran todas las familias y denominadores, incluidas las que no pertenecen a los tres candidatos existentes. La revisión puede respaldar o cuestionar MLP/LSTM/CNN1D; no se fijan frecuencias ni ranking antes de extraerlos. Los resultados predictivos colombianos no intervienen en el conteo bibliográfico.

Extracción: referencia/identificador, fuente de descubrimiento, decisión y motivo, versión y SHA-256, páginas de método/resultados, papel del modelo, arquitectura, regularización, entrenamiento, datos, métricas y valores, y evaluación de calidad. La frecuencia se calcula desde registros estructurados mediante código visible en el JBook. Revisión por un único proceso de extracción; no se declara doble revisión independiente ni consenso interevaluador.


## Decisiones de aplicación y sensibilidad

- Corpus recuperado: 20 textos completos; 19 empíricos y una revisión secundaria. Principal: 16 estudios puntuales; sensibilidad: 14 sin preprints y 19 al añadir dos probabilísticos y un mercado relacionado. Cinco candidatos carecen de texto íntegro verificado y quedan fuera de todos los denominadores. Una búsqueda focalizada y acceso público no constituyen una revisión exhaustiva de toda la disciplina.
- Se mantienen en el denominador los estudios puntuales con cero comparadores neuronales admisibles. Un estudio que sólo evalúa variantes de su propuesta no desaparece del corpus porque no aporte las familias seleccionadas.
- GRU de una capa en Ugurlu es control de profundidad (ablación), frente a GRU multicapa propuesta: excluir en estricto; incluir como sensibilidad aumenta GRU de uno a dos estudios. LSTM y ANN son comparadores de la propuesta GRU. La etiqueta LSTM de Less Is More representa LSTM-FFEC según método y figura 6; no cuenta como LSTM independiente.
- Perceptrón sin capa oculta no se cuenta como MLP/DNN. Redes de ramas de ensambles y componentes de híbridos no se desagregan. DNN y MLP simples del mismo artículo se colapsan. DDNN-JSU distribucional conserva su propia familia y estrato.
- Referencias de un benchmark comparativo de arquitecturas conocidas aportan presencias aunque sus autores no utilicen la palabra baseline para cada una. En artículos con arquitectura original, las variantes de la propuesta se conservan como propuesto/ablación. El componente empírico del benchmark Lago 2021 se incluye una vez; su review no añade estudios.
- NR significa especificación insuficiente, no cero capas, ausencia de regularización ni configuración tomada de otro modelo. Se cuentan presencias verificadas aun con defectos metodológicos, que se documentan por estudio. No se convierten esas presencias en garantía de reproducibilidad ni de superioridad.
- Taxonomía conservadora: las versiones nombradas de foundations se conservan separadas (por ejemplo, Moirai y Moirai-2). La tabla mide arquitecturas/modelos identificados, no grandes paradigmas tecnológicos.
- Revisión realizada por un único proceso de extracción; no se declara revisión independiente. La justificación documental es posterior a la búsqueda colombiana ya realizada.

## Archivos y reproducción

`studies.csv` contiene referencias, estrato, protocolo, calidad y SHA-256 de la copia. `extractions.csv` contiene las 90 filas de modelos, roles, configuraciones, métricas y localizadores. `screening_inherited.csv` identifica los 83 registros y motivos. `retrieval_registry.csv` registra 25 candidatos complementarios y su recuperación. `baseline_frequencies.csv` conserva presencia única y denominadores. Los PDF/XML completos permanecen en caché local ignorada, no se redistribuyen.

El código visible de `book/09_literatura.ipynb` recalcula las frecuencias y verifica su concordancia con el CSV, además de comprobar casos de doble conteo y atribución indebida. Para incorporar estudios, editar primero las extracciones verificadas y el registro, ejecutar `python scripts/update_baseline_frequencies.py`, regenerar el capítulo y ejecutar el libro. El script sólo procesa metadatos bibliográficos; no abre series numéricas ni prueba.
