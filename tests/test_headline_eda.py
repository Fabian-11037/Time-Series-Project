import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from colombia_energy.headline_eda import HeadlineStudy,training_sample,contributions,tokenize
from colombia_energy.model_policy import assert_e1_features

def document(key,stamp,title='energía mercado precio nacional cambia'):
    return dict(id=key,source='El Colombiano',source_kind='news',title_kind='explicit_headline',title_raw=title,
        url='https://example.test/'+key,available_at_assumed=stamp,quarantined=0)

class HeadlineEDA(unittest.TestCase):
    def test_fit_rejects_future_or_unknown_dates(self):
        for stamp in ['2018-01-01T00:00:00-05:00',None]:
            frame=pd.DataFrame([dict(document('a','2017-01-01T00:00:00-05:00'),available=stamp,year=2017)])
            with self.assertRaises(ValueError):training_sample(frame)

    def test_partition_uses_availability_and_never_loads_test(self):
        train=pd.DataFrame([document('past','2017-12-31T12:00:00-05:00'),document('carry','2018-01-01T00:00:00-05:00')])
        valid=pd.DataFrame([document('valid','2020-01-02T00:00:00-05:00','xilófono prospectivo futuro desconocido informe'),
            document('future','2022-01-01T00:00:00-05:00')])
        def loader(split):
            if split=='test':raise AssertionError('Test must stay closed')
            return train if split=='train' else valid
        with patch('colombia_energy.headline_eda.load_text',side_effect=loader) as mocked:
            study=HeadlineStudy()
        self.assertEqual(set(study.fit['id']),{'past'})
        self.assertEqual(set(study.validation['id']),{'carry','valid'})
        self.assertEqual([call.args[0] for call in mocked.call_args_list],['train','validation'])

    def test_component_scale_does_not_change_contributions(self):
        w=np.array([[1.,2.],[0.,0.]])
        h=np.array([[2.,1.,0.],[0.,1.,3.]])
        scale=np.array([4.,.25])
        np.testing.assert_allclose(contributions(w,h),contributions(w/scale,h*scale[:,None]))
        self.assertTrue(np.all(contributions(w,h)[1]==0))

    def test_unknown_text_is_not_forced_to_topic_zero(self):
        study=HeadlineStudy.__new__(HeadlineStudy)
        study.vectorizer=TfidfVectorizer(tokenizer=tokenize,token_pattern=None)
        x=study.vectorizer.fit_transform(['energía mercado precio nacional','gas demanda planta eléctrica',
            'fútbol equipo estadio victoria','deporte partido torneo cancha'])
        study.model=NMF(n_components=2,init='nndsvda',random_state=1,max_iter=250).fit(x)
        study.labels={0:'T01',1:'T02'};study.transform_warning_count=0
        result=study.transform(pd.DataFrame({'title_raw':['zzzxqvv zzzxqvv']}))
        self.assertFalse(result.loc[0,'represented'])
        self.assertTrue(result[['T01','T02']].isna().all().all())

    def test_topic_outputs_are_not_e1_numeric_features(self):
        for feature in ['T01','topic_01','fraccion_fuera_vocabulario','titulares_numero']:
            with self.assertRaises(ValueError):assert_e1_features([feature])

if __name__=='__main__':unittest.main()
