"""Pipeline numérico con forward chaining y preprocesamiento independiente por fold."""
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from .data import ROOT,TARGET,load_numeric
from .model_policy import assert_e1_features,WEATHER_PREFIXES
from .forward_chaining import split_train_val_forwardChaining

PIPELINE_DEFAULTS={
    'method':'split_train_val_forwardChaining','n_splits':5,
    'development_start':'2000-01-01T00:00:00-05:00',
    'validation_start':'2018-01-01T00:00:00-05:00',
    'development_end_exclusive':'2022-01-01T00:00:00-05:00',
    'test_start':'2022-01-01T00:00:00-05:00',
    'test_end_exclusive':'2026-01-01T00:00:00-05:00',
    'lookback_hours':168,'horizon_hours':24,'stride_hours':24,
    'hourly_release_lag_hours':24,'hydrology_release_lag_days':2,
    'include_calendar':True,'seed':11037,
    'availability_scenario':'retrospective_assumed_release_lags'
}

def pipeline_config(overrides=None):
    config=dict(PIPELINE_DEFAULTS)
    if overrides:
        unknown=set(overrides)-set(config)
        if unknown:raise ValueError('Opciones desconocidas: '+str(sorted(unknown)))
        config.update(overrides)
    for field in ['n_splits','lookback_hours','horizon_hours','stride_hours']:
        if not isinstance(config[field],int) or isinstance(config[field],bool) or config[field]<1:
            raise ValueError('Se requiere un entero positivo: '+field)
    for field in ['hourly_release_lag_hours','hydrology_release_lag_days']:
        if not isinstance(config[field],int) or isinstance(config[field],bool) or config[field]<0:
            raise ValueError('Rezago inválido: '+field)
    if config['hydrology_release_lag_days']<1:raise ValueError('La hidrología diaria requiere al menos el cierre del día.')
    for field in ['development_start','validation_start','development_end_exclusive','test_start','test_end_exclusive']:
        if pd.Timestamp(config[field]).tzinfo is None:raise ValueError('Se requiere zona horaria: '+field)
    if config['method']!='split_train_val_forwardChaining':raise ValueError('Método no autorizado')
    if pd.Timestamp(config['test_start'])!=pd.Timestamp(PIPELINE_DEFAULTS['test_start']) or config['test_end_exclusive']!=PIPELINE_DEFAULTS['test_end_exclusive']:
        raise ValueError('El periodo de prueba está congelado.')
    if not pd.Timestamp(config['development_start'])<pd.Timestamp(config['validation_start'])<pd.Timestamp(config['development_end_exclusive'])<=pd.Timestamp(config['test_start']):
        raise ValueError('Cortes temporales inválidos')
    if config['stride_hours']%24:raise ValueError('Los orígenes deben conservar el paso diario.')
    return config

def load_pipeline_config(path=None):
    path=ROOT/'configs/training_pipeline.json' if path is None else path
    return pipeline_config(json.loads(path.read_text(encoding='utf-8')))

def load_development_data(table='hourly'):
    # Only the already exposed development years are read; test remains inaccessible.
    return pd.concat([load_numeric('train',table=table),load_numeric('validation',table=table)]).sort_index()

def validate_development_index(index,config):
    index=pd.DatetimeIndex(index)
    if index.tz is None:raise ValueError('El índice debe tener zona horaria.')
    index=index.tz_convert('America/Bogota')
    if len(index)<2 or not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError('Índice temporal desordenado, duplicado o insuficiente.')
    if not np.all(np.diff(index.as_unit('ns').asi8)==pd.Timedelta(hours=1).value):
        raise ValueError('El calendario horario contiene huecos.')
    if index[0]<pd.Timestamp(config['development_start']) or index[-1]>=pd.Timestamp(config['development_end_exclusive']):
        raise PermissionError('La preparación sólo admite el periodo de desarrollo.')
    return index

def numeric_feature_frame(hourly,hydrology,config):
    index=validate_development_index(hourly.index,config)
    if not hydrology.index.is_monotonic_increasing or hydrology.index.has_duplicates:
        raise ValueError('Índice hidrológico no válido.')
    if hydrology.index.tz is None or (len(hydrology) and hydrology.index[-1]>=pd.Timestamp(config['development_end_exclusive'])):
        raise PermissionError('Hidrología fuera del periodo de desarrollo o sin zona horaria.')
    columns=[TARGET,'demanda_real_kwh','demanda_comercial_kwh']
    columns+=sorted(c for c in hourly.columns if c.startswith(WEATHER_PREFIXES))
    features=hourly[columns].shift(config['hourly_release_lag_hours']).copy()
    hydro_columns=['llenado_valor_original','reserva_util_kwh','capacidad_util_kwh','aportes_kwh_dia']
    released=hydrology[hydro_columns].copy()
    released.index=released.index+pd.Timedelta(days=config['hydrology_release_lag_days'])
    features=features.join(released.reindex(index,method='ffill'))
    if config['include_calendar']:
        phases={'hour':index.hour/24,'week':(index.day_of_week+index.hour/24)/7,
            'year':(index.day_of_year-1+index.hour/24)/np.where(index.is_leap_year,366,365)}
        for name,phase in phases.items():
            features[name+'_sin']=np.sin(2*np.pi*phase)
            features[name+'_cos']=np.cos(2*np.pi*phase)
    assert_e1_features(features.columns)
    return features

def forward_chaining_folds(index,config,input_usable=None,target_usable=None):
    """Plan temporal por bloques; ventanas supervisadas completas y sin etiquetas compartidas."""
    index=validate_development_index(index,config)
    length=len(index);lookback=config['lookback_hours'];horizon=config['horizon_hours']
    origins=np.arange(lookback,length-horizon+1,config['stride_hours'],dtype=np.int64)
    origins=origins[index[origins].hour==0]
    if input_usable is not None:
        flags=np.asarray(input_usable,dtype=bool)
        if flags.shape!=(length,):raise ValueError('Máscara de entradas incompatible')
        bad=np.r_[0,np.cumsum(~flags)]
        origins=origins[bad[origins]-bad[origins-lookback]==0]
    if target_usable is not None:
        flags=np.asarray(target_usable,dtype=bool)
        if flags.shape!=(length,):raise ValueError('Máscara de etiquetas incompatible')
        bad=np.r_[0,np.cumsum(~flags)]
        origins=origins[bad[origins+horizon]-bad[origins]==0]
    initial=origins[index[origins]<pd.Timestamp(config['validation_start'])]
    eligible=origins[index[origins]>=pd.Timestamp(config['validation_start'])]
    if len(initial)<3 or len(eligible)<config['n_splits']:raise ValueError('Datos insuficientes para los folds.')
    validation_blocks=np.array_split(eligible,config['n_splits'])
    # The original library function operates on a small calendar-block schedule.
    # Its output is then mapped to all supervised origins, avoiding quadratic window allocation.
    train_x,train_y,val_x,val_y=split_train_val_forwardChaining(np.arange(config['n_splits']+3),1,1,1)
    if len(val_y)!=config['n_splits']:raise AssertionError('Número inesperado de folds del backend')
    folds=[]
    for key in sorted(val_y):
        block=int(val_y[key].ravel()[0]);block_id=block-3
        past_blocks=np.unique(np.r_[train_x[key].ravel(),train_y[key].ravel()])
        if past_blocks.max()>=block:raise AssertionError('El backend incluyó bloques futuros')
        start=int(validation_blocks[block_id][0])
        stop=int(validation_blocks[block_id+1][0]) if block_id+1<len(validation_blocks) else length
        train=origins[(origins+horizon)<=start]
        validation=validation_blocks[block_id]
        validation=validation[validation+horizon<=stop]
        if not len(train) or not len(validation):raise ValueError('Fold vacío tras la purga de etiquetas')
        assert train[-1]+horizon<=validation[0]
        digest=hashlib.sha256(train.astype('<i8').tobytes()+validation.astype('<i8').tobytes()).hexdigest()
        folds.append(dict(fold=len(folds)+1,train_origins=train,validation_origins=validation,
            validation_block=block,indices_sha256=digest))
    return folds

def build_training_pipeline(config=None,hourly=None,hydrology=None):
    config=pipeline_config(config)
    hourly=load_development_data() if hourly is None else hourly
    hydrology=load_development_data('hydrology') if hydrology is None else hydrology
    features=numeric_feature_frame(hourly,hydrology,config)
    target=hourly[TARGET].copy()
    usable=np.isfinite(features.to_numpy()).all(axis=1)
    folds=forward_chaining_folds(features.index,config,usable,np.isfinite(target.to_numpy()))
    return dict(config=config,features=features,target=target,folds=folds)

def pipeline_fold_summary(pipeline):
    rows=[];index=pipeline['features'].index;horizon=pipeline['config']['horizon_hours']
    for fold in pipeline['folds']:
        train=fold['train_origins'];validation=fold['validation_origins']
        rows.append(dict(fold=fold['fold'],train_start=index[train[0]],
            train_end_exclusive=index[train[-1]]+pd.Timedelta(hours=horizon),
            validation_start=index[validation[0]],
            validation_end_exclusive=index[validation[-1]]+pd.Timedelta(hours=horizon),
            train_windows=len(train),validation_windows=len(validation),
            indices_sha256=fold['indices_sha256']))
    return pd.DataFrame(rows).set_index('fold')

def prepare_fold_arrays(pipeline,fold):
    features=pipeline['features'];target=pipeline['target'].to_numpy();config=pipeline['config']
    lookback=config['lookback_hours'];horizon=config['horizon_hours']
    train=fold['train_origins'];validation=fold['validation_origins']
    train_positions=train[:,None]-lookback+np.arange(lookback)
    validation_positions=validation[:,None]-lookback+np.arange(lookback)
    train_rows=np.unique(train_positions);validation_rows=np.unique(validation_positions)
    scaler=StandardScaler().fit(features.iloc[train_rows])
    scaled_train=scaler.transform(features.iloc[train_rows]).astype(np.float32)
    scaled_validation=scaler.transform(features.iloc[validation_rows]).astype(np.float32)
    X_train=scaled_train[np.searchsorted(train_rows,train_positions)]
    X_validation=scaled_validation[np.searchsorted(validation_rows,validation_positions)]
    y_train=target[train[:,None]+np.arange(horizon)].astype(np.float32)
    y_validation=target[validation[:,None]+np.arange(horizon)].astype(np.float32)
    assert features.index[train_rows[-1]]<features.index[validation[0]]
    return dict(fold=fold['fold'],X_train=X_train,y_train=y_train,
        X_validation=X_validation,y_validation=y_validation,feature_scaler=scaler,
        feature_names=list(features.columns),train_origins=features.index[train],
        validation_origins=features.index[validation],scaler_fit_rows=len(train_rows),
        scaler_fit_start=features.index[train_rows[0]],scaler_fit_end=features.index[train_rows[-1]],
        target_units='COP/kWh')

def run_forward_chaining(pipeline,model_factory,fit_model,evaluate_model,seeds=(11037,)):
    """Extensión para modelos futuros: una instancia nueva por fold y semilla."""
    if not seeds:raise ValueError('Se requiere al menos una semilla.')
    rows=[]
    for fold in pipeline['folds']:
        batch=prepare_fold_arrays(pipeline,fold)
        for seed in seeds:
            model=model_factory(seed=seed,n_features=len(batch['feature_names']),horizon=pipeline['config']['horizon_hours'])
            fitted=fit_model(model,batch,seed=seed)
            scores=evaluate_model(model if fitted is None else fitted,batch)
            rows.append(dict(fold=fold['fold'],seed=seed,**scores))
        del batch
    return pd.DataFrame(rows)
