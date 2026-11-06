"""Audita y resume la evaluación de prueba sin reentrenar ni volver a inferir."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/test_pytorch'
summary=pd.read_csv(out/'summary.csv')
rows=pd.read_csv(out/'metrics_per_seed.csv')
assert len(rows)==15 and not rows.duplicated(['family','seed']).any()
manifest=[]
for r in rows.itertuples():
    folder=out/r.family/f'seed_{r.seed}'
    with np.load(folder/'predictions.npz') as a:
        y=a['actual'].astype(np.float64);p=a['predictions'].astype(np.float64)
        assert y.shape==p.shape==(1461,24) and np.isfinite(p).all()
        dates=pd.to_datetime(a['origins_ns'],utc=True).tz_convert('America/Bogota')
        assert dates.equals(pd.date_range('2022-01-01','2025-12-31',tz='America/Bogota',freq='D'))
        err=y-p
        assert np.isclose(abs(err).mean(),r.mae)
        assert np.isclose(np.sqrt(np.square(err).mean()),r.rmse)
        assert np.isclose(1-np.square(err).sum()/np.square(y-y.mean()).sum(),r.r2)
    curve=pd.read_csv(folder/'curves.csv');assert curve.epoch.tolist()==list(range(1,31))
    for name in ['checkpoint.pt','curves.csv','predictions.npz','metrics.json']:
        path=folder/name
        manifest.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
config=json.loads((out/'configuration.json').read_text())
assert hashlib.sha256((ROOT/'PROTOCOLO_PRUEBA_2026-11-05.md').read_bytes()).hexdigest()==config['protocol_sha256']
assert hashlib.sha256((ROOT/'scripts/evaluate_test_pytorch.py').read_bytes()).hexdigest()==config['script_sha256']
assert hashlib.sha256((ROOT/'scripts/train_pytorch.py').read_bytes()).hexdigest()==config['architecture_sha256']
(out/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'verification.json').write_text(json.dumps(dict(verified_runs=15,verified_artifacts=60,
    test_days=1461,test_hours=35064,metrics_recomputed=True,protocol_unchanged=True),indent=2))
reference=json.loads((out/'weekly_reference.json').read_text())
lines=['# Evaluación de prueba de los tres modelos','',
    'Fecha: 5 de noviembre de 2026. Evaluación autorizada explícitamente por el usuario después del piloto. Arquitecturas, hiperparámetros y cinco semillas congelados antes de consultar prueba. Los 15 modelos se reentrenaron desde cero durante 30 épocas con desarrollo 2000–2021; todos los checkpoints se guardaron antes de abrir prueba.','',
    'Prueba: 2022–2025, 1461 orígenes diarios y 35064 horas por semilla. Pronóstico diario de las próximas 24 horas con contexto de 168 horas y pesos fijos. Los orígenes posteriores incorporan observaciones pasadas de prueba disponibles según rezagos de 24 horas y dos días, sin actualizar pesos ni escaladores. No es un único pronóstico a cuatro años.','',
    '| Modelo | R² medio ± DE | MAE medio ± DE (COP/kWh) | RMSE medio ± DE (COP/kWh) |',
    '|---|---:|---:|---:|']
for r in summary.sort_values('mae').itertuples():
    lines.append(f'| {r.family} | {r.r2:.4f} ± {r.r2_sd:.4f} | {r.mae:.3f} ± {r.mae_sd:.3f} | {r.rmse:.3f} ± {r.rmse_sd:.3f} |')
lines+=['',f"Referencia semanal: MAE {reference['mae']:.3f}, RMSE {reference['rmse']:.3f} COP/kWh; R² {reference['r2']:.4f}.",'',
    'Se reportan medias y desviaciones estándar entre cinco semillas; no se eligió la mejor semilla ni se promediaron predicciones como ensemble. R² se calcula sobre todas las horas concatenadas de prueba. La variación entre semillas no representa incertidumbre temporal.','',
    'CNN1D presenta el menor error descriptivo entre las redes. Los errores absolutos son mayores que en validación; el R² depende también de la variabilidad del objetivo y no permite comparar directamente la dificultad de ambos periodos. No se realizaron ajustes a partir de estos resultados ni pruebas de significancia.','',
    'El periodo de prueba ya fue consultado: no debe volver a tratarse como prueba intacta para futuros ajustes. Permanecen pendientes los requisitos confirmatorios bibliográficos y estadísticos del E1. Las limitaciones de datos retrospectivos y rezagos supuestos siguen vigentes.','',
    'Artefactos: `configuration.json`, `preprocessing.json`, `metrics_per_seed.csv`, `summary.csv`, referencia semanal, curvas, checkpoints, predicciones y manifiesto de 60 archivos. Las métricas de los 15 ajustes se recalcularon desde sus predicciones. El protocolo es `PROTOCOLO_PRUEBA_2026-11-05.md`; la entrada separada es `scripts/evaluate_test_pytorch.py --evaluate-test`, que impide repetir automáticamente una prueba ya abierta.','']
(out/'RESUMEN_PRUEBA.md').write_text('\n'.join(lines))
print('\n'.join(lines[6:13]))
