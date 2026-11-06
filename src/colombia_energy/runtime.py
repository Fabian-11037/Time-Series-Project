"""Dispositivo y bloqueo de ejecución para Windows y Linux."""
from contextlib import contextmanager
from pathlib import Path
import os
import platform
import random
import sys
import numpy as np
import torch


def select_device(requested='auto'):
    """Auto usa CUDA/ROCm si está disponible; CPU en caso contrario."""
    requested = requested.lower()
    if requested == 'cpu':
        return torch.device('cpu')
    if requested in ('auto', 'gpu'):
        if torch.cuda.is_available():
            return torch.device('cuda:0')
        if requested == 'auto':
            return torch.device('cpu')
        raise RuntimeError('GPU solicitada pero PyTorch no detecta CUDA/ROCm. Use --device cpu o instale una distribución compatible.')
    try:
        device = torch.device(requested)
    except (RuntimeError, ValueError) as exc:
        raise ValueError('Dispositivo válido: auto, cpu, gpu, cuda o cuda:N.') from exc
    if device.type != 'cuda':
        raise ValueError('Dispositivo válido: auto, cpu, gpu, cuda o cuda:N.')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA/ROCm no disponible; use --device cpu.')
    index = 0 if device.index is None else device.index
    if index < 0 or index >= torch.cuda.device_count():
        raise ValueError(f'Índice GPU fuera de rango: {index}.')
    return torch.device(f'cuda:{index}')


def synchronize_device(device):
    if torch.device(device).type == 'cuda':
        torch.cuda.synchronize(device)


def seed_training(seed, device):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.device(device).type == 'cuda':
        torch.cuda.manual_seed_all(seed)


def runtime_environment(device, threads):
    device = torch.device(device)
    environment = dict(platform=platform.platform(), os_name=os.name,
        python=sys.version, torch=torch.__version__, numpy=np.__version__,
        device=str(device), threads=threads, cuda=torch.version.cuda,
        hip=torch.version.hip, cpu=platform.processor(),
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        hip_override=os.environ.get('HSA_OVERRIDE_GFX_VERSION'))
    environment['backend'] = ('rocm' if torch.version.hip else 'cuda') if device.type == 'cuda' else 'cpu'
    if device.type == 'cuda':
        environment.update(gpu=torch.cuda.get_device_name(device),
            gpu_memory_bytes=torch.cuda.get_device_properties(device).total_memory)
    return environment


@contextmanager
def exclusive_run(path):
    """Bloqueo no bloqueante, liberado incluso si la ejecución falla."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open('a+b')
    locked = False
    try:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            raise RuntimeError(f'Ya hay una ejecución activa para {path.parent}.') from exc
        yield
    finally:
        if locked:
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()
