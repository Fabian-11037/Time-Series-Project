"""Comprobaciones de arquitectura, regularización y parada previas a la búsqueda."""
import torch
from train_variants import Variant,ARCHITECTURES,EarlyStop,ridge_penalty

torch.set_num_threads(2)
for code in ARCHITECTURES:
 for lookback in [24,72,168,336]:
  model=Variant(code,lookback,37)
  p=model(torch.randn(2,lookback,37))
  assert p.shape==(2,24) and torch.isfinite(p).all() and (p>=0).all()
  (p.mean()+1e-4*ridge_penalty(model)).backward()
  assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in model.parameters())
m=torch.nn.Linear(3,2);before=ridge_penalty(m).item()
with torch.no_grad():m.bias.add_(100)
assert abs(ridge_penalty(m).item()-before)<1e-6
stop=EarlyStop();assert stop.update(100.,1)==(True,False)
stop.update(99.9,2);assert stop.stale==1
stop.update(99.7,3);assert stop.stale==0
for epoch in range(4,20):_,halt=stop.update(99.7,epoch);assert not halt
assert stop.update(99.7,20)[1]
assert stop.best_epoch==3
print('OK: 48 formas de entrada, salidas positivas, gradientes, Ridge sin sesgos y parada anticipada.')
