"""Síntesis de apoyo al EDA, distinguiendo texto completo de resúmenes."""
from pathlib import Path
import nbformat as nbf
from create_notebooks import ROOT,BOOK,SETUP
from inline_notebook_code import apply_presentation_visibility,materialize_notebook

def write(stem,cells):
    nb=nbf.v4.new_notebook(cells=[nbf.v4.new_markdown_cell(s) if kind=='md' else nbf.v4.new_code_cell(s) for kind,s in cells])
    nb=materialize_notebook(nb,stem)
    nb.metadata.kernelspec=dict(name='python3',display_name='Python 3',language='python')
    nb.metadata.language_info=dict(name='python',version='3.12')
    path=BOOK/(stem+'.ipynb')
    if path.exists():
        old=nbf.read(path,as_version=4)
        nb.metadata.update(old.metadata)
        for previous,current in zip(old.cells,nb.cells):
            if previous.cell_type==current.cell_type:current.id=previous.id
            if previous.cell_type==current.cell_type=='code' and previous.source==current.source:
                current.outputs=previous.get('outputs',[]);current.execution_count=previous.get('execution_count');current.metadata=previous.metadata
    apply_presentation_visibility(nb)
    with path.open('w',encoding='utf-8',newline='\n') as stream:nbf.write(nb,stream)

def main():
    write('09_literatura',[
('md','# 9. Literatura consultada e implicaciones metodológicas\n\nLa revisión integra un inventario de Scopus y Web of Science, una preselección de estudios y una consulta dirigida de textos completos. Los conteos del cribado previo se presentan junto con una auditoría de las exportaciones disponibles. La documentación del inventario presenta limitaciones de trazabilidad en las cadenas originales, los motivos de exclusión por registro y la revisión independiente.\n\nLas extracciones verificadas comprenden Time-MMD, NSW-EPNews, Tan y colaboradores, Lago y colaboradores, REST-TS, TeR-TSF y TimesX. El directorio `literature/` registra versiones, fuentes, huellas y localizadores de resultados. La caracterización de modelos de referencia se fundamenta en su descripción metodológica en texto completo.'),
('code',SETUP),
('code','''import json
meta=json.loads((ROOT/'literature/inherited_prisma_counts.json').read_text(encoding='utf-8'))
counts=pd.Series({k:meta[k] for k in ['registros_exportados','scopus','wos','unicos','seleccionados']},name='inventario_previo')
eda.table(counts.to_frame(),'literatura_inventario_previo')
audit=json.loads((ROOT/'literature/raw_export_audit.json').read_text(encoding='utf-8'))
eda.table(pd.DataFrame({'exportación_actual':[audit['scopus_current_publication_ids'],audit['wos_current_records']],
    'inventario_previo':[audit['inherited_scopus_count'],audit['inherited_wos_count']]},index=['Scopus','Web of Science']),'literatura_conciliacion_exportaciones')
display(Markdown(f"La exportación actual de Scopus contiene **{audit['scopus_current_publication_ids']}** identificadores distintos, mientras el inventario previo registra **{audit['inherited_scopus_count']}**. La diferencia de **{audit['scopus_difference']}** registros no está conciliada por artículo. El inventario previo y la exportación actual se presentan por separado hasta completar su conciliación."))
selected=pd.read_csv(ROOT/'literature/inherited_selected_83.csv')
freq=selected[['LSTM','GRU','RNN','MLP','CNN']].sum().to_frame('resúmenes_preseleccionados_que_mencionan_arquitectura')
eda.table(freq,'literatura_menciones_no_baselines')
fig,ax=eda.plt.subplots(figsize=(9,4));ax.axis('off')
boxes=[(.9,f"Registros del inventario previo: {meta['registros_exportados']} (Scopus {meta['scopus']}, WoS {meta['wos']})"),
       (.65,f"Únicos según inventario previo: {meta['unicos']}"),(.4,f"Preselección por resúmenes: {meta['seleccionados']}"),
       (.15,'Evaluación de elegibilidad y revisión independiente en desarrollo')]
for y,label in boxes:ax.text(.5,y,label,ha='center',va='center',bbox=dict(boxstyle='round',fc='#eef4fa',ec='#245b8d'))
for y in [.82,.57,.32]:ax.annotate('',xy=(.5,y-.08),xytext=(.5,y),arrowprops=dict(arrowstyle='->'))
eda.figure(fig,'flujo_bibliografico_parcial')
'''),
('md','## Resultados extraídos de los estudios\n\nLa tabla sintetiza resultados publicados junto con su problema, conjunto de datos, modelos y métricas. Las diferencias de escala, frecuencia, horizonte y protocolo requieren interpretar cada resultado en su contexto experimental.\n'),
('code',"verified=pd.read_csv(ROOT/'literature/verified_extracts.csv')\neda.table(verified,'literatura_resultados_verificados')"),
('md','**Time-MMD.** Integra series numéricas y texto alineado en varios dominios. La comparación de DLinear en Energy aporta evidencia sobre la incorporación de información textual en una serie semanal de gasolina. Su aplicación al precio eléctrico requiere evaluar cobertura, fechas de publicación y estabilidad de las versiones documentales. [Texto completo, apéndices D.4, K y tabla 12](https://arxiv.org/pdf/2406.08627v2).\n\n**Tan y colaboradores.** Las ablaciones reemplazan o retiran el LLM en modelos alimentados por series numéricas. Sus resultados fundamentan la inclusión de referencias numéricas fuertes y evaluaciones del aporte de cada componente bajo presupuestos comparables. [Texto completo, secciones 3–4 y tabla 3](https://arxiv.org/pdf/2406.16964v2).\n\n**NSW-EPNews.** Combina precios eléctricos, temperatura y noticias. El desempeño depende del modelo y de la configuración. La ablación retira simultáneamente noticias y temperatura; para estimar el aporte específico del texto se requiere mantener constantes las covariables numéricas. [Texto completo, secciones 3–4, tablas 1–2 y apéndice C](https://arxiv.org/pdf/2506.11050v1).\n\n**Lago y colaboradores.** Comparan redes densas y regresión autorregresiva regularizada en distintos mercados eléctricos. El benchmark fundamenta la evaluación temporal, la inclusión de referencias competitivas y el reporte conjunto de errores absolutos y relativos. [Texto completo, secciones 3–6 y tabla 2](https://doi.org/10.1016/j.apenergy.2021.116983).\n\n**REST-TS.** Examina la sensibilidad de la rama textual y propone supervisión sobre residuos. La variación de resultados entre dominios fundamenta las ablaciones con texto placebo y las comparaciones con una estructura numérica común. [Texto completo, secciones 3–4 y tabla 1](https://arxiv.org/pdf/2606.19413).\n\n**TeR-TSF.** Compara texto original, generado y ajustado mediante refuerzo. La sensibilidad al procedimiento de generación destaca la importancia de conservar la procedencia del texto y separar los datos utilizados en el ajuste y la evaluación. [Texto completo, método y tabla 2](https://arxiv.org/pdf/2509.00687).\n\n**TimesX.** Analiza el efecto de sustituir el contexto textual y los riesgos de contaminación asociados al preentrenamiento. Sus resultados fundamentan el control de versiones y la igualdad de información disponible entre modelos. [Texto completo, sección 3, tabla 3 y apéndice S](https://arxiv.org/pdf/2607.06973).\n\n## Documentación complementaria\n\nLos planes de investigación del programa orientan la documentación de fuentes, cobertura, calidad y diccionario de variables. La lista de artículos y datasets aportada se incorpora como inventario bibliográfico complementario. La síntesis de resultados utiliza las extracciones verificadas en los artículos completos.\n\n## Implicaciones para el diseño del pronóstico\n\nLas familias MLP, LSTM y CNN1D ofrecen representaciones complementarias de las relaciones entre rezagos, la memoria temporal y los patrones locales. Su caracterización como modelos de referencia requiere completar la extracción de arquitecturas y frecuencias de uso en los estudios elegibles.\n\nLa evaluación del aporte textual requiere comparar modelos con el mismo bloque numérico, los mismos orígenes y una política común de disponibilidad. Los mecanismos de agrupamiento y fusión deben ajustarse con entrenamiento. La incertidumbre sobre versiones retrospectivas se incorpora al análisis de sensibilidad del diseño experimental.\n'),
('code',"eda.decision('Estimar el preprocesamiento y las representaciones con entrenamiento; documentar cobertura y disponibilidad temporal.', 'Comparar representaciones temporales y evaluar el aporte de información adicional mediante ablaciones con una estructura numérica común.', 'Definir presupuesto, semillas, margen y protocolo de evaluación considerando la escala y frecuencia del problema.', 'La trazabilidad del inventario bibliográfico y las diferencias entre dominios condicionan la selección de referencias y la transferencia de resultados.')")
])
    write('10_conclusiones',[
('md','# 11. Síntesis e implicaciones metodológicas\n\nLos resultados del análisis exploratorio se integran para orientar el preprocesamiento, la representación temporal y el diseño de evaluación del pronóstico.'),
('code',SETUP),
('code','''q=pd.read_csv(ROOT/'results/tables/calidad_train.csv',index_col=0)
d=pd.read_csv(ROOT/'results/tables/distribucion_precio_train.csv',index_col=0)
s=pd.read_csv(ROOT/'results/tables/adf_kpss_train.csv',index_col=0)
t=eda.metadata('coverage_summary.json')
display(Markdown(f"""En entrenamiento se comprobaron **{int(q.loc['horas recibidas','resultado']):,} horas**, **{int(q.loc['horas ausentes','resultado'])} horas ausentes** y **{int(q.loc['claves horarias duplicadas','resultado'])} claves duplicadas**. La asimetría del precio es **{float(d.loc['asimetría'].iloc[0]):.3f}** y su curtosis en exceso **{float(d.loc['curtosis_exceso'].iloc[0]):.3f}**. Los valores extremos se conservan y se interpretan como parte de la distribución observada.

El corpus seleccionado contiene **{t['exports']['titulares_prensa_2000_2025.csv']:,} titulares de prensa**, de los cuales **{t['exports']['titulares_prensa_2020_2025.csv']:,}** tienen fecha declarada en el tramo reciente. Hay **{t['exports']['titulos_informes_ideam_xm.csv']:,}** entradas de informes. El conjunto de fechas declaradas reúne **{t['exports']['textos_ampliados_fechas_declaradas_2000_2025.csv']:,}** textos fechados, y el subconjunto de disponibilidad comprobada **{t['exports']['textos_disponibilidad_verificada_2020_2025.csv']:,}** versiones. La cobertura corresponde al archivo recuperado y a las condiciones de disponibilidad documentadas.
"""))
eda.table(s[['lectura_conjunta']],'conclusion_estacionariedad')
decisions=pd.DataFrame([
['Integridad y rangos','Sin imputación innecesaria; conservar anomalías de llenado y versiones originales.','Máscaras de calidad; no borrar extremos de precio.'],
['Distribución y regímenes','Comparar escala robusta/log1p usando train; evaluar pérdida robusta.','Memoria y adaptación a nivel/varianza; no escoger por prueba.'],
['Ciclos y dependencia','Calendario y rezagos diarios/semanales; filtros operativos causales.','Contexto semanal y salida diaria como propuesta previa al benchmark.'],
['Covariables','Conservar ciudades y frecuencias; acumulados hacia atrás.','Representación multivariada con observaciones disponibles al origen.'],
['Texto y cobertura','Fechas supuestas/comprobadas separadas; desconocidos sin fecha inventada.','Representaciones documentales ajustadas con entrenamiento y evaluadas mediante un protocolo temporal común.'],
['Validación','Cortes temporales, purga de etiquetas que cruzan cortes y prueba congelada.','Mismos orígenes e igual presupuesto; inferencia temporal en benchmark.']
],columns=['hallazgo','preprocesamiento','arquitectura_y_validación'])
eda.table(decisions.set_index('hallazgo'),'matriz_decisiones_eda')
'''),
('md','## Limitaciones y desarrollo del estudio\n\nEl análisis caracteriza la distribución, calidad, dependencia temporal, estacionalidad, cambios de régimen, heterocedasticidad y asociaciones entre variables. El estudio documental complementa estos resultados mediante la cobertura de fuentes, las características léxicas y la representación de tópicos.\n\nLas limitaciones principales corresponden a la representación meteorológica mediante rejillas de reanálisis, la disponibilidad histórica de las versiones numéricas y textuales y la desigual cobertura editorial. La evaluación de duplicados semánticos y la conciliación del inventario bibliográfico constituyen extensiones del análisis.\n\nLa evaluación numérica comprende una búsqueda de 192 configuraciones de MLP, LSTM y CNN1D, con 4800 ajustes sobre desarrollo. El capítulo de modelos presenta las arquitecturas seleccionadas, sus fundamentos y resultados frente a la referencia semanal. Las métricas de validación también intervienen en la parada y selección, por lo que no constituyen una evaluación externa imparcial. La definición de un margen de relevancia práctica, el análisis de potencia y la inferencia con dependencia temporal permanecen pendientes.\n')])

if __name__=='__main__':main()
