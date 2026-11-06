"""Búsqueda reanudable en desarrollo; ninguna ruta de acceso a prueba."""
import argparse, copy, fcntl, hashlib, html, itertools, json, os, random, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from colombia_energy.pipeline import build_training_pipeline, load_pipeline_config, prepare_fold_arrays

ARCHITECTURES={
 'M1':dict(family='MLP',widths=[64,32]),'M2':dict(family='MLP',widths=[128,64]),
 'M3':dict(family='MLP',widths=[256,128]),'M4':dict(family='MLP',widths=[128,64,32]),
 'L1':dict(family='LSTM',hidden=32,layers=1,dense=False),
 'L2':dict(family='LSTM',hidden=64,layers=1,dense=False),
 'L3':dict(family='LSTM',hidden=32,layers=2,dense=False),
 'L4':dict(family='LSTM',hidden=64,layers=1,dense=True),
 'C1':dict(family='CNN1D',channels=32,kernel=5,dilations=[1,1]),
 'C2':dict(family='CNN1D',channels=32,kernel=3,dilations=[1,1]),
 'C3':dict(family='CNN1D',channels=64,kernel=5,dilations=[1,1]),
 'C4':dict(family='CNN1D',channels=32,kernel=3,dilations=[1,2,4])}

class Variant(nn.Module):
    def __init__(self, architecture, lookback, n_features, dropout=.1):
        super().__init__();a=ARCHITECTURES[architecture];self.family=a['family']
        if self.family=='MLP':
            layers=[nn.Flatten()];previous=lookback*n_features
            for width in a['widths']:
                layers += [nn.Linear(previous,width),nn.ReLU(),nn.Dropout(dropout)];previous=width
            self.net=nn.Sequential(*layers,nn.Linear(previous,24))
        elif self.family=='LSTM':
            self.net=nn.LSTM(n_features,a['hidden'],num_layers=a['layers'],batch_first=True,
                dropout=dropout if a['layers']>1 else 0.)
            layers=[nn.Dropout(dropout)]
            if a['dense']:layers += [nn.Linear(a['hidden'],32),nn.ReLU(),nn.Dropout(dropout)]
            self.head=nn.Sequential(*layers,nn.Linear(32 if a['dense'] else a['hidden'],24))
        else:
            layers=[];previous=n_features
            for dilation in a['dilations']:
                layers += [nn.Conv1d(previous,a['channels'],a['kernel'],
                    dilation=dilation,padding=dilation*(a['kernel']-1)//2),nn.ReLU(),nn.Dropout1d(dropout)]
                previous=a['channels']
            self.net=nn.Sequential(*layers,nn.AdaptiveAvgPool1d(7),nn.Flatten(),nn.Linear(previous*7,24))
        self.positive=nn.Softplus()
    def forward(self,x):
        if self.family=='LSTM':
            sequence,_=self.net(x);z=self.head(sequence[:,-1])
        else:z=self.net(x.transpose(1,2) if self.family=='CNN1D' else x)
        return self.positive(z) # Precio / escala positiva, sin centrado.

def ridge_penalty(model):
    return sum(p.square().sum() for p in model.parameters() if p.ndim>1)

class EarlyStop:
    def __init__(self,relative=.002,patience=15,min_epochs=20):
        self.relative=relative;self.patience=patience;self.min_epochs=min_epochs
        self.reference=float('inf');self.best=float('inf');self.best_epoch=0;self.stale=0
    def update(self,value,epoch):
        best=value<self.best
        if best:self.best=value;self.best_epoch=epoch
        if value < self.reference*(1-self.relative):self.reference=value;self.stale=0
        else:self.stale+=1
        return best,epoch>=self.min_epochs and self.stale>=self.patience

def atomic_json(path,data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False));tmp.replace(path)

def publish(out,status):
    status['updated_at']=pd.Timestamp.now(tz='America/Bogota').isoformat()
    atomic_json(out/'status.json',status)
    done=status['completed'];total=status['total'];percent=100*done/total
    current=status.get('current',{})
    description=' · '.join(f'{k}: {v}' for k,v in current.items())
    page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="refresh" content="5"><title>Entrenamiento E1</title><style>body{{font:18px system-ui;background:#101820;color:#edf3f5;max-width:900px;margin:60px auto;padding:24px}}progress{{width:100%;height:34px;accent-color:#39c99a}}p{{line-height:1.6}}small{{color:#acbac4}}code{{overflow-wrap:anywhere}}h1{{font-size:28px}}</style><h1>Entrenamiento de variantes E1</h1><p>{html.escape(status['state'])}</p><progress value="{done}" max="{total}"></progress><p><strong>{done:,} / {total:,} ajustes · {percent:.2f}%</strong></p><p>{html.escape(description)}</p><p>Dropout 0,1 · 192 configuraciones · 5 folds · 5 semillas<br>Parada: MAE de validación, mejora 0,2%, paciencia 15, mínimo 20, máximo 200 épocas.<br>Salida positiva Softplus · Ridge explícito · Sin consultar prueba.</p><small>Actualización: {html.escape(status['updated_at'])} · Refresco cada 5 segundos</small></html>'''
    tmp=out/'progress.tmp';tmp.write_text(page);tmp.replace(out/'progress.html')

def search_config():
    return dict(architectures=ARCHITECTURES,lookbacks=[24,72,168,336],ridge=[0.,1e-5,1e-4,1e-3],
        dropout=.1,seeds=list(range(11037,11042)),n_folds=5,max_epochs=200,min_epochs=20,
        patience=15,relative_improvement=.002,batch_size=256,lr=.001,weight_decay=0.,
        target='price / train standard deviation, no centering',output='Softplus',
        pipeline=load_pipeline_config(),protocol_sha256=hashlib.sha256((ROOT/'PROTOCOLO_VARIANTES_2026-11-05.md').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='results/variant_search')
    args=parser.parse_args();out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
    lock=(out/'runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config=search_config()
    if (out/'configuration.json').exists() and json.loads((out/'configuration.json').read_text())!=config:
        raise RuntimeError('Configuración/fuentes modificadas: usar otra carpeta')
    atomic_json(out/'configuration.json',config)
    total=12*4*4*5*5
    rows=[json.loads(p.read_text()) for p in sorted(out.glob('runs/*/*/metrics.json'))]
    done=len(rows);started=time.time()
    status=dict(state='Preparando datos',completed=done,total=total,pid=os.getpid(),started_at=pd.Timestamp.now(tz='America/Bogota').isoformat())
    publish(out,status)
    try:
        if not torch.cuda.is_available():raise RuntimeError('Se requiere GPU')
        torch.set_num_threads(4)
        atomic_json(out/'environment.json',dict(python=sys.version,torch=torch.__version__,numpy=np.__version__,
            hip=torch.version.hip,gpu=torch.cuda.get_device_name(0),hip_override=os.environ.get('HSA_OVERRIDE_GFX_VERSION')))
        base=build_training_pipeline(dict(config['pipeline'],lookback_hours=336))
        manifest=[]
        for lookback in config['lookbacks']:
            pipeline=dict(base,config=dict(base['config'],lookback_hours=lookback))
            for fold in base['folds']:
                batch=prepare_fold_arrays(pipeline,fold)
                scaler=batch['feature_scaler']
                audit=dict(lookback=lookback,fold=batch['fold'],n_train=len(batch['y_train']),n_validation=len(batch['y_validation']),
                    train_origins_sha256=hashlib.sha256(batch['train_origins'].asi8.tobytes()).hexdigest(),
                    validation_origins_sha256=hashlib.sha256(batch['validation_origins'].asi8.tobytes()).hexdigest(),
                    feature_names=batch['feature_names'],feature_mean=scaler.mean_.tolist(),feature_scale=scaler.scale_.tolist(),
                    scaler_fit_start=str(batch['scaler_fit_start']),scaler_fit_end=str(batch['scaler_fit_end']),
                    validation_start=str(batch['validation_origins'][0]),validation_last_origin=str(batch['validation_origins'][-1]))
                assert batch['train_origins'][-1]+pd.Timedelta(hours=24)<=batch['validation_origins'][0]
                assert batch['validation_origins'][-1]<pd.Timestamp(config['pipeline']['test_start'])
                prep=out/'preprocessing';prep.mkdir(exist_ok=True)
                atomic_json(prep/f'context_{lookback}_fold_{fold["fold"]}.json',audit)
                manifest.append(audit);atomic_json(out/'fold_audit.json',manifest)
                scale=float(batch['y_train'].std())
                assert scale>0 and np.all(batch['y_train']>=0)
                x=torch.as_tensor(batch['X_train'],device='cuda')
                y=torch.as_tensor(batch['y_train']/scale,device='cuda')
                xv=torch.as_tensor(batch['X_validation'],device='cuda')
                yv=torch.as_tensor(batch['y_validation'],device='cuda')
                for architecture,ridge,seed in itertools.product(ARCHITECTURES,config['ridge'],config['seeds']):
                    candidate=f'{architecture}_h{lookback}_l2_{ridge:g}'
                    run=out/'runs'/candidate/f'fold_{fold["fold"]}_seed_{seed}'
                    if (run/'metrics.json').exists():continue
                    run.mkdir(parents=True,exist_ok=True)
                    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
                    model=Variant(architecture,lookback,x.shape[-1],config['dropout']).to('cuda')
                    optimizer=torch.optim.Adam(model.parameters(),lr=config['lr'],weight_decay=0.)
                    stopper=EarlyStop();curves=[];best_state=None;t0=time.time()
                    for epoch in range(1,201):
                        model.train();train_mae=0.;train_l2=0.
                        for ix in torch.randperm(len(x),device='cuda').split(256):
                            optimizer.zero_grad(set_to_none=True)
                            mae=nn.functional.l1_loss(model(x[ix]),y[ix]);l2=ridge_penalty(model)
                            loss=mae+ridge*l2
                            if not torch.isfinite(loss):raise FloatingPointError(f'Pérdida no finita {candidate}')
                            loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
                            train_mae+=float(mae.detach())*len(ix);train_l2+=float(l2.detach())*len(ix)
                        model.eval()
                        with torch.no_grad():pred=torch.cat([model(z) for z in xv.split(256)])*scale
                        val=float((pred-yv).abs().mean())
                        if not np.isfinite(val):raise FloatingPointError('Validación no finita')
                        improved,stop=stopper.update(val,epoch)
                        if improved:best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
                        curves.append(dict(epoch=epoch,train_mae_cop_kwh=train_mae/len(x)*scale,
                            train_ridge_unweighted=train_l2/len(x),validation_mae_cop_kwh=val))
                        status.update(state='Entrenando',completed=done,current=dict(configuration=candidate,
                            fold=fold['fold'],seed=seed,epoch=epoch,best_epoch=stopper.best_epoch,
                            best_mae=round(stopper.best,4),epochs_without_relevant_gain=stopper.stale))
                        publish(out,status)
                        if epoch%5==0 or stop:pd.DataFrame(curves).to_csv(run/'curves.csv',index=False)
                        if stop:break
                    model.load_state_dict(best_state);model.eval()
                    with torch.no_grad():prediction=(torch.cat([model(z) for z in xv.split(256)])*scale).cpu().numpy()
                    actual=batch['y_validation'];error=prediction.astype(np.float64)-actual
                    assert np.isfinite(prediction).all() and (prediction>=0).all()
                    assert np.isclose(np.abs(error).mean(),stopper.best,rtol=1e-5,atol=1e-3)
                    torch.save(dict(state_dict=best_state,architecture=architecture,lookback=lookback,
                        dropout=.1,ridge=ridge,seed=seed,fold=fold['fold'],target_scale=scale,
                        n_features=x.shape[-1],best_epoch=stopper.best_epoch,preprocessing=audit,
                        output='Softplus'),run/'checkpoint.pt')
                    np.savez_compressed(run/'predictions.npz',predictions=prediction,actual=actual,
                        origins_ns=batch['validation_origins'].asi8,timezone='America/Bogota')
                    pd.DataFrame(curves).to_csv(run/'curves.csv',index=False)
                    metrics=dict(candidate=candidate,architecture=architecture,family=ARCHITECTURES[architecture]['family'],
                        lookback=lookback,ridge=ridge,seed=seed,fold=fold['fold'],epochs=epoch,best_epoch=stopper.best_epoch,
                        mae=float(np.abs(error).mean()),rmse=float(np.sqrt(np.square(error).mean())),
                        n_values=int(error.size),parameters=sum(p.numel() for p in model.parameters()),seconds=time.time()-t0,
                        stop_reason='patience' if stop else 'max_epochs')
                    atomic_json(run/'metrics.json',metrics);rows.append(metrics);done+=1
                    pd.DataFrame(rows).to_csv(out/'metrics.csv',index=False)
                    status.update(completed=done);publish(out,status)
                    print(f'{done}/{total} {candidate} fold={fold["fold"]} seed={seed} best={stopper.best_epoch} stop={epoch} MAE={metrics["mae"]:.4f}',flush=True)
                    del model,optimizer,pred,prediction,best_state
                del x,y,xv,yv,batch
        frame=pd.DataFrame(rows);aggregates=[]
        for (candidate,seed),g in frame.groupby(['candidate','seed']):
            aggregates.append(dict(candidate=candidate,seed=int(seed),mae=float(np.average(g.mae,weights=g.n_values)),
                rmse=float(np.sqrt(np.average(g.rmse**2,weights=g.n_values)))))
        seeds=pd.DataFrame(aggregates);seeds.to_csv(out/'metrics_per_seed.csv',index=False)
        summary=seeds.groupby('candidate').agg(mae=('mae','mean'),mae_sd=('mae','std'),rmse=('rmse','mean')).sort_values('mae')
        summary.to_csv(out/'summary.csv')
        status.update(state='Completado',completed=done,current={});publish(out,status)
        atomic_json(out/'completed.json',dict(runs=done,total_seconds=time.time()-started,test_evaluated=False))
    except BaseException as error:
        status.update(state='Error',error=str(error));publish(out,status);raise

if __name__=='__main__':main()
