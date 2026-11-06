"""Sección de análisis de los abstracts IEEE aportados; código de conteos visible."""
import csv

def ieee_abstract_cells(root):
    with (root/'literature/ieee_abstracts_2026-11-06/selected_abstracts.csv').open(encoding='utf-8',newline='') as f:
        selected=list(csv.DictReader(f))
    with (root/'literature/ieee_abstracts_2026-11-06/records.csv').open(encoding='utf-8',newline='') as f:
        records={r['record_id']:r for r in csv.DictReader(f)}
    refs='\n'.join(f"- **{r['record_id']}.** {records[r['record_id']]['citation']} [DOI]({r['url']})." for r in selected)
    return [
('md',r'''## 9.3 Abstracts de IEEE Xplore: selección y arquitecturas de interés

Las cinco exportaciones aportadas el 6 de noviembre de 2026 contienen **438 registros únicos**. La ampliación evalúa su cercanía al precio eléctrico colombiano, los mecanismos de integración de información operativa y documental, la representación multivariada y la disponibilidad temporal. El cribado asistido por reglas y la lectura detallada de candidatos identifican **12 estudios prioritarios y ocho de contexto**. Cuatro registros están marcados como retractados o avisos de retractación y se excluyen de la evidencia. Los restantes 414 no se priorizan por distancia de objetivo, tarea o redundancia metodológica.

La selección se fundamenta en los abstracts proporcionados. Las afirmaciones de desempeño se atribuyen a sus autores; arquitectura reproducible, comparadores, partición y resultados completos requieren consulta posterior. Este material amplía el mapa de candidatos y no se añade a las frecuencias verificadas de baselines de la sección 9.1. Las exportaciones no incluyen las cadenas originales de búsqueda ni permiten declarar una consulta exhaustiva a IEEE Xplore. Se detectan 28 coincidencias de título normalizado con el inventario heredado, que se registran para conciliación antes de combinar flujos.

El [inventario y la extracción por estudio](https://github.com/Fabian-11037/Time-Series-Project/tree/main/literature/ieee_abstracts_2026-11-06) conservan identificadores, procedencia, huellas, decisiones y evaluación crítica. Los originales y sus abstracts íntegros no se redistribuyen.
'''),
('code',r'''ieee_dir = ROOT/'literature/ieee_abstracts_2026-11-06'
ieee_records = pd.read_csv(ieee_dir/'records.csv',keep_default_na=False)
ieee_screen = pd.read_csv(ieee_dir/'screening.csv',keep_default_na=False)
ieee_selected = pd.read_csv(ieee_dir/'selected_abstracts.csv',keep_default_na=False)
ieee_manifest = json.loads((ieee_dir/'source_manifest.json').read_text(encoding='utf-8'))
assert ieee_records.record_id.is_unique and ieee_screen.record_id.is_unique
assert set(ieee_records.record_id)==set(ieee_screen.record_id)
assert ieee_records.loc[ieee_records.doi.ne(''),'doi'].str.casefold().is_unique
assert sum(f['records'] for f in ieee_manifest['files'])==ieee_manifest['exported_records']
assert len(ieee_records)==ieee_manifest['unique_records']
assert set(ieee_selected.record_id)==set(ieee_screen.loc[ieee_screen.decision.isin(['prioritario','contexto']),'record_id'])
assert not ieee_selected.fulltext_reviewed.any() and not ieee_selected.baseline_frequency_eligible.any()
assert not set(ieee_screen.loc[ieee_screen.decision=='excluido_retractacion','record_id']) & set(ieee_selected.record_id)
ieee_flow = ieee_screen.groupby('decision').size().rename('registros').to_frame()
eda.table(ieee_flow,'ieee_seleccion_abstracts')
eda.table(pd.DataFrame(ieee_manifest['files'])[['file','records','sha256']],'ieee_exportaciones_auditadas')
eda.table(ieee_screen.loc[ieee_screen.decision=='excluido_retractacion',['record_id','title','doi']], 'ieee_retractaciones_excluidas')
'''),
('md',r'''### Estudios prioritarios y alcance de su aportación

**Información operativa anticipatoria.** IEEE428 integra informes de desconexiones programadas en un esquema de predicción inicial y refinamiento mediante clusters, con horizonte de 24 horas para pérdidas de transmisión. Es la referencia más cercana a utilizar anuncios de mantenimientos o restricciones de XM. IEEE280 convierte comentarios del operador de Alberta en series de sentimiento obtenidas con LLM y comunica mejoras de precisión del 2–3 % según modelo y experimento. Ambos pronostican pérdidas, no precios. El segundo abstract no identifica las redes, el LLM ni la métrica concreta; el porcentaje no se adopta como margen colombiano. La utilidad de estos textos depende de acreditar que el anuncio y su versión eran conocidos al origen.

**Eventos y representación documental.** AGESL (IEEE259) combina eventos extraídos de noticias, sentimiento e historia de precios para WTI; su red profunda de fusión no está suficientemente descrita en el resumen. HAN–LSTM (IEEE041) separa la atención sobre palabras/oraciones de la dependencia temporal. BELT (IEEE395) combina BERT ajustado y LSTM apilada con entrenamiento conjunto. Estos dos últimos evalúan dirección de retornos o precios bursátiles; requieren adaptar la salida a regresión de 24 precios y verificar que cualquier diferencia frente a la rama numérica utilice las mismas covariables y orígenes.

**Referencia textual interpretable.** TSITM (IEEE003) acopla LDA con regresión y regularización elastic net para seleccionar tópicos asociados a la serie. Es un control útil antes de introducir fusión profunda, aunque no pertenece a Deep Learning. El submuestreo aleatorio repetido descrito en su abstract debe sustituirse por validación cronológica en esta aplicación. Los tópicos se aprenden dentro de entrenamiento y no se convierten en una taxonomía temática manual.
'''),
('code',r'''ieee_priority = ieee_selected.loc[ieee_selected.priority=='prioritario'].set_index('record_id')
with pd.option_context('display.max_colwidth',None,'display.max_rows',30):
    eda.table(ieee_priority[['title','objective','architecture','project_relevance']], 'ieee_estudios_prioritarios')
    eda.table(ieee_priority[['reported_result','critical_assessment']], 'ieee_resultados_y_limitaciones_abstracts')
'''),
('md',r'''### Priorización de arquitecturas para evaluaciones posteriores

1. **MTS-Mixers (IEEE021) y DLinear como referencia adicional (IEEE023).** Separar mezcla temporal y de canales permite contrastar la necesidad de atención con una alternativa numérica eficiente. El abstract de MTS-Mixers no especifica anchos o profundidad. DLinear figura entre los modelos evaluados en IEEE023; no se infiere de ello una validación en precio eléctrico.
2. **Convolución causal dilatada y multiescala inspirada en CSConv (IEEE025).** Es la ampliación más cercana a CNN1D para captar varios ciclos. CSConv añade filtrado espectral cruzado y una salida basada en MLP; no equivale a una TCN convencional. Espectro y descomposición deben estimarse sobre información pasada de cada origen.
3. **Forwardformer (IEEE088) y DDformer (IEEE010).** El primero aporta atención multiescala y tratamiento de calendario en demanda day-ahead; el segundo combina descomposición tendencia/estacionalidad y transformaciones entre dimensiones. Constituyen alternativas numéricas para dependencias entre precio, demanda y clima. El máximo de reducción de error de 45,9 % declarado por DDformer frente a FEDformer no es una mejora promedio ni una ganancia ya acreditada en XM.
4. **LSTM con HAN o BERT (IEEE041/IEEE395).** Son diseños concretos para fusionar titulares y la representación numérica. Conviene comparar encoder congelado, ajuste del encoder y módulos de atención/relevancia aprendidos, con una rama numérica común y controles de texto permutado o retirado.
5. **Fusión con ponderación dinámica (IEEE096).** El abstract describe BART con LoRA, embeddings BGE M3 y un Transformer encoder-decoder que modula la influencia textual según volumen y consistencia. Esta idea es pertinente para la cobertura editorial desigual. El nombre *Time Fusion Transformers* no demuestra que implemente el Temporal Fusion Transformer canónico. Las reducciones aproximadas de MAE/RMSE y la mejora cold-start que comunica requieren verificar comparadores, periodos y ablaciones. La atención, por sí sola, no identifica un efecto causal.
6. **Salida probabilística y multihorizonte inspirada en RSAM (IEEE079).** Su Transformer con regresión cuantílica permite ampliar la evaluación puntual hacia cobertura y amplitud de intervalos. La evidencia se refiere a irradiancia y meteorología numérica, sin noticias exógenas.

Las referencias numéricas MLP, LSTM y CNN1D existentes mantienen su función de comparación. Esta priorización identifica candidatos; sus espacios, presupuestos y evaluación temporal se definirán tras revisar los textos completos. Las arquitecturas propuestas en abstracts no acreditan por sí mismas uso como baseline en otros estudios.

### Estudios de apoyo y controles de interpretación

CKVF y LHCnn aportan alternativas de retención y convolución con atención; MTSMAE y TS-PTLM plantean preentrenamiento o adaptación de representaciones. Su inspiración en NLP no equivale a incorporar noticias observadas. Los trabajos de clima interior, lluvia y noticias ambientales sirven de contexto para covariables y auditoría documental, sin constituir evidencia directa de mejora en el precio.
'''),
('code',r'''with pd.option_context('display.max_colwidth',None,'display.max_rows',30):
    eda.table(ieee_selected.loc[ieee_selected.priority=='contexto',
        ['record_id','title','architecture','critical_assessment']].set_index('record_id'), 'ieee_estudios_contexto')
ieee_matches = ieee_screen.loc[ieee_screen.inherited_title_matches.ne(''),['record_id','title','inherited_title_matches']]
eda.table(ieee_matches,'ieee_coincidencias_inventario_previo')
'''),
('md',r'''El cribado descarta equivalencias que alterarían la interpretación: FUSION (IEEE276) evalúa recuperación y respuesta a preguntas financieras con ROUGE, no precisión de precios; en IEEE437, NLP significa programación no lineal, no procesamiento de lenguaje natural. *Reservoir computing* (IEEE252) designa una arquitectura recurrente para clasificación documental y no modela embalses hidroeléctricos. En lluvia (IEEE139), la *accuracy* comunicada está insuficientemente definida para compararla con errores de regresión; procesar bidireccionalmente una ventana íntegramente pasada no constituye fuga por sí mismo.

La revisión posterior debe extraer profundidad, ancho, regularización, optimización, comparadores y disponibilidad de cada entrada. Para informes operativos se comprobará anuncio frente a ejecución del evento; para noticias, publicación frente a recuperación; para preentrenamiento, periodo y procedencia del corpus. El aporte textual se evaluará con ablaciones que mantengan invariable la información numérica. Estas condiciones convierten la proximidad temática en una hipótesis verificable, sin atribuir al contexto colombiano las mejoras declaradas en otros dominios.

### Referencias identificadas en los abstracts seleccionados

'''+refs)
    ]
