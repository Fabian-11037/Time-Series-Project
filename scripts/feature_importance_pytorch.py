"""Importancia post hoc por permutación de trayectorias en último fold de validación."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
import torch
from train_pytorch import ROOT, Forecaster
from colombia_energy.pipeline import build_training_pipeline, load_pipeline_config, prepare_fold_arrays
from colombia_energy.runtime import select_device, runtime_environment

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', default='auto', help='auto, cpu, gpu, cuda o cuda:N')
    parser.add_argument('--output',default='results/feature_importance_pytorch_portable')
    parser.add_argument('--checkpoint-dir',default='results/pilot_pytorch_gfx1030')
    args = parser.parse_args()
    device = select_device(args.device)
    torch.set_num_threads(4)
    out = ROOT / args.output
    out.mkdir(exist_ok=True, parents=True)
    (out/'environment.json').write_text(json.dumps(runtime_environment(device,4),indent=2),encoding='utf-8')
    pipeline = build_training_pipeline(load_pipeline_config())
    batch = prepare_fold_arrays(pipeline, pipeline['folds'][-1])
    names = batch['feature_names']
    groups = {n: [i] for i, n in enumerate(names) if n not in ['hour_sin', 'hour_cos', 'week_sin', 'week_cos', 'year_sin', 'year_cos']}
    for k in ['hour', 'week', 'year']:
        groups['calendar_' + k] = [names.index(k + '_sin'), names.index(k + '_cos')]
    x = torch.as_tensor(batch['X_validation'], device=device)
    y = batch['y_validation'].astype(np.float64)
    rng = np.random.default_rng(11037)
    permutations = [torch.tensor(rng.permutation(len(x)), device=device) for _ in range(3)]
    rows = []
    for family in ['MLP', 'LSTM', 'CNN1D']:
        for seed in range(11037, 11042):
            path = ROOT / args.checkpoint_dir / family / f'fold_5_seed_{seed}/checkpoint.pt'
            ck = torch.load(path, map_location=device, weights_only=False)
            model = Forecaster(family, len(names), 24).to(device)
            model.load_state_dict(ck['state_dict'])
            model.eval()

            def predict(z):
                with torch.no_grad():
                    return (torch.cat([model(b) for b in z.split(256)]) * ck['target_std'] + ck['target_mean']).cpu().numpy()
            baseline = predict(x)
            with np.load(path.parent / 'predictions.npz') as saved:
                np.testing.assert_allclose(baseline, saved['predictions'], rtol=1e-05, atol=0.001)
            base = float(np.abs(baseline - y).mean())
            for variable, columns in groups.items():
                for repeat, order in enumerate(permutations):
                    xp = x.clone()
                    for col in columns:
                        xp[:, :, col] = x[order, :, col]
                    mae = float(np.abs(predict(xp) - y).mean())
                    rows.append(dict(family=family, seed=seed, repeat=repeat, variable=variable, baseline_mae=base, permuted_mae=mae, delta_mae=mae - base))
            print(f'{family} semilla {seed} completada', flush=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(out / 'importance_runs.csv', index=False)
    means = frame.groupby(['family', 'seed', 'variable']).delta_mae.mean().reset_index()
    summary = means.groupby(['family', 'variable']).delta_mae.agg(['mean', 'std']).reset_index()
    summary = summary.sort_values(['family', 'mean'], ascending=[True, False])
    summary.to_csv(out / 'importance_summary.csv', index=False)
    meta = dict(fold=5, validation_start=str(batch['validation_origins'][0]), validation_last_origin=str(batch['validation_origins'][-1]), n_origins=len(x), n_features=len(names), groups=groups, seeds=list(range(11037, 11042)), repetitions=3, permutation='Trayectoria completa de 168 horas intercambiada entre orígenes; seno/coseno permutados juntos', test_consulted=False, models_refitted=False)
    (out / 'method.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    lines = ['# Importancia por permutación en validación', '', f"Último fold: {meta['validation_start']} a {meta['validation_last_origin']}; {len(x)} orígenes. Modelos del piloto, cinco semillas, tres permutaciones por variable y semilla. No se modificaron pesos ni se consultó prueba.", '', 'Se intercambia entre orígenes la trayectoria completa de 168 horas de una variable, preservando el orden dentro de cada trayectoria. Los pares seno/coseno del calendario se permutan conjuntamente. Importancia = MAE permutado − MAE original, en COP/kWh. Mayor valor indica mayor dependencia predictiva en este bloque. Se promedian primero las tres repeticiones y después las cinco semillas; DE corresponde a semillas.', '', 'La permutación puede romper correlaciones y crear combinaciones poco habituales. Variables correlacionadas pueden compartir o esconder importancia. No es causalidad, significancia estadística ni una medida de dispersión de la variable. El calendario horario es idéntico entre ventanas diarias y esta permutación no puede medir su importancia. Este diagnóstico se limita al último fold de validación y no atribuye importancia a los modelos finales reentrenados con todo desarrollo.', '']
    for family in ['MLP', 'LSTM', 'CNN1D']:
        lines += [f'## {family}', '', '| Variable | Aumento MAE | DE entre semillas |', '|---|---:|---:|']
        for r in summary[summary.family == family].head(10).itertuples():
            lines.append(f'| {r.variable} | {r.mean:.4f} | {r.std:.4f} |')
        lines.append('')
    (out / 'IMPORTANCIA.md').write_text('\n'.join(lines), encoding='utf-8')
    print(summary.groupby('family').head(5).to_string(index=False))
if __name__ == '__main__':
    main()
