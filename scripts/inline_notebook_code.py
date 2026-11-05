"""Genera celdas ejecutables y visibles con el código de cada análisis."""
import ast
import copy
import hashlib
from pathlib import Path

import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]
MODULES=['data','asof_text','model_policy','forward_chaining','pipeline','eda','headline_eda']

def notebook_setup():
    return '''%matplotlib inline
from pathlib import Path

ROOT = next(
    directory for directory in [Path.cwd(), *Path.cwd().parents]
    if (directory / "data/manifest.json").exists()
)
'''


def is_presentation_node(node):
    if isinstance(node,ast.FunctionDef):
        return node.name in {'decision','table','figure'}
    if isinstance(node,ast.If):
        return bool(node.body) and all(is_presentation_node(n) for n in node.body+node.orelse)
    if not isinstance(node,ast.Expr) or not isinstance(node.value,ast.Call):
        return False
    call=node.value
    if isinstance(call.func,ast.Name) and call.func.id=='decision':
        return all(isinstance(arg,(ast.Constant,ast.JoinedStr)) for arg in call.args)
    return (isinstance(call.func,ast.Name) and call.func.id=='display'
        and len(call.args)==1 and isinstance(call.args[0],ast.Call)
        and isinstance(call.args[0].func,ast.Name) and call.args[0].func.id=='Markdown')


def is_presentation_cell(source):
    """Identifica celdas dedicadas únicamente a texto o formato de salidas."""
    try:
        body=ast.parse(source).body
    except SyntaxError:
        return False
    return bool(body) and all(is_presentation_node(node) for node in body)


def apply_presentation_visibility(nb):
    for cell in nb.cells:
        if cell.cell_type!='code':
            continue
        tags=[tag for tag in cell.metadata.get('tags',[]) if tag not in {'hide-input','remove-input','hide-cell'}]
        presentation=is_presentation_cell(cell.source)
        if presentation:
            tags.append('remove-input')
        cell.metadata['code_role']='presentation' if presentation else 'analysis'
        if tags:
            cell.metadata['tags']=tags
        else:
            cell.metadata.pop('tags',None)
    return nb

class NotebookNames(ast.NodeTransformer):
    def visit_ImportFrom(self,node):
        if node.level or (node.module or '').startswith('colombia_energy'):
            return None
        return node

    def visit_Attribute(self,node):
        node=self.generic_visit(node)
        if isinstance(node.value,ast.Name):
            if node.value.id=='eda':return ast.copy_location(ast.Name(id=node.attr,ctx=node.ctx),node)
            if node.value.id=='self':
                if node.attr=='transform':return ast.copy_location(ast.Name(id='project_titles',ctx=node.ctx),node)
                node.value.id='study'
        return node

def converted(node):
    return ast.fix_missing_locations(NotebookNames().visit(copy.deepcopy(node)))

def loaded_names(node):
    return {n.id for n in ast.walk(node) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}

def output_boundary(node):
    return (isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)
        and isinstance(node.value.func,ast.Name) and node.value.func.id in {'table','figure','display','decision'})

def analytical_cells(nodes):
    pending=[];cells=[]
    for node in nodes:
        if is_presentation_node(node):
            if pending:
                cells.append(nbf.v4.new_code_cell(ast.unparse(ast.Module(body=pending,type_ignores=[]))))
                pending=[]
            cells.append(nbf.v4.new_code_cell(ast.unparse(node)))
            continue
        pending.append(node)
        if output_boundary(node):
            cells.append(nbf.v4.new_code_cell(ast.unparse(ast.Module(body=pending,type_ignores=[]))))
            pending=[]
    if pending:cells.append(nbf.v4.new_code_cell(ast.unparse(ast.Module(body=pending,type_ignores=[]))))
    return cells

class SourceCatalog:
    def __init__(self):
        self.definitions={};self.imports={};self.initializers=[];self.methods={};self.hashes={}
        for module in MODULES:
            path=ROOT/'src/colombia_energy'/(module+'.py')
            source=path.read_text(encoding='utf-8')
            self.hashes[module]=hashlib.sha256(source.encode()).hexdigest()
            for original in ast.parse(source).body:
                if isinstance(original,(ast.Import,ast.ImportFrom)):
                    if isinstance(original,ast.ImportFrom) and original.level:continue
                    for alias in original.names:
                        name=alias.asname or (alias.name.split('.')[0] if isinstance(original,ast.Import) else alias.name)
                        self.imports[name]=original
                elif isinstance(original,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    self.definitions[original.name]=converted(original)
                elif isinstance(original,ast.Assign):
                    for target in original.targets:
                        if isinstance(target,ast.Name) and target.id!='ROOT':self.definitions[target.id]=converted(original)
                elif isinstance(original,ast.Expr) and isinstance(original.value,ast.Call):
                    self.initializers.append(converted(original))
                elif isinstance(original,ast.ClassDef) and original.name=='HeadlineStudy':
                    self.methods={method.name:converted(method) for method in original.body if isinstance(method,ast.FunctionDef)}
        project=copy.deepcopy(self.methods['transform'])
        project.name='project_titles';project.args.args=project.args.args[1:]
        self.definitions['project_titles']=ast.fix_missing_locations(project)
        self.imports['SimpleNamespace']=ast.parse('from types import SimpleNamespace').body[0]

    def support_cells(self,analysis):
        required=set().union(*(loaded_names(node) for node in analysis))
        # Values computed in the chapter take precedence over similarly named functions.
        class Bindings(ast.NodeVisitor):
            def __init__(self):self.names=set()
            def visit_Name(self,node):
                if isinstance(node.ctx,ast.Store):self.names.add(node.id)
            def visit_FunctionDef(self,node):self.names.add(node.name)
            def visit_ClassDef(self,node):self.names.add(node.name)
            def visit_Lambda(self,node):pass
        bindings=Bindings()
        for node in analysis:bindings.visit(node)
        required-=bindings.names
        selected={};visiting=set()
        def include(name):
            if name in selected or name in visiting or name not in self.definitions:return
            visiting.add(name)
            node=self.definitions[name]
            for dependency in sorted(loaded_names(node)-{name}):include(dependency)
            selected[name]=node
            visiting.remove(name)
        for name in sorted(required):include(name)
        used=required|set().union(*(loaded_names(n) for n in selected.values()))
        imports=[];seen=set()
        for name in sorted(used):
            if name in self.imports:
                code=ast.unparse(self.imports[name])
                if code not in seen:imports.append(code);seen.add(code)
        cells=[nbf.v4.new_code_cell(notebook_setup()+'\n'+'\n'.join(imports))]
        constants=[node for node in selected.values() if isinstance(node,ast.Assign)]
        for node in self.initializers:
            names=loaded_names(node)
            if names & {'RESULTS','OUT'} and (names & {'RESULTS','OUT'}).issubset(selected):constants.append(node)
            elif 'plt' in names and 'plt' in used:constants.append(node)
        if 'pd' in used:
            constants.extend(ast.parse("pd.set_option('display.max_rows', 35)\npd.set_option('display.max_columns', 14)\npd.set_option('display.float_format', lambda x: f'{x:.5g}')").body)
        if constants:cells.append(nbf.v4.new_code_cell(ast.unparse(ast.Module(body=constants,type_ignores=[]))))
        for name,node in selected.items():
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                cells.append(nbf.v4.new_code_cell(ast.unparse(node)))
        return cells

def materialize_notebook(nb,stem):
    """El cuaderno resultante ejecuta las implementaciones incluidas en sus celdas."""
    catalog=SourceCatalog();result=[];all_nodes=[]
    for cell in nb.cells:
        if cell.cell_type!='code':result.append(cell);continue
        source=cell.source.strip()
        if source.startswith('%matplotlib inline'):continue
        if source.startswith('from colombia_energy.headline_eda import HeadlineStudy'):
            nodes=ast.parse('study = SimpleNamespace()').body
            nodes+=copy.deepcopy(catalog.methods['__init__'].body)
            nodes+=copy.deepcopy(catalog.methods['lexical'].body)
        elif source in {'study.fit_topics()','study.profiles()','study.drift()'}:
            method=source.split('.')[1].split('(')[0]
            nodes=copy.deepcopy(catalog.methods[method].body)
        elif source.startswith('eda.') and len(ast.parse(source).body)==1:
            expression=ast.parse(source).body[0]
            call=expression.value
            if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr in catalog.definitions and call.func.attr not in {'decision','table','figure'}:
                nodes=copy.deepcopy(catalog.definitions[call.func.attr].body)
            else:nodes=converted(ast.parse(source)).body
        else:nodes=converted(ast.parse(source)).body
        all_nodes.extend(nodes);result.extend(analytical_cells(nodes))
    support=catalog.support_cells(all_nodes)
    # Keep the chapter introduction before its imports, data access and helper definitions.
    first_code=next(i for i,cell in enumerate(result) if cell.cell_type=='code')
    result[first_code:first_code]=support
    nb.cells=result
    for index,cell in enumerate(nb.cells):
        cell.id=hashlib.sha256((stem+'\n'+str(index)+'\n'+cell.source).encode()).hexdigest()[:12]
        if cell.cell_type=='code':
            cell.metadata.pop('tags',None)
            ast.parse('\n'.join(line for line in cell.source.splitlines() if not line.startswith('%')))
            assert 'colombia_energy' not in cell.source
    nb.metadata['inline_analysis_sources']=catalog.hashes
    return nb
