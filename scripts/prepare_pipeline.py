"""Prepara folds y escaladores; el entrenamiento supervisado se incorpora mediante callbacks."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from colombia_energy.pipeline import load_pipeline_config,build_training_pipeline,pipeline_fold_summary,prepare_fold_arrays

def main(plan_only=False):
    config=load_pipeline_config();pipeline=build_training_pipeline(config)
    output=ROOT/'results/pipeline';output.mkdir(parents=True,exist_ok=True)
    summary=pipeline_fold_summary(pipeline)
    summary.to_csv(output/'folds.csv')
    arrays={}
    for fold in pipeline['folds']:
        arrays[f"train_{fold['fold']}"]=fold['train_origins']
        arrays[f"validation_{fold['fold']}"]=fold['validation_origins']
    np.savez_compressed(output/'fold_indices.npz',**arrays)
    preprocessors=[]
    if not plan_only:
        for fold in pipeline['folds']:
            batch=prepare_fold_arrays(pipeline,fold);scaler=batch['feature_scaler']
            preprocessors.append(dict(fold=fold['fold'],scaler='StandardScaler',
                feature_names=batch['feature_names'],mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),
                var=scaler.var_.tolist(),n_samples_seen=int(scaler.n_samples_seen_),
                fit_start=str(batch['scaler_fit_start']),fit_end=str(batch['scaler_fit_end']),
                X_train_shape=list(batch['X_train'].shape),y_train_shape=list(batch['y_train'].shape),
                X_validation_shape=list(batch['X_validation'].shape),y_validation_shape=list(batch['y_validation'].shape)))
            print('Preparado fold '+str(fold['fold']),flush=True)
            del batch
    (output/'preprocessors.json').write_text(json.dumps(preprocessors,indent=2),encoding='utf-8')
    report=dict(config=config,folds=len(pipeline['folds']),feature_names=list(pipeline['features'].columns),
        development_rows=len(pipeline['features']),backend='timeseries-cv 0.1.5 / split_train_val_forwardChaining',
        backend_scope='calendar_blocks',models_trained=False,test_values_read=False,
        test_manifest_sha256=hashlib.sha256((ROOT/'data/test_freeze.json').read_bytes()).hexdigest(),
        fitted_preprocessors=len(preprocessors))
    (output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(summary[['train_start','train_end_exclusive','validation_start','validation_end_exclusive','train_windows','validation_windows']].to_string())

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--plan-only',action='store_true');main(parser.parse_args().plan_only)
