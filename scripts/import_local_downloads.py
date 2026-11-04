"""Importa la instantánea descargada, sin consultar resultados de modelos."""
import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import unicodedata

REPO=Path(__file__).resolve().parents[1]

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def slug(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c)).lower().replace(' ','_')

def split_csv(path,folder,partition):
    streams={};counts={}
    with path.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames
        for row in reader:
            part=partition(row)
            if part not in streams:
                target=folder/part;target.parent.mkdir(parents=True,exist_ok=True)
                raw=target.open('wb');compressed=gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='')
                text=io.TextIOWrapper(compressed,encoding='utf-8',newline='')
                writer=csv.DictWriter(text,fieldnames=fields,lineterminator='\n');writer.writeheader()
                streams[part]=(writer,text,raw);counts[part]=0
            streams[part][0].writerow(row);counts[part]+=1
    for writer,text,raw in streams.values():text.close();raw.close()
    return counts

def main(source):
    numeric=source/'dataset_numerico_2000_2025'
    texts=source/'news_2000_2025/extension_2020_2025/selected_dataset'
    counts={}
    counts['numeric_hourly']=split_csv(numeric/'dataset_horario_xm_clima_2000_2025.csv',REPO/'data/numeric/hourly',lambda r:r['date'][:4]+'.csv.gz')
    counts['hydrology_daily']=split_csv(numeric/'hidrologia_diaria_xm_2000_2025.csv',REPO/'data/numeric/hydrology',lambda r:r['date'][:4]+'.csv.gz')
    for name,kind in [('titulares_prensa_2000_2025.csv','press'),('titulos_informes_ideam_xm.csv','official')]:
        counts[kind]=split_csv(texts/name,REPO/('data/text/'+kind),lambda r:slug(r['source'])+'/'+(r['publication_date_claimed'][:4] if r['publication_date_claimed'] else 'undated')+'.csv.gz')
    metadata=REPO/'data/metadata';metadata.mkdir(parents=True,exist_ok=True)
    for name in ['coverage_2000_2025_by_month_source.csv','coverage_2020_2025_by_month_source.csv','coverage_summary.json',
        'archive_version_verification.json','availability_rules.json','independent_verification.json','source_provenance.json']:
        shutil.copy2(texts/name,metadata/name)
    for name in ['dataset_schema.json','verification.json','particion_cronologica_propuesta.json']:
        shutil.copy2(numeric/name,metadata/('numeric_'+name))
    shutil.copytree(numeric/'metadata',metadata/'numeric_sources',dirs_exist_ok=True)
    availability_path=metadata/'availability_rules.json'
    availability=json.loads(availability_path.read_text(encoding='utf-8'))
    availability['project_scope_override']=dict(E1_numeric_only=True,E1_text_or_text_derived_features_allowed=False,
        text_scenarios_apply_to='future contextual phases E2/E3')
    write_json(availability_path,availability)
    for name in ['asof_text.py']:
        target=REPO/'src/colombia_energy'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(texts/name,target)
    (REPO/'src/colombia_energy/__init__.py').write_text('"""EDA reproducible del candidato colombiano."""\n',encoding='utf-8')
    evidence=REPO/'data/provenance';evidence.mkdir(parents=True,exist_ok=True)
    src=texts/'verified_archive_entry_evidence.jsonl'
    with src.open('rb') as f,(evidence/'verified_archive_entries.jsonl.gz').open('wb') as target:
        with gzip.GzipFile(fileobj=target,mode='wb',mtime=0,filename='') as z:shutil.copyfileobj(f,z)
    # Publish provenance metadata, not original feeds, full articles or corpus bodies.
    metadata_rows=[]
    for p in (source/'news_2000_2025/extension_2020_2025/archived_feeds_raw').glob('*.meta.json'):
        r=json.loads(p.read_text(encoding='utf-8'))
        keys=['key','medium','requested_capture','original_url','indexed_digest','status','final_replay_url','actual_capture_at',
              'retrieved_at','sha256_response','errors']
        entry={k:r.get(k) for k in keys}
        entry['archive_payload_digest_verified_at_download']=r.get('archive_payload_digest_verified')
        body=p.with_name(r['key']+'.body.gz')
        entry['strict_export_payload_digest_reproduced']=bool(r.get('status')=='ok' and body.exists() and
            base64.b32encode(hashlib.sha1(gzip.decompress(body.read_bytes())).digest()).decode().rstrip('=')==(r.get('indexed_digest') or '').removeprefix('sha1:'))
        metadata_rows.append(entry)
    write_json(evidence/'archive_capture_metadata.json',metadata_rows)
    write_json(metadata/'import_counts.json',counts)
    shutil.copy2(source/'source_catalog.json',metadata/'source_catalog.json')
    acquisition=REPO/'scripts/acquisition';acquisition.mkdir(exist_ok=True)
    for p in source.glob('*.py'):
        if p.name.startswith(('download_','collect_','ingest_','extend_','discover_','verify_')):
            shutil.copy2(p,acquisition/p.name)
    literature=REPO/'literature';literature.mkdir(exist_ok=True)
    old=source.parents[1]/'repo/github-main/data/literature'
    for name in ['selected_83.csv','prisma_counts.json']:
        if (old/name).exists():shutil.copy2(old/name,literature/('inherited_'+name))
    manifest=[]
    for p in sorted((REPO/'data').rglob('*')):
        if not p.is_file() or p.name=='manifest.json':continue
        assert p.stat().st_size<50_000_000,str(p)
        row_count=None
        if p.name.endswith('.csv.gz'):
            with gzip.open(p,'rt',encoding='utf-8',newline='') as f:row_count=sum(1 for _ in csv.DictReader(f))
        manifest.append(dict(path=p.relative_to(REPO).as_posix(),bytes=p.stat().st_size,rows=row_count,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    write_json(REPO/'data/manifest.json',dict(snapshot='2026-11-03',timezone='America/Bogota',files=manifest,
        upstream_hourly_sha256=hashlib.sha256((numeric/'dataset_horario_xm_clima_2000_2025.csv').read_bytes()).hexdigest(),
        upstream_hydrology_sha256=hashlib.sha256((numeric/'hidrologia_diaria_xm_2000_2025.csv').read_bytes()).hexdigest()))
    print(json.dumps(dict(files=len(manifest),bytes=sum(r['bytes'] for r in manifest),rows={k:sum(v.values()) for k,v in counts.items()})))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True)
    main(parser.parse_args().source_root.resolve())
