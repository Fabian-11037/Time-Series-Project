import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from colombia_energy.pipeline import pipeline_config,build_training_pipeline,prepare_fold_arrays,run_forward_chaining
from colombia_energy.data import TARGET

def sample_data():
    index=pd.date_range('2010-01-01',periods=60*24,freq='h',tz='America/Bogota')
    rows=np.arange(len(index),dtype=float)
    hourly=pd.DataFrame({TARGET:100+rows/10,'demanda_real_kwh':1000+rows,
        'demanda_comercial_kwh':900+rows,'temperature_2m_c_bogota':18+np.sin(rows)},index=index)
    days=pd.date_range('2010-01-01',periods=60,freq='D',tz='America/Bogota')
    hydro=pd.DataFrame({'llenado_valor_original':np.linspace(.3,.8,60),'reserva_util_kwh':np.arange(60)+100.,
        'capacidad_util_kwh':1000.,'aportes_kwh_dia':np.arange(60)+10.},index=days)
    config=pipeline_config(dict(validation_start='2010-02-01T00:00:00-05:00',lookback_hours=24,
        hourly_release_lag_hours=2,hydrology_release_lag_days=1))
    return hourly,hydro,config

class ForwardPipeline(unittest.TestCase):
    def test_expanding_folds_and_disjoint_complete_labels(self):
        h,d,c=sample_data();p=build_training_pipeline(c,h,d);previous=set()
        self.assertEqual(len(p['folds']),5)
        for fold in p['folds']:
            train=fold['train_origins'];val=fold['validation_origins']
            self.assertLessEqual(train[-1]+c['horizon_hours'],val[0])
            self.assertTrue(previous.issubset(set(train)));previous=set(train)
            train_labels=set((train[:,None]+np.arange(c['horizon_hours'])).ravel())
            val_labels=set((val[:,None]+np.arange(c['horizon_hours'])).ravel())
            self.assertFalse(train_labels&val_labels)
        repeats=build_training_pipeline(c,h,d)
        self.assertEqual([f['indices_sha256'] for f in p['folds']],[f['indices_sha256'] for f in repeats['folds']])

    def test_validation_changes_cannot_modify_training_or_scaler(self):
        h,d,c=sample_data();p=build_training_pipeline(c,h,d);fold=p['folds'][0]
        first=prepare_fold_arrays(p,fold)
        changed=h.copy();changed.loc[changed.index>=first['validation_origins'][0],:]+=1e8
        other=build_training_pipeline(c,changed,d);second=prepare_fold_arrays(other,other['folds'][0])
        np.testing.assert_allclose(first['X_train'],second['X_train'])
        np.testing.assert_allclose(first['y_train'],second['y_train'])
        np.testing.assert_allclose(first['feature_scaler'].mean_,second['feature_scaler'].mean_)
        self.assertEqual(first['X_train'].shape[1:],(24,len(p['features'].columns)))
        self.assertEqual(first['y_validation'].shape[1],24)

    def test_hydrology_is_released_after_the_reference_day(self):
        h,d,c=sample_data();p=build_training_pipeline(c,h,d)
        self.assertTrue(pd.isna(p['features'].loc[h.index[0],'reserva_util_kwh']))
        self.assertEqual(p['features'].loc[h.index[24],'reserva_util_kwh'],d.iloc[0]['reserva_util_kwh'])
        self.assertEqual(p['features'].loc[h.index[23],'demanda_real_kwh'],h.iloc[21]['demanda_real_kwh'])

    def test_test_period_and_invalid_calendars_are_rejected(self):
        h,d,c=sample_data()
        with self.assertRaises(ValueError):pipeline_config(dict(test_start='2023-01-01T00:00:00-05:00'))
        with self.assertRaises(ValueError):build_training_pipeline(c,h.drop(h.index[100]),d)
        with self.assertRaises(ValueError):build_training_pipeline(c,pd.concat([h.iloc[:1],h]),d)
        with self.assertRaises(ValueError):pipeline_config(dict(hydrology_release_lag_days=0))
        future=h.copy();future.index=future.index+pd.DateOffset(years=12)
        with self.assertRaises(PermissionError):build_training_pipeline(c,future,d)

    def test_loader_never_requests_test(self):
        h,d,c=sample_data();calls=[]
        def loader(split,table='hourly'):
            calls.append((split,table))
            if split=='test':raise AssertionError('Test read')
            frame=h if table=='hourly' else d
            middle=len(frame)//2
            return frame.iloc[:middle] if split=='train' else frame.iloc[middle:]
        with patch('colombia_energy.pipeline.load_numeric',side_effect=loader):build_training_pipeline(c)
        self.assertEqual(calls,[('train','hourly'),('validation','hourly'),('train','hydrology'),('validation','hydrology')])

    def test_new_model_and_preprocessor_per_fold_and_seed(self):
        h,d,c=sample_data();p=build_training_pipeline(c,h,d);models=[];scalers=[]
        def factory(**kwargs):
            model=dict(kwargs);models.append(model);return model
        def fit(model,batch,seed):
            model['fold']=batch['fold'];scalers.append(batch['feature_scaler']);return model
        def evaluate(model,batch):
            self.assertEqual(model['fold'],batch['fold']);return {'example_metric':float(batch['y_train'].mean())}
        scores=run_forward_chaining(p,factory,fit,evaluate,seeds=(1,2))
        self.assertEqual(len(scores),10);self.assertEqual(len({id(m) for m in models}),10)
        self.assertEqual(len({id(s) for s in scalers}),5)

    def test_horizons_longer_than_the_daily_step_are_purged(self):
        h,d,c=sample_data();c.update(horizon_hours=48);p=build_training_pipeline(c,h,d)
        for left,right in zip(p['folds'],p['folds'][1:]):
            self.assertLessEqual(left['validation_origins'][-1]+48,right['validation_origins'][0])

    def test_text_and_unknown_city_features_are_not_admitted(self):
        h,d,c=sample_data();h['temperature_2m_c_unknown_city']=0
        with self.assertRaises(ValueError):build_training_pipeline(c,h,d)

if __name__=='__main__':unittest.main()
