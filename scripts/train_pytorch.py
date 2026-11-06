"""Piloto E1 en CPU o GPU: tres familias, cinco folds y cinco semillas; prueba inaccesible."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import pandas as pd
import torch
from torch import nn
from colombia_energy.pipeline import build_training_pipeline, load_pipeline_config, run_forward_chaining
from colombia_energy.runtime import select_device, synchronize_device, seed_training, runtime_environment, exclusive_run

class Forecaster(nn.Module):

    def __init__(self, family, n_features, horizon):
        super().__init__()
        self.family = family
        if family == 'MLP':
            self.net = nn.Sequential(nn.Flatten(), nn.Linear(168 * n_features, 128), nn.ReLU(), nn.Dropout(0.1), nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, horizon))
        elif family == 'LSTM':
            self.net = nn.LSTM(n_features, 32, batch_first=True)
            self.head = nn.Linear(32, horizon)
        elif family == 'CNN1D':
            self.net = nn.Sequential(nn.Conv1d(n_features, 32, 5, padding=2), nn.ReLU(), nn.Conv1d(32, 32, 5, padding=2), nn.ReLU(), nn.AdaptiveAvgPool1d(7), nn.Flatten(), nn.Linear(32 * 7, horizon))
        else:
            raise ValueError(family)

    def forward(self, x):
        if self.family == 'LSTM':
            states, _ = self.net(x)
            return self.head(states[:, -1])
        return self.net(x.transpose(1, 2) if self.family == 'CNN1D' else x)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='results/pilot_pytorch_portable')
    parser.add_argument('--device', default='auto', help='auto, cpu, gpu, cuda o cuda:N')
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error('--threads debe ser positivo')
    device = select_device(args.device)
    torch.set_num_threads(args.threads)
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    with exclusive_run(out / 'runner.lock'):
        run_pilot(out, device, args.threads)

def run_pilot(out, device, threads):
    config = dict(epochs=30, batch_size=256, lr=0.001, weight_decay=0.0001, seeds=list(range(11037, 11042)), families=['MLP', 'LSTM', 'CNN1D'], pipeline=load_pipeline_config(), protocol='PROTOCOLO_PILOTO_2026-11-05.md')
    protocol_bytes = (ROOT / config['protocol']).read_bytes()
    config['protocol_sha256'] = hashlib.sha256(protocol_bytes).hexdigest()
    config['environment'] = runtime_environment(device, threads)
    config['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    config['runtime_sha256'] = hashlib.sha256((ROOT / 'src/colombia_energy/runtime.py').read_bytes()).hexdigest()
    config_path = out / 'configuration.json'
    if config_path.exists() and json.loads(config_path.read_text(encoding='utf-8')) != config:
        raise RuntimeError('La configuración existente difiere; usar otra carpeta de resultados.')
    config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
    print(json.dumps(config['environment']), flush=True)
    pipeline = build_training_pipeline(config['pipeline'])
    all_rows = []
    started = time.perf_counter()
    for family in config['families']:

        def factory(*, seed, n_features, horizon):
            seed_training(seed, device)
            return Forecaster(family, n_features, horizon).to(device)

        def fit(model, batch, *, seed):
            run = out / family / f"fold_{batch['fold']}_seed_{seed}"
            run.mkdir(parents=True, exist_ok=True)
            model.run_path = run
            model.seed = seed
            model.target_mean = float(batch['y_train'].mean())
            model.target_std = float(batch['y_train'].std())
            if model.target_std <= 0:
                raise ValueError('Escala del objetivo degenerada')
            if (run / 'metrics.json').exists():
                state = torch.load(run / 'checkpoint.pt', map_location=device, weights_only=False)
                model.load_state_dict(state['state_dict'])
                model.elapsed = state['train_seconds']
                return model
            x = torch.as_tensor(batch['X_train'], device=device)
            y = torch.as_tensor((batch['y_train'] - model.target_mean) / model.target_std, device=device)
            xv = torch.as_tensor(batch['X_validation'], device=device)
            yv = torch.as_tensor(batch['y_validation'], device=device)
            optimizer = torch.optim.Adam(model.parameters(), lr=config['lr'], weight_decay=config['weight_decay'])
            curves = []
            synchronize_device(device)
            t0 = time.perf_counter()
            for epoch in range(1, config['epochs'] + 1):
                model.train()
                order = torch.randperm(len(x), device=device)
                total = 0.0
                for ix in order.split(config['batch_size']):
                    optimizer.zero_grad(set_to_none=True)
                    loss = nn.functional.l1_loss(model(x[ix]), y[ix])
                    if not torch.isfinite(loss):
                        raise FloatingPointError('Pérdida no finita')
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    total += float(loss.detach()) * len(ix)
                model.eval()
                with torch.no_grad():
                    vp = torch.cat([model(z) for z in xv.split(config['batch_size'])])
                    val_mae = float((vp * model.target_std + model.target_mean - yv).abs().mean())
                curves.append(dict(epoch=epoch, train_mae_cop_kwh=total / len(x) * model.target_std, validation_mae_cop_kwh=val_mae))
                pd.DataFrame(curves).to_csv(run / 'curves.csv', index=False)
            synchronize_device(device)
            model.elapsed = time.perf_counter() - t0
            scaler = batch['feature_scaler']
            torch.save(dict(state_dict=model.state_dict(), family=family, seed=seed, fold=batch['fold'], n_features=x.shape[-1], horizon=y.shape[-1], feature_names=batch['feature_names'], feature_mean=scaler.mean_.tolist(), feature_scale=scaler.scale_.tolist(), target_mean=model.target_mean, target_std=model.target_std, train_seconds=model.elapsed, protocol_sha256=config['protocol_sha256']), run / 'checkpoint.pt')
            return model

        def evaluate(model, batch):
            model.eval()
            with torch.no_grad():
                x = torch.as_tensor(batch['X_validation'], device=device)
                predictions = torch.cat([model(z) for z in x.split(config['batch_size'])])
                predictions = (predictions * model.target_std + model.target_mean).cpu().numpy()
            actual = batch['y_validation']
            if not np.isfinite(predictions).all():
                raise FloatingPointError('Predicciones no finitas')
            offsets = np.arange(24)
            origins = pipeline['features'].index.get_indexer(batch['validation_origins'])
            weekly = pipeline['target'].to_numpy()[origins[:, None] + offsets - 168]
            error = predictions.astype(np.float64) - actual
            reference_error = weekly - actual
            metrics = dict(family=family, mae=float(np.abs(error).mean()), rmse=float(np.sqrt(np.square(error).mean())), weekly_mae=float(np.abs(reference_error).mean()), weekly_rmse=float(np.sqrt(np.square(reference_error).mean())), n_values=int(error.size), n_parameters=sum((p.numel() for p in model.parameters())), train_seconds=model.elapsed)
            metrics['mae_ratio_weekly'] = metrics['mae'] / metrics['weekly_mae']
            np.savez_compressed(model.run_path / 'predictions.npz', origins_ns=batch['validation_origins'].asi8, timezone='America/Bogota', predictions=predictions, actual=actual, weekly=weekly)
            (model.run_path / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
            print(f"{family} fold={batch['fold']} seed={model.seed} MAE={metrics['mae']:.3f} RMSE={metrics['rmse']:.3f} tiempo={model.elapsed:.1f}s", flush=True)
            return metrics
        rows = run_forward_chaining(pipeline, factory, fit, evaluate, seeds=config['seeds'])
        all_rows.extend(rows.to_dict('records'))
        pd.DataFrame(all_rows).to_csv(out / 'metrics.csv', index=False)
    rows = pd.DataFrame(all_rows)
    per_seed = []
    for (family, seed), group in rows.groupby(['family', 'seed']):
        n = group.n_values.to_numpy()
        mae = float(np.average(group.mae, weights=n))
        weekly_mae = float(np.average(group.weekly_mae, weights=n))
        per_seed.append(dict(family=family, seed=int(seed), mae=mae, rmse=float(np.sqrt(np.average(group.rmse ** 2, weights=n))), weekly_mae=weekly_mae, mae_ratio_weekly=mae / weekly_mae))
    pd.DataFrame(per_seed).to_csv(out / 'metrics_per_seed.csv', index=False)
    summary = pd.DataFrame(per_seed).groupby('family').agg(mae_mean=('mae', 'mean'), mae_sd_seeds=('mae', 'std'), rmse_mean=('rmse', 'mean'), weekly_mae=('weekly_mae', 'mean'), mae_ratio_weekly=('mae_ratio_weekly', 'mean'))
    summary.to_csv(out / 'summary.csv')
    (out / 'completed.json').write_text(json.dumps(dict(runs=len(rows), total_seconds=time.perf_counter() - started, test_evaluated=False), indent=2), encoding='utf-8')
    print(summary.to_string(), flush=True)
if __name__ == '__main__':
    main()
