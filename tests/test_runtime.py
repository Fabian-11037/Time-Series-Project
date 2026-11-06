"""Pruebas de ejecución, sin descargar datos ni abrir prueba."""
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
HAS_TORCH=importlib.util.find_spec('torch') is not None
if HAS_TORCH:
    import torch
    from colombia_energy.runtime import exclusive_run, runtime_environment, seed_training, select_device, synchronize_device
    from train_pytorch import Forecaster
    from train_variants import ARCHITECTURES, Variant, ridge_penalty


@unittest.skipUnless(HAS_TORCH,'Instalar requirements-pytorch-cpu.txt para validar entrenamiento')
class RuntimeTests(unittest.TestCase):
    def test_device_selection_and_explicit_gpu_failure(self):
        with patch('torch.cuda.is_available',return_value=False):
            self.assertEqual(str(select_device('auto')),'cpu')
            self.assertEqual(str(select_device('cpu')),'cpu')
            for name in ['gpu','cuda','cuda:0']:
                with self.assertRaises(RuntimeError):select_device(name)
        with patch('torch.cuda.is_available',return_value=True),patch('torch.cuda.device_count',return_value=2):
            self.assertEqual(str(select_device('gpu')),'cuda:0')
            self.assertEqual(str(select_device('cuda:1')),'cuda:1')
            with self.assertRaises(ValueError):select_device('cuda:2')
        with self.assertRaises(ValueError):select_device('incorrecto')

    def test_cpu_environment_and_synchronization(self):
        with patch('torch.cuda.synchronize') as sync,patch('torch.cuda.get_device_name') as gpu:
            synchronize_device('cpu')
            result=runtime_environment('cpu',1)
            sync.assert_not_called();gpu.assert_not_called()
        self.assertEqual(result['backend'],'cpu')
        self.assertEqual(result['device'],'cpu')

    def test_cross_process_lock_and_exception_release(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'runner.lock'
            program="from pathlib import Path\nfrom colombia_energy.runtime import exclusive_run\nimport sys\ntry:\n with exclusive_run(Path(sys.argv[1])): pass\nexcept RuntimeError:\n sys.exit(23)\n"
            env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
            with exclusive_run(path):
                result=subprocess.run([sys.executable,'-c',program,str(path)],env=env,capture_output=True,timeout=40)
                self.assertEqual(result.returncode,23,result.stderr.decode(errors='replace'))
            with self.assertRaisesRegex(ValueError,'interrupción'):
                with exclusive_run(path):raise ValueError('interrupción')
            with exclusive_run(path):pass

    def train_and_reload(self,device):
        previous=torch.get_num_threads();torch.set_num_threads(1)
        try:
            models=[(Forecaster(f,37,24),168,False) for f in ['MLP','LSTM','CNN1D']]
            models += [(Variant(a,24,37),24,True) for a in ARCHITECTURES]
            for model,length,positive in models:
                with self.subTest(model=type(model).__name__,length=length,device=str(device)):
                    seed_training(11037,device)
                    model=model.to(device)
                    x=torch.randn(4,length,37,device=device)
                    target=torch.rand(4,24,device=device)
                    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
                    before=[p.detach().clone() for p in model.parameters()]
                    model.train();optimizer.zero_grad()
                    loss=(model(x)-target).abs().mean()+1e-5*ridge_penalty(model)
                    self.assertTrue(torch.isfinite(loss));loss.backward()
                    self.assertTrue(all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()))
                    optimizer.step()
                    self.assertTrue(any(not torch.equal(p,b) for p,b in zip(model.parameters(),before)))
                    model.eval()
                    with torch.no_grad():predicted=model(x)
                    self.assertEqual(predicted.shape,(4,24))
                    self.assertTrue(torch.isfinite(predicted).all())
                    if positive:self.assertTrue((predicted>=0).all())
                    buffer=io.BytesIO();torch.save(model.state_dict(),buffer);buffer.seek(0)
                    cpu_state=torch.load(buffer,map_location='cpu',weights_only=True)
                    model=model.cpu();model.load_state_dict(cpu_state)
                    with torch.no_grad():reloaded=model(x.cpu())
                    torch.testing.assert_close(reloaded,predicted.cpu(),rtol=1e-4,atol=1e-5)
            synchronize_device(device)
        finally:torch.set_num_threads(previous)

    def test_cpu_training_all_architectures_and_checkpoint(self):
        self.train_and_reload(select_device('cpu'))

    @unittest.skipUnless(HAS_TORCH and torch.cuda.is_available(),'GPU CUDA/ROCm no disponible')
    def test_gpu_training_all_architectures_and_cpu_checkpoint(self):
        self.train_and_reload(select_device('gpu'))

    def test_archived_experiment_sources_match_historical_hashes(self):
        import hashlib,json
        manifest=json.loads((ROOT/'resources/experiment_sources/manifest.json').read_text(encoding='utf-8'))
        for entry in manifest.values():
            self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(),entry['sha256'])
        config=json.loads((ROOT/'results/variant_search/configuration.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['train_variants']['sha256'],config['source_sha256'])

    def test_model_mathematics_unchanged_from_archived_sources(self):
        import ast
        for module,names in [('train_variants',{'Variant','EarlyStop','ridge_penalty'}),('train_pytorch',{'Forecaster'})]:
            original=ast.parse((ROOT/f'resources/experiment_sources/{module}_2026-11-05.py').read_text(encoding='utf-8'))
            current=ast.parse((ROOT/f'scripts/{module}.py').read_text(encoding='utf-8'))
            old={n.name:ast.dump(n,include_attributes=False) for n in original.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names}
            new={n.name:ast.dump(n,include_attributes=False) for n in current.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names}
            self.assertEqual(old,new)

    def test_previous_test_stays_blocked_before_any_data_load(self):
        import evaluate_test_pytorch as entry
        with patch.object(sys,'argv',['evaluate_test_pytorch.py','--evaluate-test','--device','cpu']),patch.object(entry,'load_numeric',side_effect=AssertionError('No abrir datos')) as load:
            with self.assertRaisesRegex(RuntimeError,'Prueba ya consultada'):entry.main()
            load.assert_not_called()

    def test_search_runner_on_cpu_with_synthetic_development(self):
        import contextlib,json
        from types import SimpleNamespace
        import numpy as np
        import pandas as pd
        from sklearn.preprocessing import StandardScaler
        import train_variants as entry
        config=entry.search_config()
        config.update(lookbacks=[24],ridge=[0.],seeds=[11037])
        base={'config':config['pipeline'],'folds':[{'fold':1}]}
        rng=np.random.default_rng(11037)
        scaler=StandardScaler().fit(rng.normal(size=(10,3)))
        batch=dict(fold=1,X_train=rng.normal(size=(4,24,3)).astype('float32'),
            y_train=rng.uniform(1,3,size=(4,24)).astype('float32'),
            X_validation=rng.normal(size=(2,24,3)).astype('float32'),
            y_validation=rng.uniform(1,3,size=(2,24)).astype('float32'),
            train_origins=pd.date_range('2001-01-01',periods=4,tz='America/Bogota'),
            validation_origins=pd.date_range('2018-01-01',periods=2,tz='America/Bogota'),
            feature_scaler=scaler,feature_names=['a','b','c'],
            scaler_fit_start='2000-01-01',scaler_fit_end='2000-12-31')
        original_stop=entry.EarlyStop
        previous=torch.get_num_threads();torch.set_num_threads(1)
        try:
            with tempfile.TemporaryDirectory() as directory,patch.object(entry,'search_config',return_value=config),patch.object(entry,'build_training_pipeline',return_value=base),patch.object(entry,'prepare_fold_arrays',return_value=batch),patch.object(entry,'ARCHITECTURES',{'M1':entry.ARCHITECTURES['M1']}),patch.object(entry,'EarlyStop',side_effect=lambda:original_stop(patience=0,min_epochs=1)),contextlib.redirect_stdout(io.StringIO()):
                out=Path(directory)
                entry.run_search(SimpleNamespace(threads=1),out,select_device('cpu'))
                self.assertEqual(json.loads((out/'environment.json').read_text())['backend'],'cpu')
                self.assertTrue((out/'runs/M1_h24_l2_0/fold_1_seed_11037/checkpoint.pt').exists())
                self.assertEqual(len(pd.read_csv(out/'metrics.csv')),1)
        finally:torch.set_num_threads(previous)

    def test_frozen_output_configuration_rejected_without_data_load(self):
        from types import SimpleNamespace
        import train_variants as entry
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);path=out/'configuration.json';path.write_text('{"frozen": true}',encoding='utf-8')
            original=path.read_bytes()
            with patch.object(entry,'build_training_pipeline',side_effect=AssertionError('No cargar datos')) as load:
                with self.assertRaisesRegex(RuntimeError,'Configuración/fuentes'):
                    entry.run_search(SimpleNamespace(threads=1),out,select_device('cpu'))
                load.assert_not_called()
            self.assertEqual(path.read_bytes(),original)


if __name__=='__main__':unittest.main()
