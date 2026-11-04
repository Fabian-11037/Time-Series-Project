"""Extrae sólo titulares originales, URL y fechas; descarta etiquetas de tema."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit

from extend_news_2020_2025 import ROOT,connect,record,medium_for,save,now
sys.path.insert(0,str(Path(tempfile.gettempdir())/'codex_colombia_news_deps'))
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'_deps_news'))
import duckdb


def main():
 sources=json.loads((ROOT/'open_corpora_download_summary.json').read_text(encoding='utf-8'))
 c=connect();d=duckdb.connect();summaries=[]
 for source in sources:
  if source['status']!='ok':raise RuntimeError('An open corpus was not downloaded')
  path=ROOT/'open_corpora_raw'/source['local_file']
  assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
  counts=collections.Counter();domains=collections.Counter();date_bounds=[]
  def insert(url,title,pub,source_id,modified=None,captured=None,date_only=False):
   counts['source_records']+=1
   medium=medium_for(url or '')
   if medium is None:
    counts['outside_colombian_media_registry']+=1;domains[urlsplit(url or '').netloc]+=1;return
   status=record(c,medium,url,title,pub,source['repo'],source_id,path.relative_to(ROOT).as_posix(),source['retrieved_at'],
                 modified=modified,captured=captured,date_only=date_only)
   counts[status]+=1
   if status=='accepted':date_bounds.append(pub[:10])
  repo=source['repo']
  if repo=='felixludos/babel-briefings':
   with path.open(encoding='utf-8') as stream:rows=json.load(stream)
   for row in rows:
    observations=[item.get('collectedAt') for item in row.get('instances',[]) if item.get('collectedAt')]
    insert(row.get('url'),row.get('title'),row.get('publishedAt'),row.get('ID'),captured=min(observations) if observations else None)
   del rows
  elif repo=='Villaitech/colombia-news':
   query=d.execute('SELECT id, metadata.url, metadata.title, metadata.publish_date FROM read_parquet(?)',[str(path)])
   while batch:=query.fetchmany(2000):
    for ident,url,title,pub in batch:insert(url,title,pub,ident)
  else:
   query=d.execute('SELECT news_id, news_url_absolute, news_title, news_init_date, news_final_date FROM read_parquet(?)',[str(path)])
   while batch:=query.fetchmany(2000):
    for ident,url,title,pub,modified in batch:insert(url,title,pub,ident,modified=modified,date_only=True)
  c.commit()
  summary=dict(repo=repo,filename=source['filename'],counts=dict(counts),
    declared_date_bounds=[min(date_bounds),max(date_bounds)] if date_bounds else None,
    excluded_hosts_not_in_registry=domains.most_common(),revision=source['revision'],sha256=source['sha256'])
  summaries.append(summary);print(json.dumps({k:v for k,v in summary.items() if k!='excluded_hosts_not_in_registry'},ensure_ascii=True),flush=True)
 save(ROOT/'open_corpora_ingestion_summary.json',dict(at=now(),sources=summaries,
  original_source_categories_ignored=True,no_original_external_splits_used_for_forecasting=True))
 c.close();d.close()


if __name__=='__main__':main()
