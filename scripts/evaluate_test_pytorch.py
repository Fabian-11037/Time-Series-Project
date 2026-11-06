"""Reentrena en desarrollo y evalúa prueba sólo con autorización explícita."""
import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.preprocessing import StandardScaler
from train_pytorch import Forecaster, ROOT
from colombia_energy.pipeline import build_training_pipeline, numeric_feature_frame
from colombia_energy.data import load_numeric, TARGET
from colombia_energy.runtime import select_device, synchronize_device, seed_training, runtime_environment

def windows(features, target, config, start=None):
    origins = np.arange(config['lookback_hours'], len(features) - config['horizon_hours'] + 1, 24)
    flags = np.isfinite(features.to_numpy()).all(axis=1)
    bad = np.r_[0, np.cumsum(~flags)]
    origins = origins[bad[origins] - bad[origins - 168] == 0]
    good = np.r_[0, np.cumsum(~np.isfinite(target.to_numpy()))]
    origins = origins[good[origins + 24] - good[origins] == 0]
    if start is not None:
        origins = origins[features.index[origins] >= start]
    return origins

def score(y, p):
    err = p.astype(np.float64) - y.astype(np.float64)
    return dict(mae=float(np.abs(err).mean()), rmse=float(np.sqrt(np.square(err).mean())), r2=float(1 - np.square(err).sum() / np.square(y.astype(np.float64) - y.mean(dtype=np.float64)).sum()))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evaluate-test', action='store_true', required=True)
    parser.add_argument('--device', default='auto', help='auto, cpu, gpu, cuda o cuda:N')
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error('--threads debe ser positivo')
    out = ROOT / 'results/test_pytorch'
    out.mkdir(exist_ok=True, parents=True)
    if (out / 'test_access_started.json').exists() or (out / 'completed.json').exists():
        raise RuntimeError('Prueba ya consultada: no se repite automáticamente esta evaluación.')
    config = json.loads((ROOT / 'results/pilot_pytorch_gfx1030/configuration.json').read_text(encoding='utf-8'))
    protocol = ROOT / 'PROTOCOLO_PRUEBA_2026-11-05.md'
    frozen = dict(pilot_configuration=config, protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(), script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), architecture_sha256=hashlib.sha256((ROOT / 'scripts/train_pytorch.py').read_bytes()).hexdigest())
    (out / 'configuration.json').write_text(json.dumps(frozen, indent=2), encoding='utf-8')
    device = select_device(args.device)
    torch.set_num_threads(args.threads)
    (out / 'environment.json').write_text(json.dumps(runtime_environment(device, args.threads), indent=2), encoding='utf-8')
    started = time.perf_counter()
    pipeline = build_training_pipeline(config['pipeline'])
    features, target = (pipeline['features'], pipeline['target'])
    origins = windows(features, target, config['pipeline'])
    positions = origins[:, None] - 168 + np.arange(168)
    fit_rows = np.unique(positions)
    scaler = StandardScaler().fit(features.iloc[fit_rows])
    assert features.index[fit_rows].max() < pd.Timestamp('2022-01-01', tz='America/Bogota')
    assert features.index[origins[-1]] + pd.Timedelta(hours=24) <= pd.Timestamp('2022-01-01', tz='America/Bogota')
    scaled = scaler.transform(features).astype(np.float32)
    X = scaled[positions]
    y = target.to_numpy()[origins[:, None] + np.arange(24)].astype(np.float32)
    mean, std = (float(y.mean()), float(y.std()))
    xg = torch.as_tensor(X, device=device)
    yg = torch.as_tensor((y - mean) / std, device=device)
    audit = dict(train_windows=len(origins), feature_names=list(features.columns), scaler_fit_start=str(features.index[fit_rows[0]]), scaler_fit_end=str(features.index[fit_rows[-1]]), train_label_end_exclusive=str(features.index[origins[-1]] + pd.Timedelta(hours=24)), feature_mean=scaler.mean_.tolist(), feature_scale=scaler.scale_.tolist(), target_mean=mean, target_std=std)
    (out / 'preprocessing.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    training = []
    for family in config['families']:
        for seed in config['seeds']:
            seed_training(seed, device)
            model = Forecaster(family, X.shape[-1], 24).to(device)
            optimizer = torch.optim.Adam(model.parameters(), lr=config['lr'], weight_decay=config['weight_decay'])
            folder = out / family / f'seed_{seed}'
            folder.mkdir(parents=True, exist_ok=True)
            curves = []
            synchronize_device(device)
            t0 = time.perf_counter()
            for epoch in range(1, 31):
                model.train()
                total = 0.0
                for ix in torch.randperm(len(xg), device=device).split(256):
                    optimizer.zero_grad(set_to_none=True)
                    loss = nn.functional.l1_loss(model(xg[ix]), yg[ix])
                    if not torch.isfinite(loss):
                        raise FloatingPointError('Pérdida no finita')
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    total += float(loss.detach()) * len(ix)
                curves.append(dict(epoch=epoch, train_mae_cop_kwh=total / len(xg) * std))
            synchronize_device(device)
            elapsed = time.perf_counter() - t0
            torch.save(dict(state_dict=model.state_dict(), family=family, seed=seed, n_features=X.shape[-1], horizon=24, preprocessing=audit), folder / 'checkpoint.pt')
            pd.DataFrame(curves).to_csv(folder / 'curves.csv', index=False)
            training.append(dict(family=family, seed=seed, train_seconds=elapsed))
            print(f'Entrenado {family} semilla={seed}', flush=True)
            del model, optimizer
    del xg, yg, X, scaled
    pd.DataFrame(training).to_csv(out / 'training.csv', index=False)
    (out / 'test_access_started.json').write_text(json.dumps(dict(checkpoints_saved=15, fixed_epochs=30, configuration_sha256=hashlib.sha256((out / 'configuration.json').read_bytes()).hexdigest())), encoding='utf-8')
    hourly = pd.concat([load_numeric('train'), load_numeric('validation'), load_numeric('test', allow_test=True)]).sort_index()
    hydro = pd.concat([load_numeric('train', 'hydrology'), load_numeric('validation', 'hydrology'), load_numeric('test', 'hydrology', allow_test=True)]).sort_index()
    feature_config = dict(config['pipeline'], development_end_exclusive=config['pipeline']['test_end_exclusive'])
    full = numeric_feature_frame(hourly, hydro, feature_config)
    assert list(full.columns) == list(features.columns)
    np.testing.assert_allclose(full.loc[features.index].to_numpy(), features.to_numpy(), equal_nan=True)
    test_origins = windows(full, hourly[TARGET], feature_config, pd.Timestamp('2022-01-01', tz='America/Bogota'))
    expected = pd.date_range('2022-01-01', '2025-12-31', freq='D', tz='America/Bogota')
    assert full.index[test_origins].equals(expected.rename(full.index.name)), 'Prueba incompleta'
    xp = test_origins[:, None] - 168 + np.arange(168)
    assert np.all(xp.max(axis=1) < test_origins)
    used = np.unique(xp)
    tx = scaler.transform(full.iloc[used]).astype(np.float32)[np.searchsorted(used, xp)]
    ty = hourly[TARGET].to_numpy()[test_origins[:, None] + np.arange(24)].astype(np.float32)
    weekly = hourly[TARGET].to_numpy()[test_origins[:, None] + np.arange(24) - 168]
    reference = score(ty, weekly)
    (out / 'weekly_reference.json').write_text(json.dumps(reference, indent=2), encoding='utf-8')
    txg = torch.as_tensor(tx, device=device)
    rows = []
    for run in training:
        family, seed = (run['family'], run['seed'])
        folder = out / family / f'seed_{seed}'
        checkpoint = torch.load(folder / 'checkpoint.pt', map_location=device, weights_only=False)
        model = Forecaster(family, tx.shape[-1], 24).to(device)
        model.load_state_dict(checkpoint['state_dict'])
        model.eval()
        with torch.no_grad():
            pred = torch.cat([model(z) for z in txg.split(256)]).cpu().numpy() * std + mean
        assert np.isfinite(pred).all()
        np.savez_compressed(folder / 'predictions.npz', origins_ns=full.index[test_origins].asi8, timezone='America/Bogota', actual=ty, predictions=pred, weekly=weekly)
        metrics = dict(family=family, seed=seed, **score(ty, pred), n_values=ty.size)
        (folder / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
        rows.append(metrics)
        print(json.dumps(metrics), flush=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(out / 'metrics_per_seed.csv', index=False)
    summary = frame.groupby('family').agg(mae=('mae', 'mean'), mae_sd=('mae', 'std'), rmse=('rmse', 'mean'), rmse_sd=('rmse', 'std'), r2=('r2', 'mean'), r2_sd=('r2', 'std'))
    summary.to_csv(out / 'summary.csv')
    (out / 'completed.json').write_text(json.dumps(dict(runs=15, test_windows=len(test_origins), test_hours=ty.size, total_seconds=time.perf_counter() - started, test_evaluated=True), indent=2), encoding='utf-8')
    print(summary.to_string(), flush=True)
if __name__ == '__main__':
    main()
