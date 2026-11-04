"""Inventario público de archivos de informes; modificación != publicación."""
import collections
import concurrent.futures
import gzip
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from extend_news_2020_2025 import ROOT,save,now

OUT=ROOT/'official_reports'
RAW=OUT/'xm_public_inventory_raw'
BASE='https://sinergox.xm.com.co/historicos/api/blob/informes/'

def fetch(folder):
    url=BASE+'list?'+urllib.parse.urlencode({'carpeta':folder})
    key=hashlib.sha256(url.encode()).hexdigest()[:24]
    path=RAW/(key+'.json.gz');mp=RAW/(key+'.meta.json')
    if path.exists() and mp.exists():
        meta=json.loads(mp.read_text(encoding='utf-8'))
        raw=gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest()==meta['sha256']:
            return folder,json.loads(raw),meta
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Academic-public-report-inventory/1.0'}),timeout=60) as response:
                raw=response.read()
            break
        except Exception as exc:
            if getattr(exc,'code',None) in {401,403,404} or attempt==2:raise
            time.sleep(2+attempt)
    data=json.loads(raw)
    path.write_bytes(gzip.compress(raw,mtime=0))
    meta=dict(url=url,folder=folder,retrieved_at=now(),sha256=hashlib.sha256(raw).hexdigest(),raw_file=path.relative_to(ROOT).as_posix())
    save(mp,meta)
    return folder,data,meta

def main():
    RAW.mkdir(parents=True,exist_ok=True)
    pending=[''];seen=set();rows={};errors=[];inventories=0
    while pending:
        batch=[f for f in pending if f not in seen];pending=[];seen.update(batch)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures={pool.submit(fetch,f):f for f in batch}
            for future in concurrent.futures.as_completed(futures):
                try:folder,data,meta=future.result()
                except Exception as exc:
                    errors.append(dict(folder=futures[future],error=repr(exc)));continue
                inventories+=1
                for name in data.get('folders',[]):
                    child=(folder+'/' if folder else '')+name
                    # Folder years define reference scope only, never availability.
                    if re.fullmatch(r'(?:19|20)\d{2}',name) and not '2020'<=name<='2025':continue
                    if child not in seen:pending.append(child)
                for file in data.get('files',[]):
                    name=file.get('name','');path=file.get('path') or ((folder+'/' if folder else '')+name)
                    if not re.search(r'\.(?:pdf|docx?|zip|rar|xlsx?)$',name,re.I):continue
                    years=re.findall(r'(?:^|/)((?:19|20)\d{2})(?:/|$)',path)
                    if years and not any('2020'<=y<='2025' for y in years):continue
                    url=BASE+'file?'+urllib.parse.urlencode(dict(path=path,download='false'))
                    key=hashlib.sha256(('XM\n'+path).encode()).hexdigest()
                    month=re.search(r'/((?:19|20)\d{2})/(\d{2})_',path)
                    rows[key]=dict(id=key,source='XM',title_raw=name,url=url,
                        publication_date_claimed=None,published_at_claimed=None,date_precision='unknown',
                        modified_at_claimed=file.get('modificado'),reference_folder=folder,
                        reference_period_claimed=(month.group(1)+'-'+month.group(2)) if month else None,
                        reference_period_basis='folder_name_not_publication',document_kind=name.rsplit('.',1)[-1].lower(),
                        title_kind='official_file_label',catalog_url=meta['url'],raw_file=meta['raw_file'],
                        retrieved_at=meta['retrieved_at'],available_at_verified=None,
                        availability_status='historical_version_unverified',historical_version_verified=False)
        print(json.dumps(dict(folders_done=inventories,pending=len(pending),files=len(rows),errors=len(errors))),flush=True)
    output=sorted(rows.values(),key=lambda r:r['id'])
    (OUT/'xm_report_file_titles.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output),encoding='utf-8')
    save(OUT/'xm_inventory_summary.json',dict(finished_at=now(),files=len(rows),folders=inventories,errors=errors,
        by_extension=dict(collections.Counter(r['document_kind'] for r in output)),
        note='Public anonymous metadata only. Reference folders and modification dates are not publication evidence. File bodies not downloaded.'))

if __name__=='__main__':main()
