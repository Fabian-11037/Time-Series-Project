"""Metadatos de catálogos oficiales IDEAM/XM; no infiere publicación del periodo."""
import concurrent.futures
import datetime as dt
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import urllib.parse
import urllib.request

from extend_news_2020_2025 import ROOT,save,now
OUT=ROOT/'official_reports'
RAW=OUT/'catalog_raw'


class Node:
 def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
 def walk(self):
  yield self
  for child in self.children:
   if isinstance(child,Node):yield from child.walk()
 def text(self):return ''.join(child.text() if isinstance(child,Node) else child for child in self.children)


class Tree(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root]
 def handle_starttag(self,tag,attrs):
  node=Node(tag,attrs,self.stack[-1]);self.stack[-1].children.append(node)
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(node)
 def handle_startendtag(self,tag,attrs):self.stack[-1].children.append(Node(tag,attrs,self.stack[-1]))
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:self.stack=self.stack[:i];break
 def handle_data(self,data):self.stack[-1].children.append(data)


def tree(text):p=Tree();p.feed(text);return p.root


def fetch(source,url):
 key=hashlib.sha256(url.encode()).hexdigest()[:24];path=RAW/(key+'.html.gz');meta_path=RAW/(key+'.meta.json')
 if path.exists() and meta_path.exists():
  meta=json.loads(meta_path.read_text(encoding='utf-8'))
  if meta['status']=='ok':return source,url,gzip.decompress(path.read_bytes()).decode('utf-8'),meta
 try:
  quoted=urllib.parse.quote(url,safe=':/?&=%,+()')
  with urllib.request.urlopen(urllib.request.Request(quoted,headers={'User-Agent':'Academic-official-report-title-inventory/1.0'}),timeout=60) as response:raw=response.read();final=response.url
  path.write_bytes(gzip.compress(raw,mtime=0));meta=dict(status='ok',source=source,url=url,final_url=final,retrieved_at=now(),
   raw_file=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest())
  save(meta_path,meta);return source,url,raw.decode('utf-8'),meta
 except Exception as exc:
  meta=dict(status='error',source=source,url=url,error=repr(exc),retrieved_at=now());save(meta_path,meta);return source,url,None,meta


def report_nodes(source,url,text,meta):
 root=tree(text);reports=[];last_page=0
 scope=next((n for n in root.walk() if n.tag=='main' or n.attrs.get('role')=='main'),root)
 if source=='XM':scope=next((n for n in root.walk() if n.tag=='article' and n.attrs.get('data-history-node-id')),scope)
 for node in scope.walk():
  if node.tag!='a':continue
  href=node.attrs.get('href','');label=' '.join(node.text().split())
  for page in re.findall(r'(?:[?&])page=(\d+)',href):last_page=max(last_page,int(page))
  kind='pdf' if re.search(r'\.pdf(?:[?#]|$)',href,re.I) or 'pdf' in node.attrs.get('type','') else 'archive' if re.search(r'\.(?:zip|rar)(?:[?#]|$)',href,re.I) else 'document'
  is_document=('/file-download/download/public/' in href or re.search(r'\.(?:pdf|zip|rar|docx?|xlsx?)(?:[?#]|$)',href,re.I))
  if not is_document or not label:continue
  ancestor=node;pub=None;reference_label=None
  for level in range(9):
   ancestor=ancestor.parent
   if ancestor is None or ancestor.tag in {'body','html'}:break
   classes=ancestor.attrs.get('class','')
   if 'view-content' in classes or 'grid__items' in classes:break
   times=[x.attrs.get('datetime') for x in ancestor.walk() if x.tag=='time' and x.attrs.get('datetime')]
   if times:
    pub=times[0];break
   headings=[x.text().strip() for x in ancestor.walk() if x.tag in {'h2','h3','h4'}]
   if headings and reference_label is None:reference_label=' | '.join(headings)
   if 'card-icon-document' in classes or 'views-row' in classes:break
  day=pub[:10] if pub and re.match(r'\d{4}-\d{2}-\d{2}',pub) else None
  if day and not '2020-01-01'<=day<='2025-12-31':continue
  doc_url=urllib.parse.urljoin(url,href)
  key=hashlib.sha256((source+'\n'+doc_url+'\n'+label+'\n'+str(pub)).encode()).hexdigest()
  reports.append(dict(id=key,source=source,title_raw=label,url=doc_url,publication_date_claimed=day,
   publication_datetime_source=pub,date_precision='catalog_date_only_clock_unverified' if day else 'unknown',
   reference_label=reference_label,document_kind=kind,title_kind='official_catalog_link_label',
   catalog_url=url,raw_file=meta['raw_file'],retrieved_at=meta['retrieved_at'],available_at_verified=None,
   availability_status='historical_version_unverified',historical_version_verified=False))
 return root,reports,last_page


def main():
 RAW.mkdir(parents=True,exist_ok=True);records={};errors=[];plan=[]
 catalog=gzip.decompress((OUT/'ideam_catalog.html.gz').read_bytes()).decode('utf-8')
 roots=set()
 for node in tree(catalog).walk():
  if node.tag=='a' and 'Consultar repositorio' in node.text():
   href=node.attrs.get('href','');roots.add(urllib.parse.urljoin('https://www.ideam.gov.co',href))
 for url in sorted(roots):plan.append(('IDEAM',url+'?'+urllib.parse.urlencode(dict(desde='2020-01-01',hasta='2025-12-31'))))
 xm=gzip.decompress((OUT/'xm_home.html.gz').read_bytes()).decode('utf-8')
 for node in tree(xm).walk():
  if node.tag=='a':
   href=node.attrs.get('href','')
   if '/nuestra-empresa/informes/' in href and href.startswith(('https://www.xm.com.co','/')):
    plan.append(('XM',urllib.parse.urljoin('https://www.xm.com.co',href)))
 plan=list(dict.fromkeys(plan));save(OUT/'catalog_plan.json',plan)
 later=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  results=list(pool.map(lambda job:fetch(*job),plan))
 for source,url,text,meta in results:
  if text is None:errors.append(meta);continue
  root,items,last=report_nodes(source,url,text,meta)
  records.update({item['id']:item for item in items})
  if source=='IDEAM':
   later.extend((source,url+'&page='+str(page)) for page in range(1,last+1))
  print(json.dumps(dict(source=source,first_page_url=url,reports=len(items),more_pages=last)),flush=True)
 save(OUT/'additional_pages_plan.json',later)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(fetch,*job) for job in later]
  for i,future in enumerate(concurrent.futures.as_completed(futures),1):
   source,url,text,meta=future.result()
   if text is None:errors.append(meta);continue
   _,items,_=report_nodes(source,url,text,meta);records.update({item['id']:item for item in items})
   if i%30==0 or i==len(later):print(json.dumps(dict(catalog_pages_done=i,total=len(later),report_labels=len(records),errors=len(errors))),flush=True)
 rows=sorted(records.values(),key=lambda x:(x['source'],x['publication_date_claimed'] or '9999',x['id']))
 (OUT/'official_report_titles.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
 save(OUT/'collection_summary.json',dict(finished_at=now(),records=len(rows),dated_records=sum(bool(x['publication_date_claimed']) for x in rows),
  undated_records=sum(not x['publication_date_claimed'] for x in rows),by_source={s:sum(x['source']==s for x in rows) for s in ['IDEAM','XM']},
  errors=errors,initial_pages=len(plan),additional_pages=len(later),historical_availability_verified=False,
  note='Document labels only, including archive containers; no publication date inferred from a report period or filename'))
 print(json.dumps(dict(official_collection_done=True,reports=len(rows),errors=len(errors))),flush=True)


if __name__=='__main__':main()
