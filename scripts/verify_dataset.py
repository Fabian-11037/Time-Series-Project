"""Verifica huellas, calendario y claves; no explora el objetivo de prueba."""
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'El Tiempo','El Espectador','Semana','Portafolio','La República','El Colombiano','Dinero','IDEAM','XM'}

def main():
    manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
    counts=collections.Counter();ids=set();numeric_hours=set();hydro_days=set()
    for entry in manifest['files']:
        p=ROOT/entry['path'];assert p.exists(),str(p)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],str(p)
        if not p.name.endswith('.csv.gz'):continue
        n=0
        with gzip.open(p,'rt',encoding='utf-8',newline='') as f:
            reader=csv.DictReader(f)
            assert not set(reader.fieldnames)&{'topic','sentiment','category','anticipatory_label','relevance_score'}
            for r in reader:
                n+=1
                if '/numeric/hourly/' in entry['path']:
                    stamp=dt.datetime.fromisoformat(r['timestamp_start_colombia'])
                    assert stamp.utcoffset()==dt.timedelta(hours=-5)
                    assert stamp not in numeric_hours;numeric_hours.add(stamp);counts['hourly']+=1
                elif '/numeric/hydrology/' in entry['path']:
                    assert r['date'] not in hydro_days;hydro_days.add(r['date']);counts['hydrology']+=1
                else:
                    assert r['source'] in ALLOWED
                    assert r['id'] not in ids;ids.add(r['id']);counts['text']+=1
                    counts['text_'+r['source']]+=1
                    if r['available_at_verified']:counts['verified_text']+=1
                    if r['available_at_assumed'] and r['quarantined']=='0':counts['expanded_dated_text']+=1
        assert n==entry['rows'],(str(p),n,entry['rows'])
    tz=dt.timezone(dt.timedelta(hours=-5));start=dt.datetime(2000,1,1,tzinfo=tz);end=dt.datetime(2026,1,1,tzinfo=tz)
    n=int((end-start).total_seconds()/3600)
    assert numeric_hours=={start+dt.timedelta(hours=i) for i in range(n)}
    assert hydro_days=={(start+dt.timedelta(days=i)).date().isoformat() for i in range((end-start).days)}
    freeze=json.loads((ROOT/'data/test_freeze.json').read_text(encoding='utf-8'))
    for entry in freeze['files']:assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
    assert counts['hourly']==227928 and counts['hydrology']==9497 and counts['text']==568701
    assert counts['verified_text']==62572 and counts['expanded_dated_text']==568294
    summary=dict(files_verified=len(manifest['files']),counts=dict(counts),duplicate_ids=0,
        hourly_calendar_complete=True,daily_calendar_complete=True,test_hashes_unchanged=True,
        test_target_distribution_read=False,no_manual_topic_columns=True)
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/dataset_verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
