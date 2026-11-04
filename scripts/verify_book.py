"""Comprueba ejecución y enlaces locales del libro, sin abrir datos de prueba."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]

class References(HTMLParser):
    def __init__(self):super().__init__();self.refs=[]
    def handle_starttag(self,tag,attrs):
        self.refs.extend(value for key,value in attrs if key in ('href','src') and value)

def main():
    notebooks=[]
    for path in sorted((ROOT/'book').glob('*.ipynb')):
        nb=json.loads(path.read_text(encoding='utf-8'))
        cells=[c for c in nb['cells'] if c['cell_type']=='code']
        errors=sum(o['output_type']=='error' for c in cells for o in c.get('outputs',[]))
        assert cells and all(c.get('execution_count') is not None for c in cells),path.name
        assert not errors,path.name
        notebooks.append(dict(notebook=path.name,code_cells=len(cells),errors=errors))
    # Sphinx also copies unrendered Jinja macros under _static; those are assets.
    pages=[p for p in (ROOT/'docs').rglob('*.html') if '_static' not in p.relative_to(ROOT/'docs').parts];assert pages
    broken=[]
    for page in pages:
        parser=References();parser.feed(page.read_text(encoding='utf-8'))
        for ref in parser.refs:
            url=urlsplit(ref)
            if url.scheme or url.netloc or not url.path:continue
            target=(ROOT/'docs'/unquote(url.path).lstrip('/')) if url.path.startswith('/') else page.parent/unquote(url.path)
            if not target.exists():broken.append(dict(page=str(page.relative_to(ROOT/'docs')),reference=ref))
    assert not broken,broken
    audit=json.loads((ROOT/'results/headlines/analysis_audit.json').read_text(encoding='utf-8'))
    assert audit['fit_split']=='train' and audit['validation_fit_documents']==0 and audit['test_documents_read']==0
    assert audit['fit_max_available']<'2018' and audit['E1_numeric_only']
    assert not audit['raw_dataset_modified'] and not audit['numeric_or_price_data_read']
    report=dict(html_pages=len(pages),notebooks_executed=len(notebooks),
        code_cells=sum(r['code_cells'] for r in notebooks),cell_errors=0,
        broken_local_references=broken,E1_numeric_only=True,
        headline_topic_fit_split='train',headline_topic_test_documents_read=0)
    (ROOT/'results/all_notebooks_verified.json').write_text(json.dumps(notebooks,indent=2)+'\n',encoding='utf-8')
    (ROOT/'results/book_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
