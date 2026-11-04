"""Lectura reproducible; el EDA no puede cargar valores de prueba."""
from functools import lru_cache
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SPLITS={'train':(2000,2017),'validation':(2018,2021),'test':(2022,2025)}
TIME='timestamp_start_colombia'
TARGET='precio_bolsa_cop_kwh'

def load_numeric(split='train',table='hourly',*,allow_test=False):
    if split not in SPLITS:raise ValueError('Unknown split')
    if split=='test' and not allow_test:raise PermissionError('El EDA no puede consultar valores de prueba.')
    a,b=SPLITS[split]
    folder='hourly' if table=='hourly' else 'hydrology'
    frame=pd.concat([pd.read_csv(ROOT/f'data/numeric/{folder}/{year}.csv.gz') for year in range(a,b+1)],ignore_index=True)
    if table=='hourly':frame.index=pd.DatetimeIndex(pd.to_datetime(frame[TIME],utc=True)).tz_convert('America/Bogota')
    else:frame.index=pd.DatetimeIndex(pd.to_datetime(frame['date'])).tz_localize('America/Bogota')
    frame.index.name='tiempo_colombia'
    return frame

def load_text(split='train',kind=None):
    if split=='test':raise PermissionError('El EDA no explora el contenido de prueba.')
    a,b=SPLITS[split];parts=[]
    for sub in ([kind] if kind else ['press','official']):
        for path in sorted((ROOT/f'data/text/{sub}').glob('*/*.csv.gz')):
            if path.name[:4].isdigit() and a<=int(path.name[:4])<=b:
                parts.append(pd.read_csv(path,keep_default_na=False))
    return pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()

def metadata(name):return json.loads((ROOT/'data/metadata'/name).read_text(encoding='utf-8'))

def split_for_labels(start,end_exclusive):
    start=pd.Timestamp(start);end=pd.Timestamp(end_exclusive)
    if start.tzinfo is None or end.tzinfo is None:raise ValueError('Se requiere zona horaria.')
    for name,(a,b) in SPLITS.items():
        left=pd.Timestamp(f'{a}-01-01',tz='America/Bogota');right=pd.Timestamp(f'{b+1}-01-01',tz='America/Bogota')
        if left<=start<end<=right:return name
    return 'purged'
