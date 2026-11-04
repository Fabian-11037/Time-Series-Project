"""Recupera metadatos públicos exhaustivamente en los índices enumerados.

No descarga cuerpos de artículos, no clasifica temas y no convierte slugs,
leyendas de imágenes o lastmod en titulares/fechas de publicación.
El corpus editorial completo no se presume equivalente a sus sitemaps actuales.
"""
import concurrent.futures
import csv
import datetime as dt
import gzip
import hashlib
import json
import re
import sqlite3
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'news_2000_2025'
RAW = ROOT / 'public_raw'
S = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
N = '{http://www.google.com/schemas/sitemap-news/0.9}'
MEDIA = ['El Tiempo', 'El Espectador', 'Semana', 'Portafolio', 'La República', 'El Heraldo', 'El Colombiano']
TZ = dt.timezone(dt.timedelta(hours=-5))


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def save(path, obj):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    tmp.replace(path)


def xml_bytes(raw):
    for _ in range(3):
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        else:
            return raw
    raise ValueError('Too many gzip layers')


def jobs():
    out = []
    for file, medium in [('El_Tiempo_index.json', 'El Tiempo'), ('Portafolio_index.json', 'Portafolio')]:
        for url in load(file)['locs']:
            match = re.search(r'sitemap-articles-(\d{4}-\d{2})\.xml', url)
            if match and '2000-01' <= match.group(1) <= '2025-12':
                out.append(dict(medium=medium, url=url, index_month=match.group(1)))
    months = {name: index for index, name in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'], 1)}
    for url in load('La_Republica_index.json')['locs']:
        match = re.search(r'articles_([A-Za-z]+)_(\d{4})\.xml', url)
        if match and 2000 <= int(match.group(2)) <= 2025:
            out.append(dict(medium='La República', url=url, index_month=f'{match.group(2)}-{months[match.group(1)]:02}'))
    for url in load('El_Colombiano_index.json')['locs']:
        out.append(dict(medium='El Colombiano', url=url, index_month=None))
    # Recent public feeds checked as sources, not assumed to be historical archives.
    for file, medium in [('El_Espectador_news.json', 'El Espectador'), ('Semana_news_index.json', 'Semana')]:
        obj = load(file)
        urls = obj['locs'] if 'index' in file else [obj['url']]
        out.extend(dict(medium=medium, url=url, index_month=None) for url in urls)
    return list({row['url']: row for row in out}.values())


def fetch(job):
    key = hashlib.sha256(job['url'].encode()).hexdigest()
    path = RAW / f'{key}.body.gz'
    meta_path = RAW / f'{key}.meta.json'
    if path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        raw = gzip.decompress(path.read_bytes())
        if meta.get('status') == 'ok' and hashlib.sha256(raw).hexdigest() == meta['sha256_response']:
            return job, meta, raw
    errors = []
    for attempt in range(1, 5):
        try:
            req = urllib.request.Request(job['url'], headers={'User-Agent': 'Academic-news-metadata-inventory/1.0'})
            with urllib.request.urlopen(req, timeout=70) as response:
                raw, headers = response.read(), dict(response.headers)
            decoded = xml_bytes(raw)
            ET.fromstring(decoded)
            path.write_bytes(gzip.compress(raw, mtime=0))
            meta = dict(**job, status='ok', retrieved_at=now(), sha256_response=hashlib.sha256(raw).hexdigest(),
                        sha256_xml=hashlib.sha256(decoded).hexdigest(), bytes=len(raw), response_headers=headers,
                        raw_file=path.name, attempts=attempt, prior_errors=errors)
            save(meta_path, meta)
            return job, meta, raw
        except Exception as exc:
            errors.append(repr(exc))
            if attempt < 4:
                time.sleep(min(2**attempt, 20))
    meta = dict(**job, status='error', errors=errors, retrieved_at=now())
    save(meta_path, meta)
    return job, meta, None


def canonical(url):
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path, p.query, p.fragment))


def publication_date(value):
    if not value:
        return None, None, 'missing'
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo:
            return parsed.astimezone(TZ).date().isoformat(), parsed.isoformat(), 'declared_timestamp_with_zone'
        date = parsed.date().isoformat()
        return date, None, 'declared_date_or_timestamp_without_zone'
    except ValueError:
        return None, None, 'unparseable'


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(ROOT / 'news_public.sqlite')
    connection.executescript('''
      PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS source_files(url TEXT PRIMARY KEY, medium TEXT, index_month TEXT,
        status TEXT, retrieved_at TEXT, raw_file TEXT, sha256_response TEXT, url_count INTEGER, headline_count INTEGER);
      CREATE TABLE IF NOT EXISTS url_inventory(medium TEXT, url TEXT, lastmod_source TEXT,
        index_month TEXT, source_file TEXT, PRIMARY KEY(medium,url,source_file));
      CREATE TABLE IF NOT EXISTS headlines(id TEXT PRIMARY KEY, medium TEXT, url TEXT, title_raw TEXT,
        publication_date_claimed TEXT, published_at_claimed TEXT, date_precision TEXT,
        source_file TEXT, retrieved_at TEXT, historical_version_verified INTEGER DEFAULT 0);
    ''')
    tasks = jobs()
    save(ROOT / 'public_download_plan.json', dict(created_at=now(), jobs=tasks, scope='Published sitemap inventory; not an editorial census'))
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch, job) for job in tasks]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            job, meta, raw = future.result()
            url_count = headline_count = 0
            if raw is None:
                errors.append(meta)
            else:
                root = ET.fromstring(xml_bytes(raw))
                for entry in root.findall(S+'url'):
                    url = entry.findtext(S+'loc')
                    if not url:
                        continue
                    url = canonical(url)
                    url_count += 1
                    connection.execute('INSERT OR IGNORE INTO url_inventory VALUES(?,?,?,?,?)',
                        (job['medium'], url, entry.findtext(S+'lastmod'), job['index_month'], job['url']))
                    news = entry.find(N+'news')
                    title = news.findtext(N+'title') if news is not None else None
                    raw_date = news.findtext(N+'publication_date') if news is not None else None
                    day, stamp, precision = publication_date(raw_date)
                    if not title or not day or not '2000-01-01' <= day <= '2025-12-31':
                        continue
                    title = title.strip()
                    normalized = ' '.join(unicodedata.normalize('NFC', title).split())
                    key = hashlib.sha256((job['medium']+'\n'+url+'\n'+normalized+'\n'+str(raw_date)).encode()).hexdigest()
                    connection.execute('INSERT OR IGNORE INTO headlines VALUES(?,?,?,?,?,?,?,?,?,0)',
                        (key, job['medium'], url, title, day, stamp, precision, job['url'], meta['retrieved_at']))
                    headline_count += 1
            connection.execute('INSERT OR REPLACE INTO source_files VALUES(?,?,?,?,?,?,?,?,?)',
                (job['url'], job['medium'], job['index_month'], meta['status'], meta['retrieved_at'],
                 meta.get('raw_file'), meta.get('sha256_response'), url_count, headline_count))
            connection.commit()
            if i % 15 == 0 or i == len(tasks) or raw is None:
                progress = dict(completed=i, total=len(tasks), errors=len(errors), at=now(),
                    unique_headlines=connection.execute('SELECT COUNT(*) FROM headlines').fetchone()[0],
                    url_observations=connection.execute('SELECT COUNT(*) FROM url_inventory').fetchone()[0])
                save(ROOT / 'public_download_progress.json', progress)
                print(json.dumps(progress), flush=True)
    save(ROOT / 'public_download_errors.json', errors)
    connection.execute('CREATE INDEX IF NOT EXISTS headline_month_medium ON headlines(medium,publication_date_claimed)')
    connection.commit()
    for table in ['headlines', 'source_files']:
        cursor = connection.execute('SELECT * FROM '+table)
        with (ROOT / f'{table}.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow([desc[0] for desc in cursor.description])
            writer.writerows(cursor)
    summary = dict(completed_at=now(), source_files=len(tasks), errors=len(errors),
        unique_headlines=connection.execute('SELECT COUNT(*) FROM headlines').fetchone()[0],
        url_observations=connection.execute('SELECT COUNT(*) FROM url_inventory').fetchone()[0],
        full_editorial_corpus_certified=False, manual_topic_classification=False)
    save(ROOT / 'public_download_summary.json', summary)
    connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    connection.close()
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
