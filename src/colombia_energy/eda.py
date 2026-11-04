"""Análisis de entrenamiento y diagnósticos de validación; cifras desde ejecución."""
import collections
import hashlib
import json
import re
import unicodedata
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display,Markdown
from scipy import signal,stats
from statsmodels.tsa.stattools import adfuller,kpss,acf,pacf,bds
from statsmodels.tsa.seasonal import STL,MSTL
from statsmodels.stats.diagnostic import het_arch,acorr_ljungbox
from statsmodels.tsa.ar_model import AutoReg
from sklearn.feature_selection import mutual_info_regression
from .data import ROOT,TARGET,load_numeric,load_text,metadata,SPLITS,split_for_labels

SEED=11037
RESULTS=ROOT/'results'
RESULTS.mkdir(exist_ok=True)
(RESULTS/'figures').mkdir(exist_ok=True)
(RESULTS/'tables').mkdir(exist_ok=True)
plt.rcParams.update({'figure.figsize':(11,4.4),'figure.dpi':110,'savefig.dpi':160,
 'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,
 'axes.prop_cycle':plt.cycler(color=['#245b8d','#d17a32','#2b8c77','#8c5da8','#9a4949'])})

def table(frame,name):
    frame.to_csv(RESULTS/'tables'/(name+'.csv'),index=True)
    display(frame)
    return None

def figure(fig,name):
    fig.tight_layout();fig.savefig(RESULTS/'figures'/(name+'.png'),bbox_inches='tight');plt.show();plt.close(fig)

def decision(preprocess,architecture,validation,risk):
    display(Markdown('### Implicaciones del análisis\n\n'+
       '\n'.join('- **'+a+':** '+b for a,b in [('Preprocesamiento',preprocess),('Arquitectura',architecture),('Validación',validation),('Riesgos',risk)])))

def train_daily():
    frame=load_numeric();return frame,frame[TARGET].resample('D').mean()

def overview():
    manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
    rows=[]
    for key,prefix in [('Numérico horario','data/numeric/hourly'),('Hidrología diaria','data/numeric/hydrology'),
                      ('Titulares de prensa','data/text/press'),('Títulos oficiales','data/text/official')]:
        files=[r for r in manifest['files'] if r['path'].startswith(prefix)]
        rows.append(dict(bloque=key,archivos=len(files),filas=sum(r['rows'] or 0 for r in files),bytes=sum(r['bytes'] for r in files)))
    table(pd.DataFrame(rows).set_index('bloque'),'inventario')
    summary=metadata('coverage_summary.json')
    table(pd.DataFrame(summary['by_source']).T,'inventario_texto_fuente')
    display(Markdown('La variable objetivo es el **precio nacional de bolsa en COP/kWh**. La unidad de observación es el intervalo horario del SIN; las variables meteorológicas corresponden a puntos de rejilla ERA5. La dependencia serial se considera en el diseño de validación e inferencia.'))
    decision('Conservar frecuencias y ubicaciones originales; no unir cada título duplicando una fila de precio.',
       'Modelar una serie nacional con covariables multivariadas y un conjunto de textos por origen.',
       'Partición por tiempo y etiquetas completas; la cobertura de fuentes es una auditoría estructural.',
       'Fuentes con distinta disponibilidad, revisiones retrospectivas y fuerte desigualdad entre medios.')

def quality():
    frame=load_numeric();hydro=load_numeric(table='hydrology')
    numeric=frame.select_dtypes('number').drop(columns=['xm_hour'],errors='ignore')
    expected=pd.date_range('2000-01-01','2018-01-01',freq='h',inclusive='left',tz='America/Bogota')
    quality=pd.DataFrame({'comprobación':['horas esperadas','horas recibidas','horas ausentes','claves horarias duplicadas',
       'valores numéricos faltantes','valores no finitos','filas hidrológicas','claves diarias duplicadas'],
       'resultado':[len(expected),len(frame),len(expected.difference(frame.index)),frame.index.duplicated().sum(),
       numeric.isna().sum().sum(),(~np.isfinite(numeric.to_numpy())).sum(),len(hydro),hydro.index.duplicated().sum()]})
    table(quality.set_index('comprobación'),'calidad_train')
    stats_table=numeric.agg(['count','min','max','median']).T
    stats_table['nulos']=numeric.isna().sum();table(stats_table,'rangos_train')
    physical={}
    for col in numeric:
        x=numeric[col]
        if 'humidity' in col:physical[col]=int(((x<0)|(x>100)).sum())
        elif 'temperature' in col:physical[col]=int(((x< -90)|(x>60)).sum())
        elif 'precipitation' in col:physical[col]=int((x<0).sum())
        elif 'demanda' in col:physical[col]=int((x<0).sum())
    table(pd.Series(physical,name='fuera_de_rango').to_frame(),'controles_fisicos_train')
    flags=hydro[(hydro['llenado_valor_original']<0)|(hydro['llenado_valor_original']>1)]
    table(flags,'llenado_fuera_intervalo_train')
    display(Markdown(f'Se conservan **{len(flags)}** fechas de llenado fuera de [0,1] en entrenamiento. Son banderas de definición/rango, no una corrección automática. La ausencia de nulos en la tabla numérica no acredita ausencia de error instrumental, sesgo de rejilla o revisiones.'))
    decision('No imputar donde no hay huecos. Preservar las banderas de llenado y contrastar capacidad/volumen antes de corregir.',
       'Máscaras separadas para falta de texto y anomalía numérica; pérdidas robustas candidatas.',
       'La integridad completa del periodo se verifica mediante manifiesto, sin explorar el objetivo de prueba.',
       'No es posible inferir MCAR/MAR/MNAR con una matriz numérica sin faltantes. La falta de texto es selección de archivo y fuente; no se presume MCAR.')

def target_distribution():
    frame,daily=train_daily();y=frame[TARGET]
    desc=y.describe(percentiles=[.01,.05,.25,.5,.75,.95,.99,.999]).to_frame('COP/kWh')
    desc.loc['asimetría']=stats.skew(y);desc.loc['curtosis_exceso']=stats.kurtosis(y)
    table(desc,'distribucion_precio_train')
    fig,axes=plt.subplots(1,3,figsize=(13,3.8))
    axes[0].hist(y,bins=100,color='#245b8d');axes[0].set(xlabel='COP/kWh',ylabel='Horas',title='Precio nominal: entrenamiento')
    axes[1].hist(np.log1p(y),bins=100,color='#2b8c77');axes[1].set(xlabel='log(1 + precio)',title='Transformación candidata')
    q=np.sort(y);axes[2].plot(q,np.arange(1,len(q)+1)/len(q));axes[2].set(xlabel='COP/kWh',ylabel='Probabilidad acumulada',title='Distribución empírica')
    figure(fig,'distribucion_precio')
    q1,q3=y.quantile([.25,.75]);iqr=q3-q1;med=y.median();mad=(y-med).abs().median()
    upper=q3+1.5*iqr;robust=med+6*1.4826*mad
    out=pd.DataFrame({'umbral_superior':[upper,robust],'horas_mayores':[(y>upper).sum(),(y>robust).sum()]},index=['IQR 1,5','MAD 6'])
    table(out,'umbrales_anomalias_train')
    diagnostic=(y-med).abs()
    influence=[]
    for label,mask in [('Mayor que Q99',y>y.quantile(.99)),('Mayor que umbral IQR',y>upper)]:
        influence.append(dict(grupo=label,fraccion_horas=float(mask.mean()),
            fraccion_error_absoluto=float(diagnostic[mask].sum()/diagnostic.sum()),
            fraccion_error_cuadratico=float((diagnostic[mask]**2).sum()/(diagnostic**2).sum())))
    table(pd.DataFrame(influence).set_index('grupo'),'influencia_anomalias_perdida_train')
    display(Markdown('La influencia se mide respecto de la mediana de entrenamiento como centro diagnóstico, no como pronóstico evaluado. Cuantifica cuánto pesan los extremos en errores absolutos y cuadrados sin consultar prueba ni eliminar esos episodios.'))
    fig,axes=plt.subplots(2,1,figsize=(12,7))
    daily.plot(ax=axes[0],lw=.7);daily.rolling(90,min_periods=90).median().plot(ax=axes[0],lw=1.5,label='Mediana móvil pasada 90 días')
    axes[0].set(ylabel='COP/kWh',title='Precio medio diario de entrenamiento');axes[0].legend()
    yearly=frame.assign(anio=frame.index.year).groupby('anio')[TARGET].agg(['mean','median','std','max'])
    yearly[['mean','median']].plot(ax=axes[1],marker='o');axes[1].set(ylabel='COP/kWh',xlabel='Año',title='Nivel nominal y cambios de escala')
    axes[1].set_xticks(yearly.index[::2]);axes[1].set_xticklabels([str(y) for y in yearly.index[::2]])
    axes[1].legend(['Media','Mediana'])
    figure(fig,'precio_regimenes');table(yearly,'precio_anual_train')
    # Fixed-threshold binary segmentation: descriptive mean shifts, not confirmatory events.
    z=np.log1p(daily.to_numpy());z=(z-z.mean())/z.std();cuts=[];pending=[(0,len(z))]
    while pending and len(cuts)<8:
        left,right=pending.pop(0)
        if right-left<180:continue
        x=z[left:right];cs=np.r_[0,np.cumsum(x)];n=len(x);idx=np.arange(90,n-89,7)
        gain=cs[idx]**2/idx+(cs[-1]-cs[idx])**2/(n-idx)-cs[-1]**2/n
        best=int(np.argmax(gain))
        if gain[best]>3*np.log(len(z)):
            cut=left+int(idx[best]);cuts.append((cut,float(gain[best])));pending.extend([(left,cut),(cut,right)])
    breaks=pd.DataFrame([dict(fecha=daily.index[i].date(),ganancia_sse=g) for i,g in sorted(cuts)])
    table(breaks,'rupturas_exploratorias_train')
    fig,ax=plt.subplots();np.log1p(daily).plot(ax=ax,lw=.7)
    for i,g in cuts:ax.axvline(daily.index[i],color='#d17a32',alpha=.6,lw=.8)
    ax.set(title='Rupturas exploratorias de media (log1p diario)',ylabel='log(1 + COP/kWh)');figure(fig,'rupturas_train')
    decision(f'Comparar escala robusta/log1p con escala en COP, ajustadas sólo con train. IQR superior={upper:.2f}; no eliminar picos por ser extremos.',
       'Capacidad para cambios de nivel y colas; considerar salida robusta o probabilística, sin inferir que NLP ya ayuda.',
       'Mantener episodios extremos en evaluación futura y reportar error por régimen; evitar métricas porcentuales cerca de cero.',
       'Precios nominales de años distintos no son poder adquisitivo constante. Una ruptura estadística no identifica su causa; STL centrada y segmentación usan futuro dentro de train y no son atributos operativos.')

def seasonality():
    frame,daily=train_daily();y=frame[TARGET]
    fig,axes=plt.subplots(1,3,figsize=(13,3.8))
    for ax,group,title in [(axes[0],frame.index.hour,'Hora de Colombia'),(axes[1],frame.index.dayofweek,'Día de semana (lunes=0)'),(axes[2],frame.index.month,'Mes')]:
        grouped=y.groupby(group);mean=grouped.mean();lo=grouped.quantile(.25);hi=grouped.quantile(.75)
        ax.plot(mean.index,mean.values,marker='o');ax.fill_between(mean.index,lo,hi,alpha=.2);ax.set(xlabel=title,ylabel='COP/kWh')
    figure(fig,'perfiles_estacionales')
    annual=STL(np.log1p(daily),period=365,robust=True).fit()
    fig=annual.plot();fig.set_size_inches(12,8);figure(fig,'stl_diaria_anual')
    sub=np.log1p(y[y.index.year==2017])
    multiple=MSTL(sub,periods=(24,168),stl_kwargs={'robust':True}).fit()
    fig=multiple.plot();fig.set_size_inches(12,9);figure(fig,'mstl_horaria_2017')
    freq,power=signal.welch(y.to_numpy(),fs=1,nperseg=24*365,detrend='linear')
    valid=freq>0;periods=1/freq[valid];power=power[valid]
    peaks=np.argsort(power)[-12:][::-1]
    table(pd.DataFrame({'periodo_horas':periods[peaks],'potencia':power[peaks]}),'picos_espectrales_train')
    fig,ax=plt.subplots();ax.loglog(periods,power)
    for period in [24,168,24*365]:ax.axvline(period,color='#d17a32',alpha=.65,ls='--');ax.text(period,ax.get_ylim()[1]/4,str(period)+' h',rotation=90)
    ax.set(xlabel='Periodo (horas)',ylabel='Densidad espectral',title='Espectro de Welch: entrenamiento');figure(fig,'espectro_train')
    decision('Calendario conocido al origen y rezagos diarios/semanales; el ciclo anual de 365 días aproxima años bisiestos.',
       'Contexto candidato de una semana y salida de 24 horas; CNN local con acceso a rezagos estacionales o recurrencia/atención.',
       'Comparar contra ingenuos diarios y semanales con los mismos orígenes. No escoger ventanas usando prueba.',
       'Descomposiciones centradas son diagnóstico de train, no preprocesamiento causal listo para desplegar. Los perfiles no demuestran causalidad de hora o estación.')

def temporal_tests():
    frame,daily=train_daily();rows=[]
    candidates={'nivel_diario':daily,'log1p_diario':np.log1p(daily),'diferencia_log1p':np.log1p(daily).diff().dropna()}
    for name,x in candidates.items():
        a=adfuller(x,maxlag=30,regression='c',autolag='AIC',result_object=False)
        with warnings.catch_warnings(record=True) as notes:
            warnings.simplefilter('always');k=kpss(x,regression='c',nlags='auto')
        adf_reject=a[1]<.05;kpss_reject=k[1]<.05
        outcomes={(True,False):'Compatible con estacionariedad', (False,True):'Compatible con raíz unitaria/no estacionariedad',
           (True,True):'Conflicto: rupturas/heterocedasticidad u otra alternativa', (False,False):'Inconcluso: ambas H0 no rechazadas'}
        kp=('<0.01' if k[1]<=.01 else '>0.10' if k[1]>=.10 else f'{k[1]:.6g}')
        rows.append(dict(serie=name,n=len(x),adf_estadistico=a[0],adf_p=a[1],adf_rezagos=a[2],
           kpss_estadistico=k[0],kpss_p_acotado=kp,kpss_rezagos=k[2],lectura_conjunta=outcomes[(adf_reject,kpss_reject)]))
    table(pd.DataFrame(rows).set_index('serie'),'adf_kpss_train')
    y=np.log1p(frame[TARGET].to_numpy());ac,ci=acf(y,nlags=336,fft=True,alpha=.05,result_object=False)
    pc,pci=pacf(y,nlags=168,method='ldbiased',alpha=.05)
    fig,axes=plt.subplots(2,1,figsize=(12,7))
    for ax,vals,bands,title in [(axes[0],ac,ci,'ACF (log1p horario)'),(axes[1],pc,pci,'PACF (Levinson–Durbin)')]:
        lags=np.arange(len(vals));ax.vlines(lags,0,vals,lw=.7);ax.fill_between(lags,bands[:,0]-vals,bands[:,1]-vals,alpha=.25)
        for lag in [24,168]:ax.axvline(lag,color='#d17a32',alpha=.5,ls='--')
        ax.set(xlabel='Rezago horario',ylabel='Correlación',title=title)
    figure(fig,'acf_pacf_train')
    model=AutoReg(np.log1p(daily.to_numpy()),lags=7).fit();resid=model.resid
    arch=het_arch(resid,nlags=14,result_object=False)
    bstat,bp=bds(resid[-1000:],max_dim=3,distance=1.5)
    diagnostics=pd.DataFrame({'estadístico':[arch[0],*np.atleast_1d(bstat)],'p':[arch[1],*np.atleast_1d(bp)]},index=['ARCH LM (14)','BDS dimensión 2','BDS dimensión 3'])
    table(diagnostics,'dependencia_no_lineal_train');table(acorr_ljungbox(resid,lags=[7,14,30],return_df=True),'ljung_box_ar7_train')
    decision('La lectura conjunta ADF/KPSS determina qué transformaciones comparar; no diferenciar automáticamente por un único p-valor.',
       'Memoria estacional y varianza variable justifican comparar arquitecturas y pérdidas robustas con referencias lineales fuertes.',
       'Errores dependientes requieren bootstrap por bloques o inferencia temporal; las horas y semillas no son observaciones independientes equivalentes.',
       'BDS rechaza independencia bajo varias alternativas, incluida heterocedasticidad: no demuestra por sí solo no linealidad de la media ni utilidad del texto. Pruebas exploratorias y sensibles a rupturas.')

def covariates():
    frame=load_numeric();hydro=load_numeric(table='hydrology')
    numeric=frame.select_dtypes('number').drop(columns=['xm_hour'],errors='ignore')
    corr=numeric.corr(method='spearman')
    fig,ax=plt.subplots(figsize=(11,10));im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r')
    labels=[c.replace('relative_humidity_2m_pct_','RH ').replace('temperature_2m_c_','T ').replace('precipitation_preceding_hour_mm_','P ').replace('_kwh','') for c in corr]
    ax.set_xticks(range(len(corr)),labels,rotation=90,fontsize=7);ax.set_yticks(range(len(corr)),labels,fontsize=7)
    fig.colorbar(im,ax=ax,label='Spearman');ax.set_title('Asociaciones contemporáneas descriptivas (train)');figure(fig,'correlaciones_train')
    table(corr[[TARGET]].sort_values(TARGET),'correlacion_contemporanea_train')
    predictors=numeric.drop(columns=TARGET).shift(24)
    aligned=predictors.join(frame[TARGET]).dropna()
    rng=np.random.default_rng(SEED);idx=np.sort(rng.choice(len(aligned),min(12000,len(aligned)),replace=False));sample=aligned.iloc[idx]
    mi=mutual_info_regression(sample.drop(columns=TARGET),sample[TARGET],n_neighbors=5,random_state=SEED)
    lagged=pd.DataFrame({'spearman_rezago_24h':aligned.corr(method='spearman')[TARGET].drop(TARGET),
        'informacion_mutua_muestra_train':mi},index=predictors.columns).sort_values('spearman_rezago_24h')
    table(lagged,'asociaciones_rezagadas_train')
    x=numeric.drop(columns=TARGET);std=x.std();z=(x-x.mean())/std.replace(0,np.nan);matrix=z.dropna(axis=1).to_numpy()
    condition=np.linalg.cond(matrix[::24]);gram=np.corrcoef(matrix[::24],rowvar=False)
    vif=np.diag(np.linalg.pinv(gram))
    table(pd.DataFrame({'VIF_aproximado':vif},index=z.dropna(axis=1).columns).sort_values('VIF_aproximado',ascending=False),'colinealidad_train')
    display(Markdown(f'Número de condición de la matriz estandarizada diaria de covariables: **{condition:.4g}**. El VIF usa pseudoinversa si hay singularidad; se interpreta junto al número de condición, no como identificación causal.'))
    daily=frame[TARGET].resample('D').mean();h=hydro.select_dtypes('number')
    changes=pd.DataFrame({'precio_diario':daily,'reserva_rezago_1d':h['reserva_util_kwh'].shift(1),
      'aportes_acumulados_7d_pasados':h['aportes_kwh_dia'].shift(1).rolling(7).sum(),
      'cambio_reserva_7d_pasado':h['reserva_util_kwh'].shift(1)-h['reserva_util_kwh'].shift(8)})
    table(changes.corr(method='spearman'),'hidrologia_cambios_pasados_train')
    weather=[]
    for c in numeric:
        if any(s in c for s in ['temperature','humidity','precipitation']):
            weather.append(dict(variable=c,media=numeric[c].mean(),sd=numeric[c].std(),p01=numeric[c].quantile(.01),p99=numeric[c].quantile(.99)))
    table(pd.DataFrame(weather).set_index('variable'),'heterogeneidad_ciudades_train')
    fig,axes=plt.subplots(3,1,figsize=(12,9))
    for ax,prefix,label in zip(axes,['temperature','relative_humidity','precipitation'],['Temperatura °C','Humedad %','Lluvia mm/h']):
        cols=[c for c in numeric if c.startswith(prefix)]
        means=numeric[cols].groupby(frame.index.month).mean()
        means.columns=[c.rsplit('_',1)[-1] for c in cols];means.plot(ax=ax);ax.set(xlabel='Mes',ylabel=label);ax.legend(ncol=4,fontsize=7)
    figure(fig,'clima_por_ciudad_train')
    decision('Conservar las ocho ciudades. Acumulados y cambios sólo hacia atrás; estandarización/selección sólo con train.',
       'Bloques numéricos de demanda, clima e hidrología y fusión aprendida; regularizar ante covariables redundantes.',
       'Asociaciones contemporáneas y con rezago son EDA retrospectivo, no evidencia de información conocida ni ganancia fuera de muestra.',
       'Demanda realizada del horizonte y clima futuro realizado producirían fuga. Un día de rezago hidrológico es ilustración, no un rezago de publicación certificado. Lluvia urbana no reemplaza lluvia de cuencas aportantes; esta última no está descargada.')

def text_analysis():
    coverage=pd.read_csv(ROOT/'data/metadata/coverage_2000_2025_by_month_source.csv')
    sources=metadata('coverage_summary.json')['selected_sources']
    fig,axes=plt.subplots(2,1,figsize=(14,8))
    for ax,col,title in [(axes[0],'recovered_title_records_by_declared_publication_month','Títulos recuperados por publicación declarada'),
                        (axes[1],'verified_versions_by_capture_availability_month','Versiones por disponibilidad comprobada')]:
        pivot=coverage.pivot(index='medium',columns='month',values=col).reindex(sources)
        im=ax.imshow(np.log1p(pivot.to_numpy()),aspect='auto',cmap='Blues')
        ax.set_yticks(range(len(sources)),sources);ticks=np.arange(0,len(pivot.columns),24)
        ax.set_xticks(ticks,[pivot.columns[i] for i in ticks],rotation=45,ha='right');ax.set_title(title)
        fig.colorbar(im,ax=ax,label='log(1 + número de títulos)')
    figure(fig,'cobertura_texto_comparada')
    text=load_text();cut=pd.Timestamp('2018-01-01',tz='America/Bogota')
    text['available_parsed']=pd.to_datetime(text['available_at_assumed'],utc=True,format='mixed',errors='coerce')
    text=text[(text['available_parsed']<cut)&(text['quarantined'].astype(str).isin(['0','False','false']))].copy()
    text['caracteres']=text['title_raw'].str.len();text['palabras_espacio']=text['title_raw'].str.split().str.len()
    table(text.groupby('source')[['caracteres','palabras_espacio']].agg(['count','median','mean','max']),'longitud_titulares_train')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    axes[0].hist(text['palabras_espacio'],bins=70);axes[0].set(xlabel='Palabras separadas por espacios',ylabel='Títulos',title='Longitud del texto de entrenamiento')
    annual=text.groupby(text['available_parsed'].dt.year).size();annual.plot(kind='bar',ax=axes[1]);axes[1].set(ylabel='Títulos',xlabel='Año de disponibilidad supuesta')
    figure(fig,'longitud_y_volumen_texto_train')
    def normalized(value):
        return ' '.join(unicodedata.normalize('NFC',value).casefold().split())
    def orthographic(value):
        value=''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c))
        return ' '.join(re.findall(r'\w+',value))
    exact=text['title_raw'].map(normalized);near=text['title_raw'].map(orthographic)
    report=pd.DataFrame({'n':[len(text),text['id'].duplicated().sum(),exact.duplicated().sum(),near.duplicated().sum(),
        text['canonical_url'].duplicated().sum(),(text['palabras_espacio']<=3).sum()]},
        index=['textos fechados elegibles en train ampliado','id repetidos','titulares normalizados repetidos',
           'coincidencias ignorando tildes/puntuación/caja','URL canónicas repetidas','textos de hasta 3 palabras'])
    table(report,'duplicados_textuales_train')
    # Near-duplicate audit within the same article, avoiding any learned semantic grouping.
    from difflib import SequenceMatcher
    pairs=[]
    grouped=text[text['canonical_url'].duplicated(keep=False)].groupby('canonical_url')
    for url,group in grouped:
        titles=list(dict.fromkeys(group['title_raw']))
        if len(titles)>20:continue
        for i,a in enumerate(titles):
            for b in titles[i+1:]:
                ratio=SequenceMatcher(None,orthographic(a),orthographic(b),autojunk=False).ratio()
                if .9<=ratio<1:pairs.append(dict(url_sha256=hashlib.sha256(url.encode()).hexdigest(),similitud_caracteres=ratio))
    table(pd.DataFrame(pairs,columns=['url_sha256','similitud_caracteres']),'casi_duplicados_misma_url_train')
    display(Markdown('La identificación de duplicados considera la URL, la fecha y la similitud ortográfica del titular. Los títulos periódicos se conservan para distinguir repetición editorial y duplicación de registros. El procedimiento cubre variaciones ortográficas dentro de una misma URL; la paráfrasis y la sindicación entre fuentes requieren evaluación semántica adicional.'))
    summary=metadata('coverage_summary.json')
    table(pd.DataFrame(summary['by_source']).T[['titles_all_period','titles_declared_2020_2025','titles_publication_date_unknown',
      'versions_verified_available_by_end_2025','months_2020_2025_with_declared_titles','months_2020_2025_with_verified_availability']],'cobertura_por_fuente')
    decision('Conservar máscaras de recuperación/fuente y fechas supuestas/comprobadas. No rellenar texto ausente con un resumen generado.',
       'Encoder y mecanismo de utilidad entrenados con train; permitir que el modelo ignore texto corto/repetitivo. Agrupamiento, si se usa, se aprende dentro del pipeline.',
       'Auditar cambios de fuente y cantidad de texto; comparar con/sin NLP en los mismos orígenes y con textos placebo en el benchmark futuro.',
       'La variación temporal de cobertura y fuentes puede introducir asociaciones espurias. La recuperación retrospectiva limita la verificación de versiones históricas; los nombres de anexos e informes ofrecen menor especificidad documental que los titulares individuales.')

def validation_design():
    train=load_numeric();valid=load_numeric('validation')
    rows=[]
    for split,frame in [('train',train),('validation',valid)]:
        for c in [TARGET,'demanda_real_kwh','temperature_2m_c_bogota','relative_humidity_2m_pct_barranquilla']:
            x=frame[c]
            rows.append(dict(particion=split,variable=c,n=len(x),media=x.mean(),mediana=x.median(),sd=x.std(),p01=x.quantile(.01),p99=x.quantile(.99)))
    table(pd.DataFrame(rows).set_index(['variable','particion']),'distribuciones_train_validacion')
    shifts=[]
    for c in [TARGET,'demanda_real_kwh','demanda_comercial_kwh','temperature_2m_c_bogota','relative_humidity_2m_pct_barranquilla']:
        a=train[c].resample('D').mean().to_numpy();b=valid[c].resample('D').mean().to_numpy()
        scale=np.quantile(a,.75)-np.quantile(a,.25)
        shifts.append(dict(variable=c,ks_D_descriptivo=stats.ks_2samp(a,b).statistic,
            wasserstein_div_IQR_train=stats.wasserstein_distance(a,b)/scale,
            diferencia_media_div_sd_train=(b.mean()-a.mean())/a.std()))
    table(pd.DataFrame(shifts).set_index('variable'),'desplazamiento_train_validacion')
    # Moving-block bootstrap, exploratory CI under within-period local stationarity.
    a=train[TARGET].resample('D').mean().to_numpy();b=valid[TARGET].resample('D').mean().to_numpy()
    rng=np.random.default_rng(SEED);block=30
    def resample(x):
        starts=rng.integers(0,len(x)-block+1,size=int(np.ceil(len(x)/block)))
        return np.concatenate([x[i:i+block] for i in starts])[:len(x)]
    diffs=np.array([resample(b).mean()-resample(a).mean() for _ in range(199)])
    table(pd.DataFrame({'diferencia_media_COP_kWh':[b.mean()-a.mean()],
       'IC95_bloques_inferior':[np.quantile(diffs,.025)],'IC95_bloques_superior':[np.quantile(diffs,.975)],
       'dias_bloque':[block],'replicas':[199]}),'bootstrap_shift_train_validacion')
    fig,ax=plt.subplots()
    for name,frame in [('Entrenamiento',train),('Validación',valid)]:
        x=np.sort(frame[TARGET].to_numpy());ax.plot(x,np.arange(1,len(x)+1)/len(x),label=name)
    ax.set(xlabel='COP/kWh',ylabel='Distribución acumulada',title='Desplazamiento visible sin consultar prueba');ax.legend();figure(fig,'shift_train_validacion')
    calendar=pd.date_range('2000-01-01','2026-01-01',freq='h',inclusive='left',tz='America/Bogota')
    origins=calendar[168:-23];origins=origins[origins.hour==0]
    labels=collections.Counter(split_for_labels(t,t+pd.Timedelta(hours=24)) for t in origins)
    table(pd.Series(labels,name='origenes_candidatos_calendario').to_frame(),'ventanas_calendario_sin_leer_prueba')
    tests=[]
    from .asof_text import verify_guards,eligible_retrospective,eligible
    verify_guards()
    try:load_numeric('test')
    except PermissionError:tests.append(('carga de prueba bloqueada por defecto',True))
    else:raise AssertionError('Test access allowed')
    assert split_for_labels('2017-12-31T12:00:00-05:00','2018-01-01T12:00:00-05:00')=='purged'
    tests.append(('horizonte que cruza corte eliminado',True))
    table(pd.DataFrame(tests,columns=['control','pasa']).set_index('control'),'controles_fuga')
    display(Markdown('El estadístico KS se presenta sin su p-valor IID: los días son dependientes. Wasserstein es un tamaño de desplazamiento, no prueba causal. El bootstrap de bloques conserva dependencia local y presupone estabilidad aproximada dentro de cada periodo; no corrige cambios estructurales por sí solo. Las ventanas se cuentan desde el calendario, sin leer los valores de prueba.'))
    decision('Ajustar toda transformación sólo con train. Si se recalibra con origen móvil, usar únicamente datos anteriores al origen y una política cerrada antes de prueba.',
       'Comparar capacidad de adaptación de modelos con el mismo presupuesto; no seleccionar una red con estas estadísticas de validación.',
       'Prueba congelada; sólo integridad/calendario/cobertura. Contexto pasado puede atravesar el corte, etiquetas futuras no. Origen es inicio del intervalo a pronosticar.',
       'El uso exploratorio de validación y la incertidumbre sobre disponibilidad y revisiones deben incorporarse a la interpretación de la evaluación predictiva.')
