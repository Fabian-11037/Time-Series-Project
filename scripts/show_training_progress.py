"""Barra de progreso de la búsqueda; --watch refresca sin interacción con el modelo."""
import argparse,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');args=p.parse_args()
path=Path(__file__).resolve().parents[1]/'results/variant_search/status.json'
while True:
    try:
        s=json.loads(path.read_text());d=s['completed'];n=s['total'];filled=int(30*d/n)
        c=s.get('current',{})
        print(f"\r[{'█'*filled}{'░'*(30-filled)}] {d}/{n} ({100*d/n:.2f}%) · {s['state']} · "
            f"{c.get('configuration','')} · fold {c.get('fold','-')} · semilla {c.get('seed','-')} · "
            f"época {c.get('epoch','-')} · mejor MAE {c.get('best_mae','-')}      ",end='\n' if not args.watch else '',flush=True)
        if not args.watch or s['state'] in ['Completado','Error']:
            if args.watch:print()
            break
    except FileNotFoundError:
        if not args.watch:print('Inicializando');break
    time.sleep(5)
