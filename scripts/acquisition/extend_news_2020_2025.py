"""Titulares 2020–2025 desde APIs editoriales públicas y corpus abiertos.

No se solicitan ni exportan categorías, temas, sentimiento o relevancia.
Las fechas son declaraciones de fuente, no disponibilidad histórica certificada.
"""
from __future__ import annotations
import calendar
import concurrent.futures
import datetime as dt
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parent/'news_2000_2025'/'extension_2020_2025'
RAW=ROOT/'raw'
TZ=dt.timezone(dt.timedelta(hours=-5))
ALLOWED_MEDIA={'El Tiempo','El Espectador','Semana','Portafolio','La República','El Colombiano','Dinero'}
EXCLUDED_MEDIA={'La Silla Vacía','Las2Orillas','Razón Pública','El Heraldo'}
# User excluded all three publishers; no further API downloads for them.
WP_SITES={}
HOST_LIMITS={name:threading.Semaphore(2) for name in WP_SITES}
HOST_MEDIA={
 'eltiempo.com':'El Tiempo','elespectador.com':'El Espectador','semana.com':'Semana',
 'portafolio.co':'Portafolio','larepublica.co':'La República','elheraldo.co':'El Heraldo',
 'elcolombiano.com':'El Colombiano','dinero.com':'Dinero','lasillavacia.com':'La Silla Vacía',
 'las2orillas.co':'Las2Orillas','razonpublica.com':'Razón Pública','valoraanalitik.com':'Valora Analitik',
 'pulzo.com':'Pulzo','caracol.com.co':'Caracol Radio','noticiascaracol.com':'Noticias Caracol',
 'noticiasrcn.com':'Noticias RCN','rcnradio.com':'RCN Radio','bluradio.com':'Blu Radio',
 'wradio.com.co':'W Radio','elpais.com.co':'El País (Cali)','eluniversal.com.co':'El Universal (Cartagena)',
 'vanguardia.com':'Vanguardia','publimetro.co':'Publimetro','kienyke.com':'KienyKe',
 'cambiocolombia.com':'Cambio','cuestionpublica.com':'Cuestión Pública'}
HOST_MEDIA.update({'noticias.caracoltv.com':'Noticias Caracol','futbolred.com':'Futbolred',
 'antena2.com':'Antena 2','lafm.com.co':'La FM','elnuevosiglo.com.co':'El Nuevo Siglo',
 'minuto30.com':'Minuto30','alertabogota.com':'Alerta Bogotá','zonacero.com':'Zona Cero',
 'lapatria.com':'La Patria','eluniversal.com.co':'El Universal (Cartagena)',
 'hoydiariodelmagdalena.com.co':'Hoy Diario del Magdalena','elquindiano.com':'El Quindiano',
 'diariodelhuila.com':'Diario del Huila','lanacion.com.co':'La Nación (Huila)',
 'elpilón.com.co':'El Pilón','elpilon.com.co':'El Pilón','diariodelnorte.net':'Diario del Norte'})


def now():return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path,obj):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(path)


def connect():
 c=sqlite3.connect(ROOT/'recent_headlines.sqlite',timeout=90)
 c.executescript('''PRAGMA journal_mode=WAL;
 CREATE TABLE IF NOT EXISTS headlines(id TEXT PRIMARY KEY,medium TEXT,url TEXT,canonical_url TEXT,
 title_raw TEXT,publication_date_claimed TEXT,published_at_claimed TEXT,modified_at_claimed TEXT,
 date_precision TEXT,first_source TEXT,retrieved_at TEXT,historical_version_verified INTEGER DEFAULT 0);
 CREATE TABLE IF NOT EXISTS observations(headline_id TEXT,source TEXT,source_record_id TEXT,raw_file TEXT,
 publication_raw TEXT,captured_at TEXT,retrieved_at TEXT,PRIMARY KEY(headline_id,source,source_record_id));
 CREATE TABLE IF NOT EXISTS wp_months(medium TEXT,month TEXT,expected_api_records INTEGER,
 received_api_records INTEGER,unique_post_ids INTEGER,boundary_records_excluded INTEGER,
 pages_expected INTEGER,pages_received INTEGER,status TEXT,PRIMARY KEY(medium,month));
 ''');return c


def medium_for(url):
 host=(urllib.parse.urlsplit(url).hostname or '').lower().removeprefix('www.')
 for suffix,medium in HOST_MEDIA.items():
  if host==suffix or host.endswith('.'+suffix):return medium
 return None


def text_title(value):
 return html.unescape(re.sub('<[^>]*>','',value)).strip()


def record(c,medium,url,title,pub,source,source_id,raw_file,retrieved,modified=None,captured=None,date_only=False,publication_raw=None):
 if medium in EXCLUDED_MEDIA:return 'excluded_by_user'
 if medium not in ALLOWED_MEDIA:return 'outside_user_selected_media'
 if not title or not pub or not url:return 'missing_fields'
 try:
  p=dt.datetime.fromisoformat(pub.replace('Z','+00:00'))
  if p.tzinfo is None or date_only:day=p.date().isoformat();stamp=None;precision='declared_date_timezone_unverified'
  else:day=p.astimezone(TZ).date().isoformat();stamp=p.isoformat();precision='declared_timestamp_with_zone'
 except ValueError:return 'unparseable_date'
 if not '2020-01-01'<=day<='2025-12-31':return 'outside_period'
 u=urllib.parse.urlsplit(url)
 kept=[(k,v) for k,v in urllib.parse.parse_qsl(u.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid'}]
 canonical=urllib.parse.urlunsplit((u.scheme.lower(),u.netloc.lower().removeprefix('www.'),u.path,urllib.parse.urlencode(kept),u.fragment))
 title=text_title(title)
 norm=' '.join(unicodedata.normalize('NFC',title).split())
 key=hashlib.sha256((canonical+'\n'+norm+'\n'+day).encode()).hexdigest()
 c.execute('INSERT OR IGNORE INTO headlines VALUES(?,?,?,?,?,?,?,?,?,?,?,0)',
           (key,medium,url,canonical,title,day,stamp,modified,precision,source,retrieved))
 c.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,?)',
           (key,source,str(source_id),raw_file,publication_raw or pub,captured,retrieved))
 return 'accepted'


def request_cached(url,folder,stem):
 folder.mkdir(parents=True,exist_ok=True);path=folder/(stem+'.json.gz');meta_path=folder/(stem+'.meta.json')
 if path.exists() and meta_path.exists():
  meta=json.loads(meta_path.read_text(encoding='utf-8'));raw=gzip.decompress(path.read_bytes())
  if meta.get('status')=='ok' and hashlib.sha256(raw).hexdigest()==meta['sha256_response']:return json.loads(raw),meta,path
 errors=[]
 for attempt in range(1,5):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Academic-Colombia-headline-history/1.0'})
   with urllib.request.urlopen(req,timeout=75) as r:raw=r.read();headers=dict(r.headers)
   data=json.loads(raw)
   if not isinstance(data,list):raise ValueError('Expected public post list')
   path.write_bytes(gzip.compress(raw,mtime=0));meta=dict(status='ok',url=url,retrieved_at=now(),headers=headers,
    sha256_response=hashlib.sha256(raw).hexdigest(),attempts=attempt,prior_errors=errors)
   save(meta_path,meta);return data,meta,path
  except Exception as e:
   errors.append(repr(e))
   if isinstance(e,urllib.error.HTTPError) and e.code in {401,403,404}:break
   if attempt<4:time.sleep(60 if isinstance(e,urllib.error.HTTPError) and e.code==429 else 2**attempt)
 save(meta_path,dict(status='error',url=url,errors=errors,at=now()))
 raise RuntimeError(f'{url}: {errors[-1]}')


def wp_medium(item):
 medium,host=item[:2];periods=item[2] if len(item)>2 else None
 if medium in EXCLUDED_MEDIA:return dict(medium=medium,status='excluded_by_user',failures=0)
 c=connect();folder=RAW/re.sub('[^a-z0-9]+','_',medium.lower());failures=[]
 HOST_LIMITS[medium].acquire()
 try:
  for year in range(2020,2026):
   for month in range(1,13):
    if periods is not None and (year,month) not in periods:continue
    completed=c.execute('SELECT status FROM wp_months WHERE medium=? AND month=?',(medium,f'{year}-{month:02}')).fetchone()
    if completed and completed[0]=='pass_current_api_inventory':continue
    period=f'{year}-{month:02}';start=dt.datetime(year,month,1);end=dt.datetime(year+(month==12),month%12+1,1)
    params=dict(after=(start-dt.timedelta(seconds=1)).isoformat(),before=end.isoformat(),per_page=100,
      order='asc',orderby='date',_fields='id,date,date_gmt,modified_gmt,link,title',page=1)
    base=host+'/wp-json/wp/v2/posts?'
    try:
     data,meta,path=request_cached(base+urllib.parse.urlencode(params),folder,period+'_p0001')
     headers={k.lower():v for k,v in meta['headers'].items()};expected=int(headers['x-wp-total']);pages=int(headers['x-wp-totalpages'])
     received=excluded=0;seen=set();pages_received=0
     for page in range(1,max(pages,1)+1):
      if page>1:
       params['page']=page;data,meta,path=request_cached(base+urllib.parse.urlencode(params),folder,f'{period}_p{page:04}')
      pages_received+=1
      for row in data:
       received+=1;seen.add(row['id']);local=row.get('date','')
       if not start.isoformat()<=local<end.isoformat():excluded+=1;continue
       gmt=row.get('date_gmt');pub=(gmt+'+00:00') if gmt and gmt!='0000-00-00T00:00:00' else local
       record(c,medium,row['link'],row.get('title',{}).get('rendered',''),pub,'publisher_wordpress_api',row['id'],
        path.relative_to(ROOT).as_posix(),meta['retrieved_at'],modified=row.get('modified_gmt'))
      c.commit()
     okay=received==expected and len(seen)==received and pages_received==max(pages,1)
     c.execute('INSERT OR REPLACE INTO wp_months VALUES(?,?,?,?,?,?,?,?,?)',
       (medium,period,expected,received,len(seen),excluded,max(pages,1),pages_received,'pass_current_api_inventory' if okay else 'mismatch'))
     c.commit()
     print(json.dumps(dict(medium=medium,month=period,received=received,expected=expected,status='pass' if okay else 'mismatch')),flush=True)
    except Exception as e:
     failures.append(dict(month=period,error=repr(e)));print(json.dumps(dict(medium=medium,month=period,error=repr(e))),flush=True)
  suffix=('_'+str(periods[0][0])+'_'+str(periods[0][1])) if periods else ''
  save(ROOT/(re.sub('[^a-z0-9]+','_',medium.lower())+suffix+'_failures.json'),failures)
 finally:c.close();HOST_LIMITS[medium].release()
 return dict(medium=medium,failures=len(failures))


def main():
 RAW.mkdir(parents=True,exist_ok=True);c=connect();c.close()
 jobs=[(medium,host,[(year,month)]) for year in range(2020,2026) for month in range(1,13) for medium,host in WP_SITES.items()]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:results=list(p.map(wp_medium,jobs))
 save(ROOT/'wordpress_download_summary.json',dict(finished_at=now(),sources=results))
 print(json.dumps(dict(wordpress_done=True,results=results)),flush=True)


if __name__=='__main__':main()
