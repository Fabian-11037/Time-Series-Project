"""Secciones documentales del protocolo; no ejecuta inferencia ni entrenamiento."""
def benchmark_protocol_cells(root):
    text=(root/'PROTOCOLO_BENCHMARK_2026-11-06.md').read_text(encoding='utf-8')
    first=text.index('## 1. Protocolo del benchmark')
    second=text.index('## 2. Unidad de evaluación e inferencia temporal')
    a=text[first:second].strip().replace('## 1. Protocolo del benchmark','## 8.3 Protocolo del benchmark',1)
    b=text[second:].strip().replace('## 2. Unidad de evaluación e inferencia temporal','## 8.4 Unidad de evaluación e inferencia temporal',1)
    return [a,b]
