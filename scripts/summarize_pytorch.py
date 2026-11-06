"""Verifica los artefactos del piloto y escribe el informe sin leer prueba."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / (sys.argv[1] if len(sys.argv)>1 else 'results/pilot_pytorch_gfx1030')
config = json.loads((out/'configuration.json').read_text())
rows = pd.read_csv(out/'metrics.csv')
assert len(rows)==75 and not rows.duplicated(['family','fold','seed']).any()
assert json.loads((out/'completed.json').read_text())['test_evaluated'] is False
assert hashlib.sha256((ROOT/config['protocol']).read_bytes()).hexdigest()==config['protocol_sha256']
for name, digest in json.loads((out/'source_hashes.json').read_text()).items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
manifest = []
for r in rows.itertuples():
    folder = out/r.family/f'fold_{r.fold}_seed_{r.seed}'
    with np.load(folder/'predictions.npz') as p:
        y, pred = p['actual'], p['predictions']
        assert y.shape == pred.shape and y.shape[1]==24
        assert np.isfinite(pred).all()
        assert pd.to_datetime(p['origins_ns'], utc=True).max()<pd.Timestamp('2022-01-01',tz='America/Bogota')
        error = pred.astype(np.float64)-y
        assert np.isclose(np.abs(error).mean(),r.mae)
        assert np.isclose(np.sqrt(np.square(error).mean()),r.rmse)
        assert np.isclose(np.abs(p['weekly']-y).mean(),r.weekly_mae)
    curves = pd.read_csv(folder/'curves.csv')
    assert list(curves.epoch)==list(range(1,31))
    assert np.isfinite(curves.to_numpy()).all()
    assert (folder/'checkpoint.pt').stat().st_size>0
    for name in ['predictions.npz','checkpoint.pt','curves.csv','metrics.json']:
        path = folder/name
        manifest.append(dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(out/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'verification.json').write_text(json.dumps(dict(verified_runs=len(rows),
    verified_artifacts=len(manifest), predictions_recomputed=True,
    epochs_per_run=30, test_evaluated=False, protocol_hash_unchanged=True),indent=2))
s = pd.read_csv(out/'summary.csv').sort_values('mae_mean')
per_seed = pd.read_csv(out/'metrics_per_seed.csv')
lines = ['# Resultados del piloto PyTorch E1', '',
    'Ejecución del 5 de noviembre de 2026. Desarrollo 2000–2021; validaciones consecutivas de 2018–2021. Prueba 2022–2025 sin evaluación.', '',
    'Se completaron 75 ajustes: tres familias, cinco folds expansivos y cinco semillas, con 30 épocas fijas por ajuste. Contexto de 168 horas, horizonte de 24 horas, exclusivamente variables numéricas y calendario.', '',
    '| Modelo | MAE medio ± DE entre semillas (COP/kWh) | RMSE medio (COP/kWh) | MAE / repetición semanal |',
    '|---|---:|---:|---:|']
for r in s.itertuples():
    lines.append(f'| {r.family} | {r.mae_mean:.3f} ± {r.mae_sd_seeds:.3f} | {r.rmse_mean:.3f} | {r.mae_ratio_weekly:.3f} |')
reference = s.weekly_mae.iloc[0]
best = s.iloc[0]
lines += ['', f'La repetición semanal obtuvo MAE {reference:.3f} COP/kWh sobre los mismos orígenes. El menor MAE descriptivo corresponde a {best.family}. La razón respecto a la referencia menor que 1 representa menor error. No es MASE.', '',
    'Para cada semilla se agrupan todas las horas de validación de los cinco folds, ponderando por su cantidad. Luego se promedian esas cinco métricas; la desviación estándar corresponde a inicializaciones, no a incertidumbre temporal. El RMSE de cada semilla se calcula desde los errores cuadrados agrupados, no promediando RMSE de folds.', '',
    '## Desglose temporal', '', '| Fold | Modelo | MAE medio (COP/kWh) | RMSE medio (COP/kWh) | MAE semanal |', '|---|---|---:|---:|---:|']
for (fold,family),g in rows.groupby(['fold','family']):
    lines.append(f'| {fold} | {family} | {g.mae.mean():.3f} | {g.rmse.mean():.3f} | {g.weekly_mae.mean():.3f} |')
lines += ['', '## Ejecución y límites', '',
    f"PyTorch {config['environment']['torch']}, ROCm {config['environment']['hip']}, Python {config['environment']['python'].split()[0]}, AMD Radeon RX 6700 XT (12 GB). Se utilizó `HSA_OVERRIDE_GFX_VERSION=10.3.0`: la GPU real gfx1031 produjo `invalid device function` sin esa variable. El cambio se limitó al proceso. La compatibilidad se verificó mediante operaciones GPU y los entrenamientos; no implica soporte oficial del dispositivo.", '',
    f"Tiempo de ajuste acumulado: {rows.train_seconds.sum()/60:.2f} minutos; no incluye preparación de datos ni inicialización. Parámetros: " + ', '.join(f"{family}: {int(g.n_parameters.iloc[0]):,}" for family,g in rows.groupby('family')) + '.', '',
    'Las entradas y la escala auxiliar del objetivo se ajustaron sólo con entrenamiento de cada fold. El modelo de la época 30 se conservó sin selección por validación. Se guardan pesos, escaladores, curvas, predicciones y métricas. Las métricas se recalcularon desde las predicciones de los 75 ajustes y se verificaron 300 artefactos.', '',
    'Este resultado es exploratorio: faltan la extracción sistemática de arquitecturas de los textos completos, el margen práctico δ, el análisis de potencia y un diseño confirmatorio con dependencia temporal y multiplicidad. No se afirman significancia ni superioridad final, y no se consultó prueba para seleccionar configuraciones. Las series y rezagos conservan las limitaciones retrospectivas descritas en el contexto.', '',
    '## Reproducción', '', 'Desde la raíz del repositorio, con el entorno `mlenv` activado:', '', '```bash',
    'HSA_OVERRIDE_GFX_VERSION=10.3.0 python scripts/train_pytorch.py --output results/pilot_pytorch_gfx1030',
    'python scripts/summarize_pytorch.py results/pilot_pytorch_gfx1030', '```', '',
    'El primer comando reanuda ejecuciones completas; una nueva configuración requiere otra carpeta de salida. Las versiones instaladas están en `environment_freeze.txt`; este registro no sustituye el bloqueo del EDA ni exige instalar todo el entorno en otro equipo.', '']
(out/'RESUMEN_RESULTADOS.md').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines[:14]))

# Figura estática exportable: las bandas representan semillas, no intervalos temporales.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
colors={'MLP':'#3274a1','LSTM':'#218c74','CNN1D':'#c77821'}
x=np.arange(len(s))
axes[0].bar(x,s.mae_mean,yerr=s.mae_sd_seeds,capsize=5,
    color=[colors[f] for f in s.family])
axes[0].axhline(reference,color='#555555',linestyle='--',label=f'Semanal: {reference:.2f}')
axes[0].set_xticks(x,s.family)
axes[0].set_ylabel('MAE (COP/kWh)')
axes[0].set_title('Promedio ± DE entre cinco semillas')
axes[0].legend(frameon=False)
for family,g in rows.groupby('family'):
    agg=g.groupby('fold').mae.agg(['mean','std'])
    axes[1].plot(agg.index,agg['mean'],marker='o',label=family,color=colors[family])
    axes[1].fill_between(agg.index,agg['mean']-agg['std'],agg['mean']+agg['std'],
        alpha=.12,color=colors[family])
weekly=rows.groupby('fold').weekly_mae.first()
axes[1].plot(weekly.index,weekly.values,linestyle='--',color='#555555',label='Semanal')
axes[1].set_xticks(range(1,6))
axes[1].set_xlabel('Fold temporal de validación')
axes[1].set_ylabel('MAE (COP/kWh)')
axes[1].set_title('Resultados por bloque temporal')
axes[1].legend(frameon=False)
for ax in axes:
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y',alpha=.15)
fig.suptitle('Piloto E1 · 75 ajustes · prueba 2022–2025 sin evaluar')
fig.savefig(out/'comparacion_modelos.png',dpi=170)
plt.close(fig)
