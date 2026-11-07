"""Capítulo comparativo: una entrada por estudio y trazabilidad de resultados/país."""
import csv

def consolidated_literature_cells(root,setup):
    with (root/'literature/consolidated/relevant_studies.csv').open(encoding='utf-8',newline='') as f:
        records=list(csv.DictReader(f))
    def safe(value):return value.replace('|',r'\|').replace('\n',' ')
    def study_table(group):
        lines=['| Estudio y fuente | Origen institucional | País / caso de estudio | Modelo o aporte propuesto | Resultado principal |',
               '|---|---|---|---|---|']
        for r in sorted((x for x in records if x['group']==group),key=lambda x:x['study_id']):
            level='TC' if r['evidence']=='Texto completo' else 'A'
            study=f"**{r['study_id']} · {r['reference']}** · {level}<br>[{safe(r['title'])}]({r['result_source']})"
            origin=f"[{safe(r['origin_country'])}]({r['country_source']})" if r['country_source'] else safe(r['origin_country'])
            lines.append('| '+' | '.join([study,origin,safe(r['study_case']),safe(r['model_or_contribution']),safe(r['result_summary'])])+' |')
        return '\n'.join(lines)
    return [
('md',r'''# 9. Literatura: estudios relevantes y selección de modelos

La síntesis compara **23 estudios** según su proximidad al pronóstico eléctrico colombiano: precio de energía, información textual transferible y métodos generales de series temporales. **TC** identifica resultados contrastados en texto completo; **A**, resultados declarados en el abstract. Se destacan once estudios TC y doce A.

El **origen institucional** corresponde a afiliaciones verificadas de los autores; puede ser parcial en equipos multicéntricos y no indica nacionalidad ni sede del congreso. El territorio de los datos se informa por separado. Las métricas conservan su caso, escala y horizonte: no forman un ranking de precisión entre artículos. «Sin cifra» significa que el abstract no comunica un valor, no que el estudio carezca de resultados.

## 9.1 Comparación de los estudios prioritarios

### Precio eléctrico

Estos trabajos proporcionan evidencia directa para las referencias numéricas y para evaluar la incorporación de noticias al precio de energía.
'''),
('md',study_table('Precio eléctrico')),
('md',r'''### Texto operativo y financiero

Los estudios de pérdidas de transmisión ofrecen la analogía más cercana a los informes de XM. Los de petróleo, acciones y ventas aportan mecanismos de fusión; sus resultados requieren validación en el objetivo colombiano.
'''),
('md',study_table('Texto operativo y financiero')),
('md',r'''### Métodos generales y evaluación multimodal

Estas referencias permiten contrastar eficiencia, dependencia temporal, fusión documental y calidad de la evaluación.
'''),
('md',study_table('Métodos generales')),
('code',setup),
('code',r'''import json
from matplotlib.colors import ListedColormap
catalog = pd.read_csv(ROOT/'literature/consolidated/relevant_studies.csv',keep_default_na=False)
assert catalog.study_id.is_unique and catalog.source_id.is_unique
assert len(catalog)==23 and catalog.fulltext_result.sum()==11
order = {'Precio eléctrico':0,'Texto operativo y financiero':1,'Métodos generales':2}
catalog['group_order'] = catalog['group'].map(order)
catalog = catalog.sort_values(['group_order','study_id'])
catalog['no_external_text'] = 1-catalog['external_text']
matrix_columns = ['electricity_price','other_electricity_variable','no_external_text','external_text','numeric_result','fulltext_result']
evidence_matrix = catalog.set_index('study_id')[matrix_columns]
evidence_matrix.to_csv(RESULTS/'tables/literatura_matriz_evidencia_consolidada.csv')
'''),
('md',r'''### Lectura conjunta de la evidencia

La figura identifica el problema y el tipo de evidencia de cada trabajo. Una marca indica un atributo documentado; su ausencia significa que no se describe o no aplica. «Cifra reportada» incluye porcentajes declarados en abstracts y no califica su validez. La matriz distingue uso de texto externo de arquitecturas simplemente inspiradas en NLP.
'''),
('code',r'''fig,ax = eda.plt.subplots(figsize=(10,8))
ax.imshow(evidence_matrix.to_numpy(),aspect='auto',vmin=0,vmax=1,cmap=ListedColormap(['#f1f3f5','#247e78']))
ax.set_xticks(range(6),['Precio\neléctrico','Otra variable\neléctrica','Sin texto\nexterno','Con texto\nexterno','Cifra\nreportada','Resultado en\ntexto completo'],fontsize=9)
labels = [r.study_id+' · '+r.reference.replace(' et al.','') for r in catalog.itertuples()]
ax.set_yticks(range(len(catalog)),labels,fontsize=9)
for i in range(len(catalog)):
    for j,value in enumerate(evidence_matrix.iloc[i]):
        if value: ax.text(j,i,'•',ha='center',va='center',color='white',fontsize=14)
for cut in [5.5,12.5]: ax.axhline(cut,color='white',lw=3)
ax.grid(False)
ax.set_title('Problema, información y evidencia de los 23 estudios destacados',pad=14)
eda.figure(fig,'literatura_mapa_evidencia_consolidado')
'''),
('md',r'''## 9.2 Síntesis para el diseño del proyecto

**Precio y texto.** NSW-EPNews (P06) es la referencia más próxima al objetivo, pero su ablación retira simultáneamente noticias y temperatura. Los trabajos de pérdidas (T01–T02) motivan priorizar anuncios operativos con publicación anterior al evento. En ambos casos, el aporte textual debe contrastarse manteniendo constantes las entradas numéricas.

**Beneficio condicionado.** REST-TS (G03) mejora Energy y empeora Traffic en los casos extraídos. Tan et al. (G02) muestran que retirar un LLM puede mejorar un modelo numérico, mientras TeR-TSF y TimesX (G04–G05) muestran sensibilidad al contenido y a su construcción. Esta evidencia justifica ablaciones de contenido, procedencia y arquitectura, sin anticipar una mejora universal por NLP.

| Línea de evaluación | Referencias principales | Modelo o mecanismo de interés | Propósito |
|---|---|---|---|
| Referencias numéricas | P01–P05 | MLP, LSTM, CNN1D | Comparar interacciones densas, memoria y patrones locales |
| Eficiencia y multiescala | G06–G09 | MTS-Mixers, CSConv, DDformer, Forwardformer | Contrastar mezcla de canales, convolución causal y atención |
| Fusión documental | T03–T05 | Eventos + red profunda; HAN–LSTM; BERT–LSTM | Aprender representación y relevancia sin categorías manuales |
| Cobertura textual variable | T07; G03 | Ponderación dinámica; supervisión residual | Evitar dependencia espuria del volumen de noticias y text collapse |
| Control interpretable e incertidumbre | T06; G10 | LDA–elastic net; regresión cuantílica | Contrastar complejidad e incorporar calibración de intervalos |

La validación será cronológica. Descomposición, espectro, vocabulario, agrupamientos y escalado se estiman con el pasado disponible en cada fold. Atención no demuestra causalidad; una mejora bursátil o de demanda no acredita mejora del precio eléctrico. Las publicaciones sin configuración suficiente requieren lectura completa antes de definir su implementación.

## 9.3 Justificación de las tres referencias numéricas

La frecuencia se calcula en **16 estudios puntuales de precio eléctrico con texto completo**, contando cada familia una vez por estudio y sólo cuando actúa como comparador evaluado. Propuestas, componentes y ablaciones se excluyen. MLP y DNN simples se agrupan; los híbridos mantienen su identidad. Los abstracts IEEE no incrementan estos conteos.
'''),
('code',r'''review = ROOT/'literature/baseline_review'
studies = pd.read_csv(review/'studies.csv',keep_default_na=False)
extractions = pd.read_csv(review/'extractions.csv',keep_default_na=False)
point_ids = set(studies.loc[studies.estrato=='puntual','study_id'])
peer_ids = set(studies.loc[(studies.estrato=='puntual')&(studies.preprint==0),'study_id'])
all_ids = set(studies.loc[studies.estrato!='contexto_revision','study_id'])
presence = extractions.loc[extractions.papel.isin(['comparador','comparador_benchmark']) &
    (extractions.modelo_neuronal_objetivo==1),['study_id','familia']].drop_duplicates()
def count_studies(ids):
    return presence.loc[presence.study_id.isin(ids)].groupby('familia').study_id.nunique()
families = ['LSTM','MLP/DNN','CNN','CNN-LSTM','Transformer','GRU']
frequency = pd.DataFrame({'Estudios (N=16)':count_studies(point_ids),
    'Sin preprints (N=14)':count_studies(peer_ids),'Ampliado (N=19)':count_studies(all_ids)}).reindex(families).fillna(0).astype(int)
frequency['Porcentaje (N=16)'] = (100*frequency['Estudios (N=16)']/len(point_ids)).round(2)
saved = pd.read_csv(review/'baseline_frequencies.csv').set_index('familia')
assert frequency['Estudios (N=16)'].to_dict()==saved.loc[families,'estudios_puntuales'].to_dict()
assert not len(presence.query("study_id=='ghimire_2024' and familia=='CNN'"))
eda.table(frequency,'literatura_frecuencias_consolidadas')
fig,ax = eda.plt.subplots(figsize=(9,3.7))
values = frequency['Estudios (N=16)'].iloc[::-1]
ax.barh(values.index,values.values,color=['#247e78' if f in ['LSTM','MLP/DNN','CNN'] else '#a0aab2' for f in values.index])
for i,n in enumerate(values): ax.text(n+0.08,i,str(n),va='center')
ax.set(xlabel='Estudios con comparador evaluado',title='Recurrencia de las familias consideradas (N=16)',xlim=(0,8))
ax.set_xticks(range(9))
eda.figure(fig,'literatura_frecuencias_consolidadas')
'''),
('md',r'''LSTM y MLP/DNN son las familias más recurrentes. CNN empata con CNN-LSTM y Transformer; su elección combina recurrencia con una estructura independiente y un sesgo local complementario. Sólo una de las dos referencias CNN confirma explícitamente convolución 1D. Sin preprints se conservan 14 estudios; al añadir un mercado de regulación/capacidad y dos estudios probabilísticos, el denominador es 19.

| Referencia seleccionada | Estructura | Parámetros | Criterio |
|---|---|---:|---|
| MLP M3, 24 h | Dos capas ocultas: 256–128 | 263576 | Interacciones entre posiciones y variables |
| LSTM L2, 72 h | Una capa, 64 unidades | 27928 | Memoria temporal con parámetros compartidos |
| CNN1D C3, 24 h | Dos convoluciones, 64 filtros, kernel 5 | 43224 | Patrones locales y procesamiento de posiciones en paralelo |

Con $p=37$, horizonte $H=24$, anchos densos $d_j$, estado $h$, filtros $c$, kernel $k$ y pooling a $q=7$, se verifican

$$\begin{aligned}
P_{MLP}&=\sum_j(d_{j-1}+1)d_j,\quad d_0=Lp,\ d_{m+1}=H,\\
P_{LSTM}&=4h(p+h+2)+(h+1)H,\\
P_{CNN}&=(kp+1)c+(kc+1)c+(qc+1)H.
\end{aligned}$$

El costo de inferencia por ventana es $O(Lpd_1+\sum d_{j-1}d_j)$, $O(Lh(p+h)+hH)$ y $O(Lk(pc+c^2)+qcH)$, respectivamente; el entrenamiento multiplica ese orden por épocas y ventanas, con factores de retropropagación. Los tamaños seleccionados son adaptaciones de la búsqueda colombiana, no réplicas literales. Las implementaciones y resultados se presentan en el [capítulo 10](10_modelos.ipynb).

## 9.4 Fuentes y alcance de la síntesis

La revisión focalizada del precio contiene 20 textos: 16 estudios puntuales, dos probabilísticos, uno de regulación/capacidad y una revisión secundaria. Cinco candidatos continúan sin texto íntegro verificado. La ampliación IEEE procesa 438 registros y prioriza doce estudios; ocho adicionales se conservan como contexto. Se excluyen cuatro registros retractados o avisos. Las 28 coincidencias de título con el inventario heredado requieren conciliación antes de combinar flujos. La discrepancia de Scopus (615 frente a 562 registros) y las cadenas originales de búsqueda siguen sin conciliar; no se declara una revisión sistemática exhaustiva ni doble evaluación independiente.

El corpus no aporta una comparación de las tres familias con las entradas XM, meteorología e hidrología y la política de disponibilidad del proyecto. Esa brecha delimitada al material revisado motiva el experimento colombiano. La revisión es posterior a sus resultados exploratorios; no fija retrospectivamente el margen práctico, la potencia o la evaluación independiente. La configuración insuficiente de algunas referencias mantiene vigente la condición de E1 §3.2.

La [matriz consolidada](https://github.com/Fabian-11037/Time-Series-Project/tree/main/literature/consolidated) conserva resultados, países y localizadores. La extracción extensa de [baselines](https://github.com/Fabian-11037/Time-Series-Project/tree/main/literature/baseline_review) y el [cribado IEEE](https://github.com/Fabian-11037/Time-Series-Project/tree/main/literature/ieee_abstracts_2026-11-06) permanecen disponibles para auditoría. Véanse las [referencias completas](referencias.md).
''')
    ]
