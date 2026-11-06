import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from colombia_energy.eda import used_window_rows,load_eda_development
from colombia_energy.data import SPLITS

class EDATrainingScope(unittest.TestCase):
    def test_overlapping_inputs_count_unique_rows_and_multiplicity(self):
        inputs,labels=used_window_rows([4,6],10,4,2)
        np.testing.assert_array_equal(inputs,[1,1,2,2,1,1,0,0,0,0])
        np.testing.assert_array_equal(labels,[0,0,0,0,1,1,1,1,0,0])
        self.assertEqual(int(inputs.sum()),8)
        self.assertEqual(int((inputs>0).sum()),6)

    def test_single_window_never_uses_its_own_future_labels(self):
        inputs,labels=used_window_rows([4],10,4,2)
        self.assertFalse(np.any((inputs>0)&(labels>0)))
        np.testing.assert_array_equal(np.flatnonzero(inputs),[0,1,2,3])
        np.testing.assert_array_equal(np.flatnonzero(labels),[4,5])

    def test_windows_outside_calendar_are_rejected(self):
        for origins in [[],[3],[9],[[4,6]]]:
            with self.assertRaises(ValueError):used_window_rows(origins,10,4,2)

    def test_complete_development_retains_years_after_2017(self):
        frame=pd.DataFrame({'x':[1,2,3]},index=pd.DatetimeIndex([
            '2017-01-01','2019-01-01','2021-12-31'],tz='America/Bogota'))
        original=dict(SPLITS)
        with patch('colombia_energy.pipeline.load_development_data',return_value=frame) as read:
            result=load_eda_development()
        pd.testing.assert_frame_equal(result,frame)
        read.assert_called_once_with('hourly')
        self.assertEqual(SPLITS,original)

    def test_accidental_test_source_is_rejected(self):
        frame=pd.DataFrame({'x':[1,99]},index=pd.DatetimeIndex([
            '2021-12-31','2022-01-01'],tz='America/Bogota'))
        with patch('colombia_energy.pipeline.load_development_data',return_value=frame):
            with self.assertRaises(PermissionError):load_eda_development()

if __name__=='__main__':unittest.main()
