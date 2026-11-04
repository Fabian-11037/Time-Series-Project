"""Descarga versiones fijas de corpus abiertos para ampliar titulares 2020–2025."""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parent/'news_2000_2025'/'extension_2020_2025'
OUT=ROOT/'open_corpora_raw'


def job_list():
 jobs=[]
 for meta_file,repo,filter_file in [
  ('hf_babel.json','felixludos/babel-briefings',lambda x:x=='data/babel-briefings-v1-co.json'),
  ('hf_villaitech.json','Villaitech/colombia-news',lambda x:x.endswith('.parquet')),
  ('hacktoberfest-corpus-es_colmbian_spanish_news.json','hacktoberfest-corpus-es/colmbian_spanish_news',lambda x:x.endswith('.parquet')),
 ]:
  meta=json.loads((ROOT/meta_file).read_text(encoding='utf-8'))
  for item in meta['siblings']:
   filename=item['rfilename']
   if filter_file(filename):jobs.append(dict(repo=repo,revision=meta['sha'],filename=filename))
 return jobs


def fetch(job):
 for candidate in OUT.glob('*.meta.json'):
  previous=json.loads(candidate.read_text(encoding='utf-8'))
  if previous.get('status')=='ok' and all(previous.get(k)==job[k] for k in ['repo','revision','filename']):
   if (OUT/previous['local_file']).exists():return previous
 # Short names keep the full workspace path below Windows MAX_PATH.
 stem=hashlib.sha256((job['repo']+job['filename']).encode()).hexdigest()[:16]+Path(job['filename']).suffix
 dest=OUT/stem;meta_path=OUT/(stem+'.meta.json')
 if dest.exists() and meta_path.exists():return json.loads(meta_path.read_text(encoding='utf-8'))
 url=f"https://huggingface.co/datasets/{job['repo']}/resolve/{job['revision']}/{job['filename']}"
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Academic-Colombia-public-news-history/1.0'})
  with urllib.request.urlopen(req,timeout=240) as response:
   digest=hashlib.sha256();size=0;temp=dest.with_suffix(dest.suffix+'.tmp')
   with temp.open('wb') as stream:
    while chunk:=response.read(1024*1024):stream.write(chunk);digest.update(chunk);size+=len(chunk)
  temp.replace(dest)
  result=dict(**job,status='ok',url=url,local_file=dest.name,bytes=size,sha256=digest.hexdigest(),retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat())
 except Exception as exc:result=dict(**job,status='error',url=url,error=repr(exc))
 meta_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,ensure_ascii=True),flush=True);return result


if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:results=list(p.map(fetch,job_list()))
 (ROOT/'open_corpora_download_summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
