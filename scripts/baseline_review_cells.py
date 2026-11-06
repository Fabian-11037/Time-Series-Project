"""Celdas documentales y analíticas de la revisión focalizada de baselines."""
import csv
from pathlib import Path

def baseline_review_cells(root):
    with (root/'literature/baseline_review/studies.csv').open(encoding='utf-8',newline='') as f:
        studies=list(csv.DictReader(f))
    refs='\n'.join(f"- **{s['referencia']}.** {s['titulo']}. [{s['identificador']}]({s['url_texto_completo']})." for s in studies)
    return [
('md',r'''## 9.1 Revisión de uso efectivo como referencia comparativa

La pregunta de esta revisión es qué familias neuronales numéricas se utilizan como referencias comparativas para pronosticar precios eléctricos. Se examinan estudios empíricos y benchmarks cuyo problema principal es el precio eléctrico continuo, con datos reales y texto completo disponible entre 2018 y el 6 de noviembre de 2026. El componente empírico de Lago et al. (2021) se incluye como benchmark; su síntesis secundaria no aporta observaciones adicionales.

El cribado por título y resumen de los 83 registros heredados no identificó estudios centrados en esta comparación. Los métodos generales, el pronóstico de demanda o pérdidas y los estudios financieros se conservan como contexto del proyecto multimodal. Cada decisión y su motivo se registran en [screening_inherited.csv](https://github.com/Fabian-11037/Time-Series-Project/blob/main/literature/baseline_review/screening_inherited.csv). Esto no significa que se hayan revisado 83 textos completos.

Se realizó una búsqueda pública complementaria mediante títulos exactos y combinaciones de *electricity price forecasting*, *MLP/DNN*, *LSTM*, *CNN*, *benchmark* y *baseline*, seguida de recuperación en editoriales, repositorios institucionales, sitios de autores, arXiv y Europe PMC. La búsqueda es focalizada y su cobertura no es exhaustiva. El [registro de recuperación](https://github.com/Fabian-11037/Time-Series-Project/blob/main/literature/baseline_review/retrieval_registry.csv) conserva tanto los textos examinados como los candidatos pendientes. Las frecuencias describen el corpus recuperado; no estiman la prevalencia en toda la disciplina.

La unidad de conteo es el **estudio único por familia**. Varios mercados, tamaños, semillas o configuraciones aportan una sola presencia. Se incluyen modelos efectivamente evaluados como comparadores y referencias de benchmarks sin arquitectura original propia. Se excluyen del conteo estricto las propuestas, los componentes, los controles de ablación y las menciones bibliográficas. Se mantiene en el denominador todo estudio empírico elegible, incluso cuando sólo compara variantes de su propuesta o no utiliza ninguna de las tres familias seleccionadas.

MLP y DNN feed-forward simples se agrupan; LSTM, GRU, RNN simple, BiLSTM, TCN y Transformers se distinguen. Un híbrido conserva su familia propia. N-BEATSx y N-HiTS no se convierten en MLP por sus capas densas internas. CNN agrupa la referencia convolucional independiente; la dimensión se audita por separado antes de vincularla con CNN1D. Las arquitecturas preentrenadas conservan su identificador de modelo, con sus tamaños colapsados. Los estratos probabilístico y de precio de regulación/capacidad se analizan aparte del pronóstico puntual de energía.
'''),
('code',r'''review_dir = ROOT / 'literature/baseline_review'
studies = pd.read_csv(review_dir / 'studies.csv', keep_default_na=False)
extractions = pd.read_csv(review_dir / 'extractions.csv', keep_default_na=False)
screening = pd.read_csv(review_dir / 'screening_inherited.csv', keep_default_na=False)
retrieval = pd.read_csv(review_dir / 'retrieval_registry.csv', keep_default_na=False)
assert studies.study_id.is_unique
assert screening.record_id.is_unique and len(screening) == 83
assert set(extractions.study_id) <= set(studies.study_id)
assert extractions.merge(studies[['study_id','sha256']], on='study_id', suffixes=('_extract','_study')).eval('sha256_extract == sha256_study').all()

empirical_ids = set(studies.loc[studies.estrato != 'contexto_revision', 'study_id'])
point_ids = set(studies.loc[studies.estrato == 'puntual', 'study_id'])
peer_point_ids = set(studies.loc[(studies.estrato == 'puntual') & (studies.preprint == 0), 'study_id'])
flow = pd.DataFrame([
    ['Inventario heredado: cribado por título/resumen', len(screening)],
    ['Inventario heredado: incluidos en frecuencia EPF', 0],
    ['Búsqueda complementaria: textos completos examinados', len(studies)],
    ['Estudios empíricos de pronóstico puntual', len(point_ids)],
    ['Sensibilidad: mercado relacionado', int((studies.estrato == 'mercado_relacionado').sum())],
    ['Sensibilidad: pronóstico probabilístico', int((studies.estrato == 'probabilistico').sum())],
    ['Revisión secundaria excluida del conteo', int((studies.estrato == 'contexto_revision').sum())],
    ['Candidatos pendientes de texto íntegro', int((retrieval.estado == 'pendiente_texto_completo').sum())]
], columns=['etapa','estudios_o_registros'])
eda.table(flow, 'literatura_flujo_revision_baselines')
eda.table(screening.groupby('codigo_motivo').size().to_frame('registros'), 'literatura_exclusiones_83')
eda.table(studies[['study_id','referencia','estrato','identificador']], 'literatura_estudios_baselines')
'''),
('md',r'''### Frecuencias y análisis de sensibilidad

El conteo estricto utiliza 16 estudios de pronóstico puntual. La sensibilidad sin preprints conserva 14; la ampliada incorpora un estudio de regulación/capacidad y dos probabilísticos, para 19 estudios empíricos. El porcentaje de cada familia utiliza el denominador de su columna; como un artículo puede evaluar varias familias, los porcentajes no suman 100 %. Un cero representa ausencia de comparadores verificados en ese estrato, sin atribuir ausencias a artículos inaccesibles.
'''),
('code',r'''allowed_roles = {'comparador', 'comparador_benchmark'}
baselines = extractions.loc[
    extractions.papel.isin(allowed_roles) & (extractions.modelo_neuronal_objetivo == 1)
].copy()
# Una presencia por estudio y familia: evita duplicar DNN/MLP, mercados o tamaños.
presence = baselines[['study_id','familia']].drop_duplicates()
families = sorted(presence.familia.unique())

def study_frequency(study_ids):
    return (presence.loc[presence.study_id.isin(study_ids)]
            .groupby('familia').study_id.nunique()
            .reindex(families, fill_value=0).astype(int))

frequency = pd.DataFrame({
    'estudios_puntuales': study_frequency(point_ids),
    'estudios_puntuales_sin_preprints': study_frequency(peer_point_ids),
    'estudios_ampliados': study_frequency(empirical_ids)
})
frequency['porcentaje_puntual'] = (100 * frequency.estudios_puntuales / len(point_ids)).round(2)
frequency['denominador_puntual'] = len(point_ids)
frequency['denominador_sin_preprints'] = len(peer_point_ids)
frequency['denominador_ampliado'] = len(empirical_ids)
frequency = frequency.sort_values(['estudios_puntuales','familia'], ascending=[False,True])
saved = pd.read_csv(review_dir/'baseline_frequencies.csv').set_index('familia')
pd.testing.assert_frame_equal(frequency.sort_index(), saved[frequency.columns].sort_index(), check_dtype=False)
assert (frequency.estudios_puntuales <= len(point_ids)).all()
# Controles de errores de atribución relevantes para esta revisión.
assert len(presence.query("study_id == 'd3net_2025' and familia == 'MLP/DNN'")) == 1
assert not len(presence.query("study_id == 'lago_2018' and familia == 'CNN'"))
assert not len(presence.query("study_id == 'ghimire_2024' and familia == 'CNN'"))
assert not len(presence.query("study_id == 'multibranch_2026'"))
assert 'LSTM-FFEC' in set(presence.loc[presence.study_id == 'less_more_2026','familia'])
eda.table(frequency[['estudios_puntuales','porcentaje_puntual',
    'estudios_puntuales_sin_preprints','estudios_ampliados']], 'literatura_frecuencias_baseline')

fig, ax = eda.plt.subplots(figsize=(10, 4))
plotted = frequency.loc[frequency.estudios_puntuales >= 2, 'estudios_puntuales'].sort_values()
ax.barh(plotted.index, plotted.values, color=['#4477aa' if f in {'MLP/DNN','LSTM','CNN'} else '#8899aa' for f in plotted.index])
ax.set(xlabel=f'Estudios con comparador evaluado (N={len(point_ids)})', title='Familias con al menos dos estudios; conteo estricto')
ax.set_xticks(range(0, int(plotted.max())+1))
for i, value in enumerate(plotted.values): ax.text(value+0.05, i, str(value), va='center')
ax.set_xlim(0, plotted.max()+1)
eda.figure(fig, 'frecuencia_baselines_texto_completo')

core_simple = baselines.loc[baselines.study_id.isin(point_ids) & baselines.familia.isin(['MLP/DNN','LSTM','CNN'])]
membership = pd.crosstab(core_simple.referencia, core_simple.familia).gt(0).astype(int)
eda.table(membership, 'literatura_matriz_tres_familias')
cnn_1d_ids = set(baselines.loc[(baselines.familia == 'CNN') & (baselines.dimension_convolucion == '1D'), 'study_id']) & point_ids
dimension_audit = pd.DataFrame({'estudios':[len(cnn_1d_ids), len(set(core_simple.loc[core_simple.familia=='CNN','study_id'])-cnn_1d_ids)]},
    index=['CNN con dimensión 1D explícita','CNN con dimensión no reportada'])
eda.table(dimension_audit, 'literatura_dimension_cnn')
'''),
('md',r'''LSTM aparece en **7/16 estudios (43,75 %)** y MLP/DNN en **6/16 (37,50 %)**. CNN independiente aparece en **2/16 (12,50 %)**, empatada con CNN-LSTM y Transformer. Por tanto, la frecuencia por sí sola no determina un tercer modelo único. Al retirar preprints se obtienen 6/14 para LSTM y MLP/DNN y 2/14 para CNN; al ampliar mercados y objetivos, las cifras pasan a 9/19, 8/19 y 4/19, respectivamente.

En la evidencia principal de CNN, Ugurlu et al. especifican convoluciones unidimensionales; D3Net no permite confirmar la dimensión del comparador independiente. La frecuencia estrictamente verificable de **CNN1D es 1/16**. La elección de una implementación temporal unidimensional se fundamenta en esa referencia y en la estructura horaria de la entrada, sin atribuir a todas las CNN la misma configuración.

La clasificación de controles modifica el resultado: si se incluyera la GRU de una capa de Ugurlu et al. como referencia de profundidad, GRU pasaría de 1/16 a 2/16. La tabla principal la conserva como ablación de la propuesta multicapa. Asimismo, la LSTM abreviada en *Less Is More* incorpora corrección feed-forward en su figura 6 y se registra como LSTM-FFEC. El perceptrón sin capa oculta de Laitsos et al., las ramas de la metarred de Radziukyniene et al. y las arquitecturas CNN-BiLSTM-AR o CNN-LSTM con pérdidas modificadas no aportan presencias a sus componentes.

### Configuraciones, resultados y calidad de la evidencia

La extracción conserva arquitectura, regularización, entrenamiento, resultados y páginas o tablas. **NR** significa que la especificación no se reporta de forma suficiente para reproducir ese comparador; no se completa con parámetros del modelo propuesto. Las métricas se mantienen en su mercado, caso y escala. No se promedian errores entre monedas, horizontes o conjuntos de datos.
'''),
('code',r'''configuration = core_simple[['referencia','modelo','arquitectura','regularizacion','entrenamiento','localizador']]
eda.table(configuration, 'literatura_configuraciones_baselines')
eda.table(core_simple[['referencia','modelo','metrica','valor','caso_y_unidad','localizador']], 'literatura_resultados_baselines')
eda.table(studies.loc[studies.estrato != 'contexto_revision', ['referencia','protocolo','evaluacion_critica']], 'literatura_calidad_baselines')
eda.table(retrieval.loc[retrieval.estado == 'pendiente_texto_completo', ['titulo','identificador','motivo']], 'literatura_recuperacion_pendiente')
'''),
('md',r'''Las insuficiencias más relevantes afectan la reproducibilidad de los comparadores y la evaluación temporal. Ugurlu et al. publican dos valores distintos de CNN F1–4 en tablas 2 y 3; se conserva el 8,57 de la tabla 3 con su localizador. Ghimire et al. (2024) reportan un rango vacío para una capa DNN. Khalid et al. presentan RMSE inferior a MAE en la tabla 1, incompatible con una misma escala y muestra, y no documentan suficientemente la partición. Los trabajos con STL/VMD requieren comprobar que la descomposición no utilice observaciones futuras. Estos problemas permiten verificar presencia de una familia, pero impiden trasladar sin examen sus ganancias o configuraciones al experimento colombiano.

La revisión fue realizada mediante un único proceso de extracción; no constituye doble evaluación independiente. El acceso público, la selección focalizada, las publicaciones del mismo grupo de autores y los preprints limitan la generalización de las frecuencias. Cinco candidatos permanecen sin texto íntegro verificado y no intervienen en numerador ni denominador. El inventario heredado de Scopus/WoS continúa requiriendo conciliación; esta revisión no sustituye un flujo PRISMA completo.

## 9.2 Justificación de los tres modelos

**MLP/DNN.** Su recurrencia y el benchmark abierto de Lago et al. respaldan una referencia densa multisalida. Permite estudiar interacciones no lineales entre variables y rezagos con una estructura fácil de inspeccionar. Su debilidad es el crecimiento del número de pesos con la longitud de la ventana y la ausencia de compartición temporal. M3 utiliza dos capas ocultas de 256 y 128 unidades; sus tamaños proceden de la búsqueda colombiana, mientras la literatura fundamenta la familia y el diseño multisalida.

**LSTM.** Es la familia más recurrente del corpus y aporta memoria mediante compuertas, con parámetros compartidos a lo largo de la secuencia. L2, de una capa y 64 unidades, permite contrastar esa memoria con la representación por posiciones de MLP. La recurrencia impone procesamiento secuencial y el estado final puede comprimir en exceso la historia. La literatura no establece superioridad uniforme: el resultado depende de entradas, mercado, ventana y entrenamiento.

**CNN1D.** Se selecciona por su evidencia como comparador y por complementar los otros sesgos inductivos mediante patrones locales, pesos compartidos y procesamiento paralelo de posiciones. C3 tiene dos convoluciones de 64 filtros y kernel 5, seguidas de pooling y salida densa. CNN-LSTM combina dos mecanismos y Transformer añade atención; sus frecuencias empatadas no obligan a adoptarlos cuando se buscan exactamente tres referencias simples y diferenciadas. GRU constituye una alternativa recurrente pertinente, aunque ofrece menor contraste conceptual frente a LSTM que la convolución temporal.

La simplicidad se evalúa por estructura, número de parámetros y costo, no sólo por número de capas. Las tres configuraciones son adaptaciones al mismo horizonte de 24 horas y a 37 predictores; no reproducen exactamente un artículo. Con $p$ predictores, $L$ pasos, $H$ salidas, anchos densos $d_j$, estado recurrente $h$, $c$ filtros, kernel $k$ y pooling a $q$ posiciones, sus parámetros son

$$
P_{\mathrm{MLP}}=\sum_{j=1}^{m+1}(d_{j-1}+1)d_j,\quad d_0=Lp,\ d_{m+1}=H;
$$
$$
P_{\mathrm{LSTM}}=4h(p+h+2)+(h+1)H;
$$
$$
P_{\mathrm{CNN}}=(kp+1)c+(kc+1)c+(qc+1)H.
$$

La LSTM implementada utiliza los dos vectores de sesgo por compuerta de PyTorch. Dropout, ReLU, Softplus y pooling no incorporan parámetros entrenables. Para inferencia por ventana, el costo dominante es $O(Lpd_1+\sum d_{j-1}d_j)$ en MLP, $O(Lh(p+h)+hH)$ en LSTM y $O(Lk(pc+c^2)+qcH)$ en CNN; en las configuraciones seleccionadas $q=7$. El entrenamiento por $E$ épocas y $n$ ventanas multiplica ese orden por $En$, con factores adicionales de retropropagación y optimización. Estos órdenes no predicen por sí solos el tiempo real en CPU/GPU.
'''),
('code',r'''p, H = 37, 24
widths = [24*p, 256, 128, H]
mlp_parameters = sum((a+1)*b for a,b in zip(widths[:-1],widths[1:]))
h = 64
lstm_parameters = 4*h*(p+h+2)+(h+1)*H
c,k,q = 64,5,7
cnn_parameters = (k*p+1)*c+(k*c+1)*c+(q*c+1)*H
complexity = pd.DataFrame([
    ['MLP M3',24,'256–128',mlp_parameters],
    ['LSTM L2',72,'1 capa × 64',lstm_parameters],
    ['CNN1D C3',24,'2 capas × 64; kernel 5',cnn_parameters]
], columns=['modelo','historia_horas','estructura','parametros_entrenables'])
assert list(complexity.parametros_entrenables) == [263576,27928,43224]
eda.table(complexity, 'literatura_complejidad_tres_modelos')
'''),
('md',r'''La revisión documental se realiza después de los experimentos exploratorios existentes. Sustenta la pertinencia de las familias y explicita sus adaptaciones; no convierte la selección previa de tamaños en una decisión bibliográfica a priori. Las frecuencias no incorporan los resultados colombianos ni justifican superioridad estadística. El margen práctico, el dimensionamiento y la evaluación independiente requieren su propio protocolo. La información arquitectónica insuficiente activa la condición de §3.2 del Entregable 1, que remite al procedimiento de búsqueda del Entregable 2; las 192 configuraciones exploradas no acreditan automáticamente el cumplimiento de ese requisito.

### Brecha delimitada por el corpus

Ninguno de los 16 estudios puntuales examinados evalúa conjuntamente estas tres familias en el precio horario de XM con demanda, meteorología de ocho ciudades e hidrología del SIN bajo la política de disponibilidad y los folds expansivos del proyecto. Ésta es una brecha del corpus revisado, sin afirmar ausencia universal de trabajos colombianos. El experimento permite comparar qué representación resulta adecuada para esas entradas y para los cambios de régimen observados.

Las diferencias publicadas ofrecen contexto, no un umbral transferible: Lago et al. (2018) reportan sMAPE de 13,27 % para MLP y 12,34 % para su DNN; Ugurlu et al. registran MAE de 6,37, 5,91 y 8,57 EUR/MWh para ANN, LSTM y CNN en F1–4 de la tabla 3. D3Net comunica mejoras mucho mayores frente a comparadores simples, acompañadas de descomposición y combinación de modelos cuya disponibilidad causal debe comprobarse. Cambian mercado, escala, información y presupuesto; esos resultados no fijan el margen práctico colombiano.

### Referencias de los textos completos examinados

'''+refs)
    ]
