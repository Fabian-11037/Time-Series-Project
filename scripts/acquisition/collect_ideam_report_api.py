"""Títulos oficiales, sin temas ni supuesta disponibilidad histórica."""
import concurrent.futures
import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
from extend_news_2020_2025 import ROOT,save,now

OUT=ROOT/'official_reports'
RAW=OUT/'ideam_public_api_raw'
PARAMS={'page[limit]':50,'sort':'field_fecha_publicacion,id',
 'filter[min][condition][path]':'field_fecha_publicacion','filter[min][condition][operator]':'>=',
 'filter[min][condition][value]':'2020-01-01','filter[max][condition][path]':'field_fecha_publicacion',
 'filter[max][condition][operator]':'<=','filter[max][condition][value]':'2025-12-31',
 'include':'field_archivo','fields[node--boletines]':'title,created,changed,path,field_fecha_publicacion,field_fecha_generacion,field_archivo',
 'fields[file--file]':'filename,uri,created,changed,drupal_internal__fid'}

def fetch(offset):
    params=dict(PARAMS,**{'page[offset]':offset})
    url='https://www.ideam.gov.co/jsonapi/node/boletines?'+urllib.parse.urlencode(params)
    key=hashlib.sha256(url.encode()).hexdigest()[:24];path=RAW/(key+'.json.gz');mp=RAW/(key+'.meta.json')
    if path.exists() and mp.exists():
        meta=json.loads(mp.read_text(encoding='utf-8'));raw=gzip.decompress(path.read_bytes())
        if meta.get('status')=='ok' and hashlib.sha256(raw).hexdigest()==meta['sha256']:return json.loads(raw),meta
    errors=[]
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Academic-public-report-title-inventory/1.0'}),timeout=75) as response:raw=response.read()
            data=json.loads(raw)
            if not isinstance(data.get('data'),list):raise ValueError('Not a public JSONAPI collection')
            path.write_bytes(gzip.compress(raw,mtime=0))
            meta=dict(status='ok',url=url,offset=offset,retrieved_at=now(),sha256=hashlib.sha256(raw).hexdigest(),raw_file=path.relative_to(ROOT).as_posix())
            save(mp,meta);return data,meta
        except Exception as exc:
            errors.append(repr(exc))
            if getattr(exc,'code',None) in {401,403,404}:break
            time.sleep(3)
    save(mp,dict(status='error',url=url,offset=offset,errors=errors,retrieved_at=now()))
    raise RuntimeError(str(errors))

def rows_from(data,meta):
    files={r['id']:r['attributes'] for r in data.get('included',[]) if r['type']=='file--file'}
    for node in data['data']:
        a=node['attributes'];attachments=[]
        for relationship in node.get('relationships',{}).get('field_archivo',{}).get('data',[]):
            file=files.get(relationship['id'],{})
            fid=file.get('drupal_internal__fid') or relationship.get('meta',{}).get('drupal_internal__target_id')
            attachments.append(dict(id=relationship['id'],file_id=fid,filename=file.get('filename'),
                url=urllib.parse.urljoin('https://www.ideam.gov.co',file.get('uri',{}).get('url','')),
                created_at_claimed=file.get('created'),modified_at_claimed=file.get('changed')))
        yield dict(id=hashlib.sha256(('IDEAM\n'+node['id']).encode()).hexdigest(),official_node_id=node['id'],source='IDEAM',
            title_raw=a['title'],url=urllib.parse.urljoin('https://www.ideam.gov.co',a.get('path',{}).get('alias','')),
            publication_date_claimed=a.get('field_fecha_publicacion'),published_at_claimed=None,
            generation_date_claimed=a.get('field_fecha_generacion'),created_at_claimed=a.get('created'),
            modified_at_claimed=a.get('changed'),date_precision='declared_date_only',
            attachments=attachments,document_kind='report_entry',title_kind='official_node_title',
            catalog_url=meta['url'],raw_file=meta['raw_file'],retrieved_at=meta['retrieved_at'],
            available_at_verified=None,availability_status='historical_version_unverified',historical_version_verified=False)

def main():
    RAW.mkdir(parents=True,exist_ok=True);records={};errors=[];pages=[];offset=0;done=False
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        while not done:
            offsets=list(range(offset,offset+300,50))
            futures={pool.submit(fetch,n):n for n in offsets}
            for future in concurrent.futures.as_completed(futures):
                n=futures[future]
                try:data,meta=future.result()
                except Exception as exc:errors.append(dict(offset=n,error=repr(exc)));continue
                pages.append(dict(offset=n,count=len(data['data']),raw_file=meta['raw_file']))
                for row in rows_from(data,meta):records[row['id']]=row
                if len(data['data'])<50:done=True
            offset+=300
            rows=sorted(records.values(),key=lambda r:(r['publication_date_claimed'] or '',r['id']))
            (OUT/'ideam_report_node_titles.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
            save(OUT/'ideam_api_progress.json',dict(records=len(rows),next_offset=offset,errors=errors,done=done,pages=pages,updated_at=now()))
            print(json.dumps(dict(records=len(rows),offset=offset,errors=len(errors),done=done)),flush=True)
    save(OUT/'ideam_api_summary.json',dict(finished_at=now(),records=len(records),pages=sorted(pages,key=lambda p:p['offset']),errors=errors,
        complete_public_query=not errors,editorial_census_certified=False,historical_availability_verified=False,
        note='Public current node collection filtered by explicit publication date 2020–2025; no topic labels requested or exported. Current versions are not historical version proof.'))

if __name__=='__main__':main()
