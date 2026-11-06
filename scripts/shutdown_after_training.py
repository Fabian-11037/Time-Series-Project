"""Apagado solicitado por el usuario sólo después de completar y guardar la búsqueda."""
import csv,fcntl,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/variant_search'
CANCEL=OUT/'cancel_shutdown'

def status(state,**extra):
    path=OUT/'shutdown_status.json';tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(state=state,watcher_pid=os.getpid(),updated_at=time.time(),**extra),indent=2))
    tmp.replace(path)

def read(path):return json.loads(path.read_text())

def complete():
    if not (OUT/'completed.json').exists():return False
    info=read(OUT/'completed.json');progress=read(OUT/'status.json')
    if info['runs']!=4800 or progress['completed']!=4800 or progress['state']!='Completado':
        raise RuntimeError('Conteos de finalización inconsistentes; se cancela el apagado')
    config=read(OUT/'configuration.json')
    with (OUT/'metrics.csv').open() as f:rows=list(csv.DictReader(f))
    keys={(r['candidate'],int(r['fold']),int(r['seed'])) for r in rows}
    if len(rows)!=4800 or len(keys)!=4800:raise RuntimeError('Métricas incompletas o duplicadas')
    with (OUT/'summary.csv').open() as f:
        if len(list(csv.DictReader(f)))!=192:raise RuntimeError('Resumen incompleto')
    with (OUT/'metrics_per_seed.csv').open() as f:
        if len(list(csv.DictReader(f)))!=960:raise RuntimeError('Resumen por semilla incompleto')
    for candidate,fold,seed in keys:
        folder=OUT/'runs'/candidate/f'fold_{fold}_seed_{seed}'
        for name in ['metrics.json','checkpoint.pt','predictions.npz','curves.csv']:
            if not (folder/name).is_file() or (folder/name).stat().st_size==0:
                raise RuntimeError(f'Artefacto incompleto: {folder/name}')
    return True

def main():
    lock=(OUT/'shutdown_watcher.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    status('armed',condition='4800 ajustes, resúmenes y artefactos guardados; luego 60 segundos de espera')
    while True:
        if CANCEL.exists():status('cancelled');return
        if complete():break
        progress=read(OUT/'status.json')
        if progress['state']=='Error':status('cancelled_training_error',error=progress.get('error'));return
        pid=progress['pid']
        try:os.kill(pid,0)
        except ProcessLookupError:status('cancelled_training_stopped');return
        time.sleep(15)
    status('countdown',seconds=60)
    for _ in range(12):
        if CANCEL.exists():status('cancelled');return
        time.sleep(5)
    if not complete():raise RuntimeError('La finalización ya no es válida')
    os.sync()
    status('poweroff_requested')
    result=subprocess.run(['/usr/bin/systemctl','poweroff','--no-ask-password'],capture_output=True,text=True)
    if result.returncode:status('poweroff_failed',returncode=result.returncode,error=result.stderr)

if __name__=='__main__':
    try:main()
    except Exception as e:status('error_no_shutdown',error=str(e));raise
