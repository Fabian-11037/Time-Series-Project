"""Síntesis de apoyo al EDA, distinguiendo texto completo de resúmenes."""
from pathlib import Path
import nbformat as nbf
from create_notebooks import ROOT,BOOK,SETUP

def write(stem,cells):
    nb=nbf.v4.new_notebook(cells=[nbf.v4.new_markdown_cell(s) if kind=='md' else nbf.v4.new_code_cell(s) for kind,s in cells])
    nb.metadata.kernelspec=dict(name='python3',display_name='Python 3',language='python')
    nb.metadata.language_info=dict(name='python',version='3.12')
    path=BOOK/(stem+'.ipynb')
    if path.exists():
        old=nbf.read(path,as_version=4)
        for previous,current in zip(old.cells,nb.cells):
            if previous.cell_type==current.cell_type=='code' and previous.source==current.source:
                current.outputs=previous.get('outputs',[]);current.execution_count=previous.get('execution_count');current.metadata=previous.metadata
    for cell in nb.cells:
        if cell.cell_type=='code' and len(cell.source.splitlines())>4:cell.metadata['tags']=['hide-input']
    nbf.write(nb,path)

def main():
    write('09_literatura',[
('md','''# 9. Literatura consultada e implicaciones para el EDA

Se reutilizan los inventarios aportados de Scopus y Web of Science, la preselección previa y los planes de investigación del programa. La tabla siguiente muestra el estado **heredado** del cribado; no representa una búsqueda sistemática nueva. Las cadenas originales, motivos por registro, consulta de IEEE Xplore y segundo revisor no están acreditados en esos archivos. No se inventan para completar una rúbrica.

La consulta dirigida de apoyo al EDA verificó los textos completos de Time-MMD, NSW-EPNews, Tan y colaboradores, y Lago y colaboradores. Sus URLs, versiones, huellas y localizadores de resultados están en `literature/`. No se publican los PDF privados del curso ni los cuerpos de artículos. Una arquitectura mencionada en un resumen no queda validada como baseline.'''),
('code',SETUP),
('code','''import json
meta=json.loads((ROOT/'literature/inherited_prisma_counts.json').read_text(encoding='utf-8'))
counts=pd.Series({k:meta[k] for k in ['registros_exportados','scopus','wos','unicos','seleccionados']},name='inventario_previo')
eda.table(counts.to_frame(),'literatura_inventario_previo')
audit=json.loads((ROOT/'literature/raw_export_audit.json').read_text(encoding='utf-8'))
eda.table(pd.DataFrame({'exportación_actual':[audit['scopus_current_publication_ids'],audit['wos_current_records']],
    'inventario_previo':[audit['inherited_scopus_count'],audit['inherited_wos_count']]},index=['Scopus','Web of Science']),'literatura_conciliacion_exportaciones')
display(Markdown(f"La exportación actual de Scopus contiene **{audit['scopus_current_publication_ids']}** identificadores distintos, mientras el inventario previo registra **{audit['inherited_scopus_count']}**. La diferencia de **{audit['scopus_difference']}** registros no está conciliada por artículo. Los conteos heredados se preservan como antecedente, no como un PRISMA reproducido desde los archivos actuales."))
selected=pd.read_csv(ROOT/'literature/inherited_selected_83.csv')
freq=selected[['LSTM','GRU','RNN','MLP','CNN']].sum().to_frame('resúmenes_preseleccionados_que_mencionan_arquitectura')
eda.table(freq,'literatura_menciones_no_baselines')
fig,ax=eda.plt.subplots(figsize=(9,4));ax.axis('off')
boxes=[(.9,f"Inventario previo no conciliado: {meta['registros_exportados']} (Scopus {meta['scopus']}, WoS {meta['wos']})"),
       (.65,f"Únicos según inventario previo: {meta['unicos']}"),(.4,f"Preselección por resúmenes: {meta['seleccionados']}"),
       (.15,'Pendiente: elegibilidad por texto completo, motivos y segundo revisor')]
for y,label in boxes:ax.text(.5,y,label,ha='center',va='center',bbox=dict(boxstyle='round',fc='#eef4fa',ec='#245b8d'))
for y in [.82,.57,.32]:ax.annotate('',xy=(.5,y-.08),xytext=(.5,y),arrowprops=dict(arrowstyle='->'))
eda.figure(fig,'flujo_bibliografico_parcial')
'''),
('md','''## Resultados comprobados en texto completo

La tabla es una **extracción puntual**, no un ranking entre artículos: cambian moneda, escala, periodo, horizonte y protocolo. No son resultados de los modelos colombianos. La diferencia entre añadir texto exógeno y usar un LLM sobre números es central.
'''),
('code',"verified=pd.read_csv(ROOT/'literature/verified_extracts.csv')\neda.table(verified,'literatura_resultados_verificados')"),
('md','''**Time-MMD.** El trabajo construye series numéricas y texto alineado en varios dominios y compara versiones uni/multimodales. La tabla de Energy permite comprobar ganancias concretas de DLinear al añadir la rama textual. Es gasolina semanal, no electricidad colombiana: el resultado motiva contrastar fusión, no garantiza transferencia. Para este proyecto importan cobertura, fechas de publicación y versión exacta. [Texto completo, apéndices D.4, K y tabla 12](https://arxiv.org/pdf/2406.08627v2).

**Tan y colaboradores.** Las ablaciones quitan o reemplazan el LLM en modelos alimentados por series numéricas. El resultado no demuestra que las noticias exógenas carezcan de valor. Motiva referencias numéricas fuertes y ablaciones del componente costoso, con incertidumbre y presupuesto comparable. [Texto completo, secciones 3–4 y tabla 3](https://arxiv.org/pdf/2406.16964v2).

**NSW-EPNews.** Combina precios de electricidad, temperatura y noticias. La tabla de resultados muestra que el efecto depende del modelo y de la configuración. Su prompt de ablación retira noticias y temperatura simultáneamente; ese contraste no aísla el aporte exclusivo del texto. Aquí el futuro contraste debe mantener constantes las variables numéricas y añadir sólo texto. Se conservarán salidas numéricas de dimensión fija y se auditará disponibilidad. [Texto completo, secciones 3–4, tablas 1–2 y apéndice C](https://arxiv.org/pdf/2506.11050v1).

**Lago y colaboradores.** El benchmark eléctrico compara redes feed-forward y regresión autorregresiva regularizada en varios mercados. Sus recomendaciones apoyan separar evaluación temporal, comparar referencias fuertes y usar errores interpretables junto con medidas relativas. Los valores de otros mercados no son un umbral en COP. [Texto completo, secciones 3–6 y tabla 2](https://doi.org/10.1016/j.apenergy.2021.116983).

**REST-TS.** La auditoría de la rama textual examina si cambia con el contenido y propone supervisión sobre residuales. Sus tablas incluyen mejoras y regresiones: añadir una rama no basta para atribuir una ganancia al texto. Motiva ablaciones de contenido placebo y comparaciones con el mismo backbone en E2/E3. Una futura propuesta residual deberá distinguir su mecanismo de este antecedente. [Texto completo, secciones 3–4 y tabla 1](https://arxiv.org/pdf/2606.19413).

**TeR-TSF.** Compara texto original, texto generado y texto reforzado por recompensa. Los resultados muestran que generar texto sin el esquema de refuerzo puede empeorar la predicción. Este EDA conserva titulares originales y no rellena huecos con generación. La recompensa y cualquier ajuste posterior deberán usar sólo entrenamiento. [Texto completo, método y tabla 2](https://arxiv.org/pdf/2509.00687).

**TimesX.** Su estudio de sustitución de contexto ilustra que el contenido disponible y la contaminación de preentrenamiento pueden alterar la comparación. Motiva documentar versiones, igualar contexto y no confundir una mejora arquitectónica con información adicional. La política ampliada autorizada aquí no resuelve por sí sola esos riesgos. [Texto completo, sección 3, tabla 3 y apéndice S](https://arxiv.org/pdf/2607.06973).

## Material del programa

Los planes de volatilidad, riesgo, energía con recuperación adaptativa y transferencia son **guías internas, no resultados empíricos publicados**. El plan energético, sección 7.2, pide documentar fuentes, cobertura serie/documentos, calidad, diccionario y sesgo de estaciones/reportes; esos puntos se aplican en este libro. El plan de transferencia recuerda distinguir dominios: pasar de gasolina o finanzas al precio eléctrico requiere evidencia. Las instrucciones de esos planes no reemplazan la solicitud del autor ni las pautas del curso; no se trasladan sus tareas de VaR, generación eólica o publicaciones al presente EDA.

También se revisó la lista de papers y datasets aportada en Excel. Sus notas se conservan como inventario de lectura; las afirmaciones anteriores se verificaron nuevamente en los artículos completos. Los demás títulos de esa lista no se presentan como resultados verificados de esta revisión.

## Consecuencia para E1 y fases posteriores

**E1 usará sólo entradas numéricas.** MLP, LSTM y CNN1D son candidatos de familias con sesgos distintos; la frecuencia de menciones en resúmenes no cierra su elección como los tres baselines exigidos. Falta verificar para esa selección las arquitecturas comparativas de los estudios elegibles. No se implementan ni entrenan aquí esos tres modelos.

El texto queda reservado para E2/E3. Una fusión o un retriever deberán aprender con entrenamiento, sin clasificación temática previa del corpus. La pregunta falsable futura es si añadir texto reduce el error sobre el **mismo bloque numérico** y los mismos orígenes, bajo una política temporal explícita. El escenario ampliado autorizado puede contener fuga por revisiones, que deberá declararse y contrastarse; no se convierte en un resultado operacional por incluir más registros.
'''),
('code',"eda.decision('Derivar el preprocesamiento del EDA numérico de train; registrar cobertura y políticas temporales sin aprender temas globales.', 'E1 exclusivamente numérico; en E2/E3 comparar el mismo bloque numérico con/sin texto y ablaciones de fusión.', 'No transportar métricas entre datasets; fijar presupuesto, semillas, margen y protocolo antes del benchmark.', 'Revisión sistemática y extracción final de tres baselines aún incompletas. Una ganancia publicada no acredita ganancia en Colombia.')")
])
    write('10_conclusiones',[
('md','''# 10. Decisiones derivadas y correspondencia con el Entregable 1

Este cierre se genera a partir de las tablas ejecutadas. Distingue hallazgos del EDA de decisiones que requieren un benchmark. No estima una mejora de NLP ni consulta el desempeño de prueba.'''),
('code',SETUP),
('code','''q=pd.read_csv(ROOT/'results/tables/calidad_train.csv',index_col=0)
d=pd.read_csv(ROOT/'results/tables/distribucion_precio_train.csv',index_col=0)
s=pd.read_csv(ROOT/'results/tables/adf_kpss_train.csv',index_col=0)
t=eda.metadata('coverage_summary.json')
display(Markdown(f"""En entrenamiento se comprobaron **{int(q.loc['horas recibidas','resultado']):,} horas**, **{int(q.loc['horas ausentes','resultado'])} horas ausentes** y **{int(q.loc['claves horarias duplicadas','resultado'])} claves duplicadas**. La asimetría del precio es **{float(d.loc['asimetría'].iloc[0]):.3f}** y su curtosis en exceso **{float(d.loc['curtosis_exceso'].iloc[0]):.3f}**. Los picos se preservan: no se consideran errores sólo por superar un umbral.

El corpus seleccionado contiene **{t['exports']['titulares_prensa_2000_2025.csv']:,} titulares de prensa**, de los cuales **{t['exports']['titulares_prensa_2020_2025.csv']:,}** tienen fecha declarada en el tramo reciente. Hay **{t['exports']['titulos_informes_ideam_xm.csv']:,}** entradas de informes. El conjunto ampliado autorizado reúne **{t['exports']['textos_ampliados_fechas_declaradas_2000_2025.csv']:,}** textos fechados, y el subconjunto de disponibilidad comprobada **{t['exports']['textos_disponibilidad_verificada_2020_2025.csv']:,}** versiones. No se afirma un censo editorial completo ni disponibilidad histórica certificada del conjunto ampliado.
"""))
eda.table(s[['lectura_conjunta']],'conclusion_estacionariedad')
decisions=pd.DataFrame([
['Integridad y rangos','Sin imputación innecesaria; conservar anomalías de llenado y versiones originales.','Máscaras de calidad; no borrar extremos de precio.'],
['Distribución y regímenes','Comparar escala robusta/log1p usando train; evaluar pérdida robusta.','Memoria y adaptación a nivel/varianza; no escoger por prueba.'],
['Ciclos y dependencia','Calendario y rezagos diarios/semanales; filtros operativos causales.','Contexto semanal y salida diaria como propuesta previa al benchmark.'],
['Covariables','Conservar ciudades y frecuencias; acumulados hacia atrás.','E1 numérico multivariado, sin demanda/clima futuros realizados.'],
['Texto y cobertura','Fechas supuestas/comprobadas separadas; desconocidos sin fecha inventada.','Texto sólo para fases posteriores; utilidad y agrupamiento aprendidos con train.'],
['Validación','Cortes temporales, purga de etiquetas que cruzan cortes y prueba congelada.','Mismos orígenes e igual presupuesto; inferencia temporal en benchmark.']
],columns=['hallazgo','preprocesamiento','arquitectura_y_validación'])
eda.table(decisions.set_index('hallazgo'),'matriz_decisiones_eda')
'''),
('md','''## Qué está cubierto y qué falta

Las secciones 2.1 y 2.2.B de las pautas requieren distribución, calidad, sesgos, partición, descomposición, rupturas, ADF/KPSS, ACF/PACF, espectro, no linealidad/heterocedasticidad, anomalías e implicaciones técnicas: estos bloques tienen celdas ejecutadas en el libro. Se añaden asociaciones de covariables y la auditoría documental de la modalidad textual.

La consistencia de prueba se aborda mediante integridad, calendario y procedencia, sin explorar sus valores. No se dispone de verdad instrumental para estimar el ruido de ERA5, ni de ediciones históricas verificadas de todas las entradas. Los casi duplicados semánticos y la revisión sistemática completa siguen abiertos; las limitaciones no se sustituyen por resultados inventados.

El resto del Entregable 1 requiere extracción final de los tres modelos, preregistro experimental, piloto, búsqueda equitativa, múltiples semillas, benchmark e inferencia estadística. **No está ejecutado en este repositorio.** Los tres modelos de esa fase usarán únicamente números. No se reutilizan cifras del E1 de Time-MMD como si fueran resultados colombianos.

Antes de entrenar deben fijarse el escenario de disponibilidad numérica, horizonte/contexto definitivos, métricas, margen práctico, origen de pronóstico y protocolo de búsqueda/repeticiones. El corpus textual puede preservarse completo para E2/E3 mientras los modelos del E1 permanecen numéricos.
''')])

if __name__=='__main__':main()
