"""Todos los snapshots de feeds hallados por CDX, sólo siete medios elegidos.

Se respetan las fechas reales devueltas por Wayback; no se infieren titulares
desde slugs, pies de foto ni fechas de modificación.
"""
import collections
import base64
import concurrent.futures
import datetime as dt
import email.utils
import gzip
import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from extend_news_2020_2025 import ROOT,ALLOWED_MEDIA,connect,record,medium_for,save,now

RAW=ROOT/'archived_feeds_raw'
LOCK=threading.Lock()
LAST_START=0.0
S='{http://www.sitemaps.org/schemas/sitemap/0.9}'
N='{http://www.google.com/schemas/sitemap-news/0.9}'
A='{http://www.w3.org/2005/Atom}'


def wait_slot():
 global LAST_START
 with LOCK:
  pause=max(0,1.05-(time.monotonic()-LAST_START))
  if pause:time.sleep(pause)
  LAST_START=time.monotonic()


def jobs():
 result={}
 for source in json.loads((ROOT/'feed_capture_summary.json').read_text(encoding='utf-8')):
  if source['medium'] not in ALLOWED_MEDIA:continue
  for stamp,original,status,mime,digest in source.get('captures',[]):
   key=hashlib.sha256((stamp+'\n'+original).encode()).hexdigest()[:24]
   result[key]=dict(key=key,medium=source['medium'],requested_capture=stamp,original_url=original,indexed_digest=digest,indexed_mime=mime)
 return sorted(result.values(),key=lambda row:row['requested_capture'],reverse=True)


def fetch(job):
 path=RAW/(job['key']+'.body.gz');meta_path=RAW/(job['key']+'.meta.json')
 if path.exists() and meta_path.exists():
  meta=json.loads(meta_path.read_text(encoding='utf-8'));raw=gzip.decompress(path.read_bytes())
  if meta.get('status')=='ok' and hashlib.sha256(raw).hexdigest()==meta['sha256_response']:
   digest=base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
   meta['archive_payload_digest_verified']=digest==(meta.get('indexed_digest') or '').removeprefix('sha1:')
   meta['sha1_replayed_payload']=digest
   save(meta_path,meta)
   return meta,raw
 url=f"https://web.archive.org/web/{job['requested_capture']}id_/{job['original_url']}"
 errors=[]
 for attempt in range(1,4):
  try:
   wait_slot()
   req=urllib.request.Request(url,headers={'User-Agent':'Academic-Colombia-headline-archive/1.0'})
   with urllib.request.urlopen(req,timeout=60) as response:raw=response.read();final_url=response.url;headers=dict(response.headers)
   match=re.search(r'/web/(\d{14})[^/]*/',final_url)
   if not match:raise ValueError('Replay redirected away from archived snapshot')
   capture=dt.datetime.strptime(match.group(1),'%Y%m%d%H%M%S').replace(tzinfo=dt.timezone.utc).isoformat()
   wire_digest=base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
   while raw[:2]==b'\x1f\x8b':raw=gzip.decompress(raw)
   decoded_digest=base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
   root=ET.fromstring(raw)
   kind=root.tag.split('}')[-1]
   if kind not in {'urlset','rss','feed','RDF'}:raise ValueError('Replay is not a news sitemap or feed: '+kind)
   path.write_bytes(gzip.compress(raw,mtime=0))
   meta=dict(**job,status='ok',replay_url=url,final_replay_url=final_url,actual_capture_at=capture,
    retrieved_at=now(),sha256_response=hashlib.sha256(raw).hexdigest(),bytes=len(raw),headers=headers,
    attempts=attempt,prior_errors=errors,xml_kind=kind,sha1_replayed_payload=decoded_digest,
    archive_payload_digest_verified=(job.get('indexed_digest') or '').removeprefix('sha1:') in {wire_digest,decoded_digest})
   save(meta_path,meta);return meta,raw
  except Exception as exc:
   errors.append(repr(exc))
   if isinstance(exc,urllib.error.HTTPError) and exc.code in {401,403,404}:break
   if attempt<3:time.sleep(60 if isinstance(exc,urllib.error.HTTPError) and exc.code==429 else 3*attempt)
 meta=dict(**job,status='error',errors=errors,at=now());save(meta_path,meta);return meta,None


def unarchive(url):
 match=re.search(r'/web/\d{14}[^/]*/(https?://.*)',url or '')
 return match.group(1) if match else url


def entries(root):
 for node in root.findall(S+'url'):
  news=node.find(N+'news')
  if news is not None:yield node.findtext(S+'loc'),news.findtext(N+'title'),news.findtext(N+'publication_date')
 for item in root.findall('.//item'):
  yield item.findtext('link'),item.findtext('title'),item.findtext('pubDate') or item.findtext('{http://purl.org/dc/elements/1.1/}date')
 for item in root.findall(A+'entry'):
  link=item.find(A+'link');url=link.get('href') if link is not None else None
  yield url,item.findtext(A+'title'),item.findtext(A+'published')


def pub_iso(value):
 if not value:return None
 try:return dt.datetime.fromisoformat(value.replace('Z','+00:00')).isoformat()
 except ValueError:
  try:return email.utils.parsedate_to_datetime(value).isoformat()
  except (ValueError,TypeError):return None


def main():
 RAW.mkdir(exist_ok=True);plan=jobs();save(ROOT/'archived_feed_plan.json',plan)
 c=connect();total=collections.Counter();results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures=[pool.submit(fetch,job) for job in plan]
  for i,future in enumerate(concurrent.futures.as_completed(futures),1):
   meta,raw=future.result();counts=collections.Counter()
   if raw is not None:
    root=ET.fromstring(raw)
    for index,(url,title,pub) in enumerate(entries(root)):
     url=unarchive(url);medium=medium_for(url or '')
     if medium not in ALLOWED_MEDIA:counts['outside_selected_media']+=1;continue
     normalized=pub_iso(pub)
     if not normalized:counts['missing_or_unparseable_publication_date']+=1;continue
     outcome=record(c,medium,url,title,normalized,'wayback_archived_feed',meta['key']+':'+str(index),
       (RAW/(meta['key']+'.body.gz')).relative_to(ROOT).as_posix(),meta['retrieved_at'],
       captured=meta['actual_capture_at'],publication_raw=pub)
     counts[outcome]+=1
    c.commit()
   total.update(counts);total['snapshots_'+meta['status']]+=1
   results.append(dict(key=meta['key'],medium=meta['medium'],status=meta['status'],counts=dict(counts),
    actual_capture_at=meta.get('actual_capture_at'),errors=meta.get('errors')))
   if i%15==0 or i==len(plan):
    status=dict(completed=i,total=len(plan),counts=dict(total),updated_at=now())
    save(ROOT/'archived_feed_progress.json',status);print(json.dumps(status),flush=True)
 save(ROOT/'archived_feed_download_summary.json',dict(finished_at=now(),total=dict(total),snapshots=results))
 c.close()


if __name__=='__main__':main()
