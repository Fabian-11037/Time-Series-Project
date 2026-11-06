"""EDA lingüístico y NMF ajustados sólo en entrenamiento; no atributos del E1."""
import collections
import hashlib
import json
import re
import time
import unicodedata
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Markdown,display
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import jensenshannon
from sklearn.decomposition import NMF
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .data import ROOT,load_text
from .eda import table,figure,decision

TOKEN=re.compile(r'(?u)\b[^\W\d_]{3,}\b')
STOPWORDS=set((ROOT/'resources/spanish_stopwords.txt').read_text(encoding='utf-8').splitlines())
CONFIG=dict(n_topics=8,max_features=20000,min_df=10,max_df=.85,max_per_year=4000,
    max_fit_documents=50000,min_fit_content_terms=4,max_iter=250,tol=1e-4,
    seed=11037,stability_seed=11038,diversity_block_tokens=1000)
OUT=ROOT/'results/headlines';OUT.mkdir(parents=True,exist_ok=True)

def normalized(text):return ' '.join(unicodedata.normalize('NFC',text).casefold().split())

def tokenize(text):
    return [w for w in TOKEN.findall(unicodedata.normalize('NFC',text).casefold()) if w not in STOPWORDS]

def dated_frame(raw,start,end):
    """No inventa fechas; asigna por disponibilidad supuesta, no por edición/año de archivo."""
    keep=['id','source','source_kind','title_kind','title_raw','url','available_at_assumed','quarantined']
    frame=raw[keep].copy()
    stamps=pd.to_datetime(frame['available_at_assumed'],utc=True,format='mixed',errors='coerce')
    clean=frame['quarantined'].astype(str).isin(['0','False','false'])
    selected=clean&stamps.ge(pd.Timestamp(start))&stamps.lt(pd.Timestamp(end))
    frame=frame.loc[selected].copy()
    frame['available']=stamps.loc[selected].dt.tz_convert('America/Bogota')
    frame['year']=frame['available'].dt.year
    frame['month']=frame['available'].dt.strftime('%Y-%m')
    return frame.sort_values(['available','id']).reset_index(drop=True)

def training_sample(frame,config=CONFIG):
    """Fit eligibility is checked here even if the caller accidentally mixes partitions."""
    times=pd.to_datetime(frame['available'],utc=True)
    if times.isna().any() or (times<pd.Timestamp('2000-01-01T00:00:00-05:00')).any() or (times>=pd.Timestamp('2018-01-01T00:00:00-05:00')).any():
        raise ValueError('El ajuste de vocabulario/tópicos sólo admite entrenamiento anterior a 2018.')
    fit=frame[frame['source_kind']=='news'].copy()
    fit['normalized']=fit['title_raw'].map(normalized)
    fit=fit.drop_duplicates('normalized')
    fit=fit[fit['title_raw'].map(lambda x:len(tokenize(x)))>=config['min_fit_content_terms']].copy()
    fit['rank']=fit['id'].map(lambda s:hashlib.sha256(s.encode()).hexdigest())
    fit=fit.sort_values('rank').groupby('year',sort=True).head(config['max_per_year'])
    return fit.sort_values('rank').head(config['max_fit_documents']).reset_index(drop=True)

def contributions(w,h):
    """Normalize reconstructed feature mass, resolving arbitrary NMF component scales."""
    mass=w*h.sum(axis=1)[None,:]
    total=mass.sum(axis=1)
    return np.divide(mass,total[:,None],out=np.zeros_like(mass),where=total[:,None]>0)

class HeadlineStudy:
    def __init__(self):
        raw_train=load_text('train')
        self.train=dated_frame(raw_train,'2000-01-01T00:00:00-05:00','2018-01-01T00:00:00-05:00')
        carry=dated_frame(raw_train,'2018-01-01T00:00:00-05:00','2022-01-01T00:00:00-05:00')
        raw_validation=load_text('validation')
        valid=dated_frame(raw_validation,'2018-01-01T00:00:00-05:00','2022-01-01T00:00:00-05:00')
        self.validation=pd.concat([carry,valid],ignore_index=True).drop_duplicates('id').sort_values(['available','id']).reset_index(drop=True)
        self.fit=training_sample(self.train)
        self.counters={};self.diagnostics={};self.weights={}

    def lexical(self):
        rows=[];diversity=[]
        for split,frame in [('train',self.train),('validation',self.validation)]:
            overall=collections.Counter();df=collections.Counter()
            for text in frame['title_raw']:
                words=tokenize(text);overall.update(words);df.update(set(words))
            self.counters[split]=(overall,df)
            lengths=frame['title_raw'].str.split().str.len()
            rows.append(dict(particion=split,titulares=len(frame),mediana_palabras_originales=lengths.median(),
                terminos_contenido=sum(overall.values()),vocablos_distintos=len(overall),
                fraccion_titulo_normalizado_repetido=frame['title_raw'].map(normalized).duplicated().mean(),
                fraccion_con_cifras=frame['title_raw'].str.contains(r'\d',regex=True).mean(),
                fraccion_con_interrogacion=frame['title_raw'].str.contains('?',regex=False).mean(),
                fraccion_sin_terminos_contenido=frame['title_raw'].map(lambda t:not tokenize(t)).mean()))
            for year,group in frame.groupby('year'):
                stream=[];blocks=[]
                for text in group.sort_values('id')['title_raw']:
                    stream.extend(tokenize(text))
                    while len(stream)>=CONFIG['diversity_block_tokens']:
                        words=stream[:CONFIG['diversity_block_tokens']];stream=stream[CONFIG['diversity_block_tokens']:]
                        blocks.append(len(set(words))/len(words))
                diversity.append(dict(particion=split,anio=year,titulares=len(group),bloques_completos=len(blocks),
                    diversidad_mediana=np.median(blocks) if blocks else np.nan,
                    diversidad_q25=np.quantile(blocks,.25) if blocks else np.nan,
                    diversidad_q75=np.quantile(blocks,.75) if blocks else np.nan))
        table(pd.DataFrame(rows).set_index('particion'),'titulares_resumen_linguistico')
        counter,df=self.counters['train']
        most=pd.DataFrame([dict(termino=w,apariciones=counter[w],titulares=df[w],porcentaje_titulares=100*df[w]/len(self.train))
            for w,_ in df.most_common(30)]).set_index('termino')
        table(most.head(20),'titulares_terminos_frecuentes_train')
        fig,ax=plt.subplots(figsize=(11,7));most.head(25).iloc[::-1]['porcentaje_titulares'].plot.barh(ax=ax)
        ax.set(xlabel='% de titulares de entrenamiento',ylabel='',title='Términos de contenido frecuentes: sin selección temática')
        figure(fig,'titulares_frecuencias_train')
        diversity=pd.DataFrame(diversity);table(diversity.set_index(['particion','anio']),'titulares_diversidad_anual')
        fig,ax=plt.subplots(figsize=(11,4.5))
        for split,group in diversity.groupby('particion',sort=False):
            ax.plot(group['anio'],group['diversidad_mediana'],marker='o',label=split)
            ax.fill_between(group['anio'],group['diversidad_q25'],group['diversidad_q75'],alpha=.2)
        ax.axvline(2017.5,color='#9a4949',ls='--');ax.set(xlabel='Año de disponibilidad supuesta',ylabel='Tipos / 1.000 términos',title='Diversidad léxica en bloques de igual longitud');ax.legend()
        figure(fig,'titulares_diversidad_anual')
        display(Markdown('Las bandas representan el rango intercuartílico de bloques de 1.000 términos. Se excluye el bloque incompleto de cada año y se conserva un orden determinista por identificador. La diversidad y las frecuencias caracterizan la composición léxica del archivo recuperado.'))

    def fit_topics(self):
        start=time.perf_counter()
        (OUT/'protocol.json').write_text(json.dumps(CONFIG,indent=2),encoding='utf-8')
        self.vectorizer=TfidfVectorizer(tokenizer=tokenize,token_pattern=None,lowercase=False,
            ngram_range=(1,2),min_df=CONFIG['min_df'],max_df=CONFIG['max_df'],max_features=CONFIG['max_features'],sublinear_tf=True)
        self.x_fit=self.vectorizer.fit_transform(self.fit['title_raw'])
        self.features=self.vectorizer.get_feature_names_out()
        def fit_model(seed):
            model=NMF(n_components=CONFIG['n_topics'],init='nndsvdar',solver='cd',beta_loss='frobenius',
                max_iter=CONFIG['max_iter'],tol=CONFIG['tol'],random_state=seed)
            with warnings.catch_warnings(record=True) as notes:
                warnings.simplefilter('always',ConvergenceWarning);w=model.fit_transform(self.x_fit)
            return model,w,[str(n.message) for n in notes if issubclass(n.category,ConvergenceWarning)]
        self.model,self.w_fit,notes=fit_model(CONFIG['seed'])
        second,_,notes2=fit_model(CONFIG['stability_seed'])
        similarity=cosine_similarity(self.model.components_,second.components_)
        left,right=linear_sum_assignment(-similarity)
        self.stability=dict(zip(left,similarity[left,right]))
        self.labels={i:f'T{i+1:02d}' for i in range(CONFIG['n_topics'])}
        self.terms={i:self.features[np.argsort(h)[::-1][:10]].tolist() for i,h in enumerate(self.model.components_)}
        fit_ids='\n'.join(sorted(self.fit['id']))
        self.fit_audit=dict(configuration=CONFIG,fit_split='train',validation_fit_documents=0,test_documents_read=0,
            raw_train_documents=len(self.train),fit_documents=len(self.fit),fit_min_available=str(self.fit['available'].min()),
            fit_max_available=str(self.fit['available'].max()),fit_ids_sha256=hashlib.sha256(fit_ids.encode()).hexdigest(),
            features=len(self.features),first_iterations=self.model.n_iter_,second_iterations=second.n_iter_,
            first_convergence_warnings=notes,second_convergence_warnings=notes2,
            relative_frobenius_error=self.model.reconstruction_err_/np.sqrt(self.x_fit.multiply(self.x_fit).sum()),
            stability_mean_cosine=float(similarity[left,right].mean()),seconds=time.perf_counter()-start,
            E1_numeric_only=True,raw_dataset_modified=False)
        (OUT/'fit_audit.json').write_text(json.dumps(self.fit_audit,ensure_ascii=False,indent=2),encoding='utf-8')
        (OUT/'vocabulary.json').write_text(json.dumps(self.features.tolist(),ensure_ascii=False),encoding='utf-8')
        np.savez_compressed(OUT/'nmf_components.npz',components=self.model.components_)
        np.savez_compressed(OUT/'tfidf_idf.npz',idf=self.vectorizer.idf_)
        table(self.fit.groupby(['year','source']).size().rename('titulares_para_ajuste').to_frame(),'titulares_muestra_ajuste_train')
        table(pd.DataFrame([dict(topico=self.labels[i],terminos=' · '.join(self.terms[i]),coseno_otra_semilla=self.stability[i])
            for i in range(CONFIG['n_topics'])]).set_index('topico'),'titulares_topicos_terminos_estabilidad')
        fig,axes=plt.subplots(4,2,figsize=(14,15))
        for i,ax in enumerate(axes.flat):
            h=self.model.components_[i];idx=np.argsort(h)[-8:]
            ax.barh(self.features[idx],h[idx]/h.sum());ax.set(title=self.labels[i],xlabel='Peso relativo en el componente')
            ax.tick_params(axis='y',labelsize=10)
        figure(fig,'titulares_topicos_nmf')
        display(Markdown(f"El ajuste utilizó **{len(self.fit):,}** titulares distintos de entrenamiento y **{len(self.features):,}** características. Error relativo de reconstrucción TF-IDF: **{self.fit_audit['relative_frobenius_error']:.3f}**. Similitud coseno media entre componentes emparejados de dos semillas: **{self.fit_audit['stability_mean_cosine']:.3f}**. Estas medidas resumen la capacidad de reconstrucción y la reproducibilidad de los componentes."))
        weakest=min(self.stability,key=self.stability.get)
        display(Markdown(f"La muestra de ajuste cubre **{self.fit['available'].min().date()} a {self.fit['available'].max().date()}**. El componente menos estable es **{self.labels[weakest]}**, con coseno **{self.stability[weakest]:.3f}**. El residuo conserva **{100*self.fit_audit['relative_frobenius_error']**2:.1f} %** de la energía cuadrática TF-IDF original: la energía residual cuantifica la información TF-IDF que permanece fuera de la aproximación de ocho componentes."))
        if notes or notes2:display(Markdown('**Convergencia:** '+str(notes+notes2)+' Se conserva el ajuste aproximado y su límite de iteraciones; no se selecciona otra configuración por sus resultados.'))
        df=np.asarray(self.x_fit.getnnz(axis=0)).ravel()
        bigrams=[i for i,t in enumerate(self.features) if ' ' in t]
        idx=sorted(bigrams,key=lambda i:df[i],reverse=True)[:25]
        table(pd.DataFrame({'bigrama':self.features[idx],'titulares_en_muestra_ajuste':df[idx]}).set_index('bigrama'),'titulares_bigramas_train')
        # Examples chosen only from train, with at least four content words.
        sim=np.asarray(self.x_fit@self.model.components_.T)/np.maximum(np.linalg.norm(self.model.components_,axis=1),1e-12)
        sample_weights=contributions(self.w_fit,self.model.components_);examples=[]
        for i in range(CONFIG['n_topics']):
            candidates=np.flatnonzero(sample_weights.argmax(axis=1)==i)
            selected=candidates[np.argsort(sim[candidates,i])[::-1][:3]]
            for j in selected:
                r=self.fit.iloc[j];examples.append(dict(topico=self.labels[i],fecha=str(r['available'].date()),fuente=r['source'],
                    titular=r['title_raw'],coseno=float(sim[j,i]),id=r['id'],url=r['url']))
        ex=pd.DataFrame(examples);ex.to_csv(OUT/'training_topic_examples.csv',index=False)
        with pd.option_context('display.max_colwidth',100):display(ex[['topico','fecha','fuente','titular','coseno']])

    def transform(self,frame):
        results=[];h=self.model.components_;gram=h@h.T
        for left in range(0,len(frame),10000):
            x=self.vectorizer.transform(frame['title_raw'].iloc[left:left+10000])
            with warnings.catch_warnings(record=True) as notes:
                warnings.simplefilter('always',ConvergenceWarning);w=self.model.transform(x)
            if notes:self.transform_warning_count+=len(notes)
            weights=contributions(w,h);represented=(np.asarray(x.getnnz(axis=1)).ravel()>0)&(weights.sum(axis=1)>0)
            weights[~represented]=np.nan
            xnorm=np.asarray(x.multiply(x).sum(axis=1)).ravel()
            squared=np.maximum(xnorm-2*(w*np.asarray(x@h.T)).sum(axis=1)+(w@gram*w).sum(axis=1),0)
            error=np.divide(np.sqrt(squared),np.sqrt(xnorm),out=np.full(len(w),np.nan),where=xnorm>0)
            part=pd.DataFrame(weights,columns=list(self.labels.values()))
            part['represented']=represented;part['reconstruction_error']=error;results.append(part)
        return pd.concat(results,ignore_index=True)

    def profiles(self):
        self.transform_warning_count=0;summary=[];all_months=[]
        labels=list(self.labels.values())
        for split,frame in [('train',self.train),('validation',self.validation)]:
            result=self.transform(frame);self.weights[split]=result
            w=result[labels].to_numpy();entropy=-np.nansum(np.where(w>0,w*np.log(np.maximum(w,1e-15)),0),axis=1)/np.log(CONFIG['n_topics'])
            entropy[~result['represented']]=np.nan
            result['entropy']=entropy
            summary.append(dict(particion=split,titulares=len(frame),fraccion_sin_representacion=1-result['represented'].mean(),
                maxima_contribucion_media=result[labels].max(axis=1).mean(),entropia_normalizada_media=np.nanmean(entropy),
                error_reconstruccion_medio=result['reconstruction_error'].mean()))
            joined=pd.concat([frame[['month','source','source_kind']].reset_index(drop=True),result],axis=1)
            monthly=joined.groupby('month')[labels].mean();monthly['particion']=split
            monthly['titulares_totales']=joined.groupby('month').size();monthly['titulares_representados']=joined.groupby('month')['represented'].sum()
            all_months.append(monthly)
            by_source=joined.groupby(['source_kind','source'])[labels+['represented','entropy','reconstruction_error']].mean()
            table(by_source,'titulares_topicos_por_fuente_'+split)
        table(pd.DataFrame(summary).set_index('particion'),'titulares_topicos_resumen')
        timeline=pd.concat(all_months).sort_index();table(timeline,'titulares_topicos_evolucion_mensual')
        complete=pd.period_range('2000-01','2021-12',freq='M').astype(str)
        timeline=timeline.reindex(complete)
        dates=pd.to_datetime(timeline.index+'-01')
        fig,ax=plt.subplots(figsize=(13,6))
        colors=plt.get_cmap('tab10').colors[:8]
        ax.stackplot(dates,*[timeline[t].to_numpy() for t in labels],colors=colors,
            labels=[self.labels[i]+': '+', '.join(self.terms[i][:2]) for i in range(CONFIG['n_topics'])])
        ax.axvline(pd.Timestamp('2018-01-01'),color='black',ls='--',lw=1)
        ax.set(xlabel='Disponibilidad supuesta (mes)',ylabel='Contribución media relativa',ylim=(0,1),title='Evolución de patrones léxicos; vocabulario y NMF congelados después de train')
        ax.set_xlim(pd.Timestamp('2000-01-01'),pd.Timestamp('2022-01-01'))
        ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
        figure(fig,'titulares_topicos_evolucion')
        validation=pd.concat([self.validation[['source','source_kind']].reset_index(drop=True),self.weights['validation']],axis=1)
        means=validation.groupby('source')[labels].mean()
        fig,ax=plt.subplots(figsize=(11,5));im=ax.imshow(means,aspect='auto',vmin=0,vmax=1,cmap='Blues')
        ax.set_yticks(range(len(means)),means.index);ax.set_xticks(range(8),labels);ax.set_title('Validación: proyección por fuente, sin reajustar tópicos')
        fig.colorbar(im,ax=ax,label='Contribución media relativa');figure(fig,'titulares_topicos_validacion_fuente')
        display(Markdown('Los espacios sin cobertura mensual corresponden a registros no recuperados. Los pesos expresan contribuciones relativas de NMF. Las medias se calculan sobre documentos representados y se acompañan de su cobertura. Las variaciones reflejan conjuntamente contenido, periodo, fuente y características formales del titular.'))

    def drift(self):
        known={t for t in self.features if ' ' not in t};unigrams=sorted(known)
        distributions={};rows=[]
        for split,frame in [('train',self.train),('validation',self.validation)]:
            counter,_=self.counters[split]
            outside=sum(n for w,n in counter.items() if w not in known);total=sum(counter.values())
            vector=np.array([counter[w] for w in unigrams]+[outside],dtype=float);distributions[split]=vector/vector.sum()
            rows.append(dict(particion=split,terminos=total,terminos_fuera_vocabulario=outside,fraccion_fuera_vocabulario=outside/total))
        lexical_js=float(jensenshannon(distributions['train'],distributions['validation'],base=2)**2)
        table(pd.DataFrame(rows).set_index('particion'),'titulares_cobertura_vocabulario')
        compare=[]
        for split,frame in [('train',self.train),('validation',self.validation)]:
            for source,group in frame.groupby('source'):
                counter=collections.Counter(w for t in group['title_raw'] for w in tokenize(t));n=sum(counter.values())
                compare.append(dict(particion=split,fuente=source,titulares=len(group),terminos=n,
                    fraccion_fuera_vocabulario=sum(v for w,v in counter.items() if w not in known)/n if n else np.nan))
        by_source=pd.DataFrame(compare);table(by_source.set_index(['particion','fuente']),'titulares_vocabulario_por_fuente')
        fig,ax=plt.subplots(figsize=(11,5.5))
        for split,group in by_source.groupby('particion',sort=False):
            ax.barh(group['fuente']+' ('+split+')',group['fraccion_fuera_vocabulario'],label=split,alpha=.8)
        ax.set(xlabel='Fracción de términos de contenido fuera del vocabulario',title='Cambio léxico frente al vocabulario aprendido en train')
        figure(fig,'titulares_cobertura_vocabulario_fuente')
        audit=dict(self.fit_audit,lexical_JS_divergence_bits=lexical_js,transform_convergence_warning_count=self.transform_warning_count,
            frames={k:len(v) for k,v in [('train',self.train),('validation',self.validation)]},
            topic_assignments_are_EDA_only=True,manual_topic_names=False,numeric_or_price_data_read=False)
        (OUT/'analysis_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
        display(Markdown(f'La divergencia Jensen–Shannon entre las frecuencias léxicas de train y validación, en el vocabulario fijo y una casilla externa, es **{lexical_js:.4f} bits**. Se interpreta como una medida descriptiva con valores entre 0 y 1. La categoría externa agrupa términos nuevos y términos excluidos por las reglas de frecuencia.'))
        decision('Conservar calidad, repetición y términos no representados; si se usa texto en una fase posterior, ajustar su vocabulario y agrupamiento sólo con train.',
            'La representación por tópicos permite examinar la composición documental y su variación entre fuentes y periodos.',
            'Proyectar validación con vocabulario, IDF y componentes estimados en entrenamiento; mantener fijo el número de componentes del protocolo.',
            'El predominio editorial de una fuente y la incertidumbre sobre las versiones históricas condicionan la interpretación y transferencia de los componentes.')


    def development_analysis(self):
        """Descripción conjunta de todos los textos de desarrollo y de su representación congelada."""
        frame = pd.concat([self.train,self.validation],ignore_index=True).sort_values(['available','id']).reset_index(drop=True)
        assert frame.id.is_unique
        assert frame.available.max() < pd.Timestamp('2022-01-01T00:00:00-05:00')
        counter = self.counters['train'][0]+self.counters['validation'][0]
        docs = self.counters['train'][1]+self.counters['validation'][1]
        lengths = frame.title_raw.str.split().str.len()
        summary = pd.DataFrame([dict(periodo='2000–2021',titulares=len(frame),
            primera_disponibilidad=str(frame.available.min()),ultima_disponibilidad=str(frame.available.max()),
            fuentes=frame.source.nunique(),mediana_palabras=float(lengths.median()),
            vocablos_distintos=len(counter),terminos_contenido=sum(counter.values()),
            fraccion_titular_normalizado_repetido=float(frame.title_raw.map(normalized).duplicated().mean()))])
        table(summary,'titulares_desarrollo_resumen')
        yearly = frame.groupby(['year','source_kind','source']).size().rename('titulares').to_frame()
        table(yearly,'titulares_desarrollo_anio_fuente')
        frequent = pd.DataFrame([dict(termino=w,titulares=n,porcentaje=100*n/len(frame)) for w,n in docs.most_common(30)])
        table(frequent,'titulares_desarrollo_frecuencias')
        fig,ax = plt.subplots(figsize=(11,7))
        frequent.head(25).iloc[::-1].plot.barh(x='termino',y='porcentaje',ax=ax,legend=False)
        ax.set(xlabel='Porcentaje de titulares de desarrollo 2000–2021',ylabel='',title='Frecuencias léxicas: corpus completo de desarrollo')
        figure(fig,'titulares_desarrollo_frecuencias')
        bigrams = collections.Counter()
        for title in frame.title_raw:
            words = tokenize(title)
            bigrams.update(set(zip(words[:-1],words[1:])))
        table(pd.DataFrame([dict(bigrama=' '.join(w),titulares=n) for w,n in bigrams.most_common(30)]),
            'titulares_desarrollo_bigramas')
        # Se utilizan las proyecciones ya calculadas: no se reajusta TF-IDF o NMF con validación.
        projected = pd.concat([pd.concat([f[['id','available','source','source_kind']].reset_index(drop=True),self.weights[s]],axis=1)
            for s,f in [('train',self.train),('validation',self.validation)]],ignore_index=True)
        assert len(projected)==len(frame) and projected.id.is_unique
        labels = list(self.labels.values())
        table(projected.groupby(['source_kind','source'])[labels+['represented','entropy','reconstruction_error']].mean(),
            'titulares_desarrollo_topicos_por_fuente')
        counts = []
        audits = json.loads((ROOT/'results/variant_search/fold_audit.json').read_text(encoding='utf-8'))
        for item in [a for a in audits if a['lookback']==168]:
            cutoff = pd.Timestamp(item['validation_start'])
            end = pd.Timestamp(item['validation_last_origin'])+pd.Timedelta(hours=24)
            for role,mask in [('historia_entrenamiento',projected.available<cutoff),
                              ('bloque_validacion',(projected.available>=cutoff)&(projected.available<end))]:
                selected = projected.loc[mask]
                counts.append(dict(fold=item['fold'],tramo=role,titulares=len(selected),
                    desde=str(selected.available.min()),hasta=str(selected.available.max()),
                    fraccion_representada=float(selected.represented.mean())))
        table(pd.DataFrame(counts).set_index(['fold','tramo']),'titulares_cobertura_folds')
        (OUT/'development_audit.json').write_text(json.dumps(dict(period_start='2000-01-01T00:00:00-05:00',
            period_end_exclusive='2022-01-01T00:00:00-05:00',documents=len(frame),
            max_available=str(frame.available.max()),test_documents_read=0,
            vocabulary_refit_with_validation=False,topic_fit_end_exclusive='2018-01-01T00:00:00-05:00',
            full_development_projected=True,E1_features_added=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
