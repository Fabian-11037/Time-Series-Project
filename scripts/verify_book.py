"""Comprueba ejecución y enlaces locales del libro, sin abrir datos de prueba."""
import json
import ast
import hashlib
import csv
from inline_notebook_code import is_presentation_cell
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
        assert nb.get('metadata',{}).get('inline_analysis_sources'),path.name
        for cell in cells:
            tags=set(cell.get('metadata',{}).get('tags',[]))
            presentation=is_presentation_cell(''.join(cell['source']))
            assert not tags & {'hide-input','hide-cell'},path.name
            assert ('remove-input' in tags)==presentation,path.name
            assert cell.get('metadata',{}).get('code_role')==('presentation' if presentation else 'analysis'),path.name
            code='\n'.join(line for line in ''.join(cell['source']).splitlines() if not line.startswith('%'))
            for node in ast.walk(ast.parse(code)):
                if isinstance(node,ast.ImportFrom):
                    assert not node.level and not (node.module or '').startswith('colombia_energy'),path.name
                if isinstance(node,ast.Import):
                    assert not any(alias.name.startswith('colombia_energy') for alias in node.names),path.name
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                    assert node.func.id not in {'exec','eval','__import__'},path.name
                    if not presentation:assert node.func.id != 'Markdown',path.name
        notebooks.append(dict(notebook=path.name,code_cells=len(cells),presentation_inputs_removed=sum(is_presentation_cell(''.join(c['source'])) for c in cells),errors=errors))
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
    pipeline=json.loads((ROOT/'results/pipeline/manifest.json').read_text(encoding='utf-8'))
    config=json.loads((ROOT/'configs/training_pipeline.json').read_text(encoding='utf-8'))
    assert pipeline['config']==config and pipeline['folds']==config['n_splits']
    assert config['method']=='split_train_val_forwardChaining' and not pipeline['test_values_read']
    assert pipeline['fitted_preprocessors']==config['n_splits']
    assert pipeline['test_manifest_sha256']==hashlib.sha256((ROOT/'data/test_freeze.json').read_bytes()).hexdigest()
    with (ROOT/'results/pipeline/folds.csv').open(encoding='utf-8',newline='') as stream:
        folds=list(csv.DictReader(stream))
    assert len(folds)==config['n_splits']
    for fold in folds:
        assert fold['train_end_exclusive']<=fold['validation_start']
        assert fold['validation_end_exclusive']<='2022-01-01 00:00:00-05:00'
    scope=json.loads((ROOT/'results/eda_training_scope.json').read_text(encoding='utf-8'))
    text_scope=json.loads((ROOT/'results/headlines/development_audit.json').read_text(encoding='utf-8'))
    assert scope['period_start']==config['development_start']
    assert scope['period_end_exclusive']==config['development_end_exclusive']
    assert scope['feature_count']==37 and not scope['test_values_read']
    assert scope['search_folds_match_saved_audit']
    assert not scope['model_training_repeated']
    assert text_scope['test_documents_read']==0 and text_scope['full_development_projected']
    assert text_scope['max_available']<'2022' and not text_scope['vocabulary_refit_with_validation']
    with (ROOT/'results/tables/precio_anual_desarrollo.csv').open(encoding='utf-8',newline='') as stream:
        annual=list(csv.DictReader(stream))
    assert [int(row['anio']) for row in annual]==list(range(2000,2022))
    model_nb=json.loads((ROOT/'book/10_modelos.ipynb').read_text(encoding='utf-8'))
    model_nodes=[]
    for cell in model_nb['cells']:
        if cell['cell_type']=='code':
            model_nodes.extend(ast.parse('\n'.join(line for line in ''.join(cell['source']).splitlines() if not line.startswith('%'))).body)
    functions={n.name for n in model_nodes if isinstance(n,ast.FunctionDef)}
    assert {'select_device','synchronize_device','seed_training','runtime_environment','exclusive_run'}.issubset(functions)
    assert model_nb['metadata']['inline_analysis_sources']['runtime']==hashlib.sha256((ROOT/'src/colombia_energy/runtime.py').read_bytes()).hexdigest()
    report=dict(html_pages=len(pages),notebooks_executed=len(notebooks),
        code_cells=sum(r['code_cells'] for r in notebooks),cell_errors=0,
        broken_local_references=broken,analysis_code_in_notebooks=True,analysis_inputs_visible=True,presentation_inputs_removed=sum(r['presentation_inputs_removed'] for r in notebooks),project_library_imports=0,E1_numeric_only=True,
        eda_development_start=scope['period_start'],eda_development_end_exclusive=scope['period_end_exclusive'],eda_feature_count=scope['feature_count'],headline_development_documents=text_scope['documents'],portable_runtime_code_in_notebook=True,headline_topic_fit_split='train',headline_topic_test_documents_read=0,validation_method=config['method'],forward_chaining_folds=len(folds))
    (ROOT/'results/all_notebooks_verified.json').write_text(json.dumps(notebooks,indent=2)+'\n',encoding='utf-8')
    (ROOT/'results/book_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
