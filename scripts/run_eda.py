"""Ejecuta cuadernos y construye el libro desde los datos versionados."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import faulthandler

ROOT=Path(__file__).resolve().parents[1]
for key,sub in [('MPLCONFIGDIR','mpl'),('JUPYTER_RUNTIME_DIR','jupyter'),('IPYTHONDIR','ipython'),('TEMP','temp'),('TMP','temp')]:
    p=ROOT/'tmp'/sub;p.mkdir(parents=True,exist_ok=True);os.environ[key]=str(p)
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.environ['PYTHONUTF8']='1'

def main(chapters=None,build=True,execute=True):
    if os.name=='nt':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    trace=(ROOT/'tmp/execution_trace.log').open('w',encoding='utf-8')
    faulthandler.dump_traceback_later(90,repeat=True,file=trace)
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client.kernelspec import KernelSpecManager
    kernels=ROOT/'tmp/kernels/python3';kernels.mkdir(parents=True,exist_ok=True)
    (kernels/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Python 3',language='python')),encoding='utf-8')
    manager=KernelSpecManager(kernel_dirs=[str(kernels.parent)])
    from jupyter_client import AsyncKernelManager
    class LocalKernelManager(AsyncKernelManager):
        def __init__(self,*args,**kwargs):
            kwargs['kernel_spec_manager']=manager
            super().__init__(*args,**kwargs)
    log=ROOT/'results/notebook_execution.json'
    previous={r['notebook']:r for r in json.loads(log.read_text(encoding='utf-8'))} if log.exists() else {}
    records=[]
    for path in (sorted((ROOT/'book').glob('*.ipynb')) if execute else []):
        if chapters and path.stem not in chapters:continue
        start=time.perf_counter();print('Ejecutando '+path.name,flush=True)
        nb=nbformat.read(path,as_version=4)
        client=NotebookClient(nb,timeout=1800,kernel_name='python3',resources={'metadata':{'path':str(ROOT/'book')}},kernel_manager_class=LocalKernelManager)
        client.execute();nbformat.write(nb,path)
        errors=[out for cell in nb.cells if cell.cell_type=='code' for out in cell.get('outputs',[]) if out.output_type=='error']
        assert not errors
        records.append(dict(notebook=path.name,seconds=round(time.perf_counter()-start,3),code_cells=sum(c.cell_type=='code' for c in nb.cells),errors=0))
        previous[path.name]=records[-1]
        (ROOT/'results').mkdir(exist_ok=True)
        log.write_text(json.dumps(list(previous.values()),indent=2),encoding='utf-8')
        print('Completado '+path.name+' '+str(records[-1]['seconds'])+' s',flush=True)
    out=ROOT/'results';out.mkdir(exist_ok=True)
    (out/'notebook_execution.json').write_text(json.dumps(list(previous.values()),indent=2),encoding='utf-8')
    if build:
        from jupyter_book.cli.main import main as book_cli
        book_cli(['build',str(ROOT/'book'),'--warningiserror','--keep-going'],standalone_mode=False)
        shutil.copytree(ROOT/'book/_build/html',ROOT/'docs',dirs_exist_ok=True)
        (ROOT/'docs/.nojekyll').touch()
    faulthandler.cancel_dump_traceback_later();trace.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--chapters',nargs='*');p.add_argument('--no-build',action='store_true');p.add_argument('--build-only',action='store_true');a=p.parse_args()
    main(a.chapters,not a.no_build,not a.build_only)
