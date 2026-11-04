"""Inspección reproducible de índices públicos; no clasifica ni descarga cuerpos."""
import concurrent.futures
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent / 'news_2000_2025'
RAW = ROOT / 'discovery_raw'
SOURCES = {
    'El Tiempo robots': 'https://www.eltiempo.com/robots.txt',
    'Portafolio robots': 'https://www.portafolio.co/robots.txt',
    'El Espectador index': 'https://www.elespectador.com/arc/outboundfeeds/sitemap-index/?outputType=xml',
    'El Espectador news': 'https://www.elespectador.com/arc/outboundfeeds/news-sitemap/?outputType=xml',
    'Semana index': 'https://www.semana.com/arc/outboundfeeds/sitemap-index/?outputType=xml',
    'Semana news index': 'https://www.semana.com/arc/outboundfeeds/news-sitemap-index/?outputType=xml',
    'La Republica index': 'https://www.larepublica.co/sitemapindex',
    'El Colombiano index': 'https://www.elcolombiano.com/megasitemap.xml',
    'Wayback CDX': 'https://web.archive.org/cdx/search/cdx?url=www.elespectador.com/&from=2000&to=2025&output=json&filter=statuscode:200&collapse=timestamp:6&fl=timestamp,original,statuscode&limit=500',
}


def inspect(label_url):
    label, url = label_url
    name = re.sub('[^a-zA-Z0-9]+', '_', label)
    path = RAW / f'{name}.body.gz'
    result = dict(source=label, url=url, queried_at=dt.datetime.now(dt.timezone.utc).isoformat())
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Academic-archive-inventory/1.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            result.update(status=response.status, final_url=response.url, headers=dict(response.headers))
        path.write_bytes(gzip.compress(raw, mtime=0))
        result.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), raw_file=path.name)
        if 'robots' in label:
            result['sitemaps'] = re.findall(r'(?im)^sitemap:\s*(\S+)', raw.decode('utf-8', errors='replace'))
            result['text'] = raw.decode('utf-8', errors='replace')[:3500]
        elif 'CDX' in label:
            obj = json.loads(raw)
            result['rows'] = len(obj)-1
            result['sample'] = obj[:5] + obj[-3:]
        else:
            root = ET.fromstring(raw)
            result['xml_root'] = root.tag
            locs = [x.text for x in root.iter() if x.tag.split('}')[-1] == 'loc']
            result['loc_count'] = len(locs)
            result['locs'] = locs
            result['xml_sample'] = raw.decode('utf-8', errors='replace')[:1800]
    except Exception as exc:
        result['error'] = repr(exc)
    (ROOT / f'{name}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in {'headers', 'locs', 'text', 'xml_sample'}}, ensure_ascii=True), flush=True)
    return result


if __name__ == '__main__':
    RAW.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(inspect, SOURCES.items()))
    (ROOT / 'discovery_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
