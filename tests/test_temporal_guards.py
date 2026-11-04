import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from colombia_energy.asof_text import verify_guards,eligible,eligible_retrospective
from colombia_energy.data import load_numeric,load_text,split_for_labels
from colombia_energy.model_policy import assert_e1_features

class TemporalGuards(unittest.TestCase):
    def test_text_version_and_scenario_guards(self):verify_guards()
    def test_test_is_closed_to_eda(self):
        with self.assertRaises(PermissionError):load_numeric('test')
        with self.assertRaises(PermissionError):load_text('test')
    def test_horizon_purge_and_boundary(self):
        self.assertEqual(split_for_labels('2017-12-31T00:00:00-05:00','2018-01-01T00:00:00-05:00'),'train')
        self.assertEqual(split_for_labels('2017-12-31T01:00:00-05:00','2018-01-01T01:00:00-05:00'),'purged')
        self.assertEqual(split_for_labels('2021-12-31T12:00:00-05:00','2022-01-01T12:00:00-05:00'),'purged')
        with self.assertRaises(ValueError):split_for_labels('2017-01-01','2017-01-02')
    def test_e1_has_no_text_or_text_derived_numbers(self):
        self.assertTrue(assert_e1_features(['precio_bolsa_cop_kwh','demanda_real_kwh','temperature_2m_c_bogota','aportes_kwh_dia']))
        for feature in ['title_raw','embedding_0','news_count','sentiment','topic','available_at_assumed','metadata_json']:
            with self.assertRaises(ValueError):assert_e1_features([feature])

if __name__=='__main__':unittest.main()
