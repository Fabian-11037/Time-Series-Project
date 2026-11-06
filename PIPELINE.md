# Pipeline de entrenamiento

La configuración activa está en `configs/training_pipeline.json`. El método es `split_train_val_forwardChaining`, con entrenamiento expansivo y cinco bloques consecutivos de validación dentro de 2000–2021. El periodo 2022–2025 está reservado para prueba.

## Preparar

```bash
python scripts/prepare_pipeline.py
```

Se generan el plan de folds, índices, parámetros de escalado y auditoría en `results/pipeline/`. Las dimensiones de entrada son `(n,168,p)` y las de salida `(n,24)`. Las etiquetas permanecen en COP/kWh. Los rezagos de publicación supuestos se configuran por separado para datos horarios e hidrología.

## Incorporar modelos

```python
from colombia_energy.pipeline import (
    load_pipeline_config,
    build_training_pipeline,
    run_forward_chaining,
)

pipeline = build_training_pipeline(load_pipeline_config())

# Implementar estas tres funciones con el modelo elegido:
# model_factory(*, seed, n_features, horizon) -> modelo nuevo
# fit_model(modelo, batch, *, seed) -> modelo ajustado (o None)
# evaluate_model(modelo, batch) -> diccionario de métricas

# results = run_forward_chaining(
#     pipeline, model_factory, fit_model, evaluate_model, seeds=(100,101,102,103,104)
# )
```

Cada `batch` contiene `X_train`, `y_train`, `X_validation`, `y_validation`, fechas de origen, nombres de variables y el escalador ajustado en ese fold. El MLP puede aplanar la entrada; LSTM y CNN1D conservan la dimensión temporal. El callback debe devolver predicciones de las 24 horas para los mismos orígenes. Las métricas se calculan en las unidades declaradas del objetivo.

Se crea una instancia nueva por fold y semilla. `model_factory` debe inicializar los generadores aleatorios de Python, NumPy y el framework utilizado antes de construir el modelo. La preparación no carga los valores de prueba. El ajuste de modelos, su búsqueda, pérdida, métricas y margen práctico deben preregistrarse antes de ejecutarse. La función callback proporciona una extensión del pipeline; las tres familias tienen una implementación exploratoria en `scripts/train_pytorch.py`, con resultados en `results/pilot_pytorch_gfx1030/RESUMEN_RESULTADOS.md`. El benchmark confirmatorio sigue pendiente.

## Función de referencia

Se utiliza la función de timeseries-cv 0.1.5 incorporada en `src/colombia_energy/forward_chaining.py`, con atribución y licencia en `third_party/timeseries-cv/`. El backend opera sobre identificadores de bloques; las ventanas horarias se construyen y purgan posteriormente. Esta separación evita materializar todas las ventanas repetidamente en el backend original.

La distribución publicada emplea los argumentos `numInputs`, `numOutputs`, `numJumps`. Sus ejemplos web utilizan otros nombres. La integración ya contiene la llamada compatible y no necesita instalar el paquete completo, cuya restricción NumPy <2 difiere del entorno fijado del proyecto.

El capítulo 8 incluye el código del pipeline, los cortes efectivos y un ejemplo ejecutado de preparación. Los contrastes anteriores entre 2000–2017 y 2018–2021 se mantienen como diagnósticos del EDA.

## Piloto PyTorch ejecutado

Véase `PROTOCOLO_PILOTO_2026-11-05.md`. Con el entorno confirmado por el usuario (`mlenv`) activo y acceso a la GPU AMD:

```bash
HSA_OVERRIDE_GFX_VERSION=10.3.0 python scripts/train_pytorch.py --output results/pilot_pytorch_gfx1030
python scripts/summarize_pytorch.py results/pilot_pytorch_gfx1030
```

El override corresponde a la ejecución local en RX 6700 XT; no es una exigencia para otras GPUs. No se cambia a CPU silenciosamente. La ejecución reanuda los ajustes completos; los cambios de configuración requieren otra carpeta. Se completaron 75 ajustes con prueba intacta. El bloqueo original del EDA se conserva; las versiones del piloto están en `environment_freeze.txt` dentro de sus resultados.

## Evaluación de prueba autorizada

El 5 de noviembre de 2026 se reentrenaron los tres modelos con desarrollo completo y se evaluaron cinco semillas por familia en prueba por solicitud explícita del usuario. Entrada separada: `scripts/evaluate_test_pytorch.py --evaluate-test`. Resultados y reglas de evaluación diaria con pesos fijos: `results/test_pytorch/RESUMEN_PRUEBA.md`; registro previo: `PROTOCOLO_PRUEBA_2026-11-05.md`. El script bloquea repeticiones automáticas una vez iniciada la consulta. Para auditar los artefactos existentes, ejecutar `python scripts/summarize_test_pytorch.py`. Prueba ya no está sin consultar; los accesos de EDA/piloto siguen bloqueados.

## Búsqueda de variantes con Dropout fijo

Iniciada el5de noviembre de2026. Registro: `PROTOCOLO_VARIANTES_2026-11-05.md`. Script reanudable: `scripts/train_variants.py`,192configuraciones y4800ajustes, sólo desarrollo, salida positiva Softplus y parada anticipada. Estado vivo: `results/variant_search/status.json`; URL/PID del panel local: `results/variant_search/processes.json`. La barra de consola se obtiene con `python scripts/show_training_progress.py --watch`. No lanzar una copia mientras otra ejecución tenga el bloqueo. Las métricas de selección con parada sobre validación no son una evaluación externa independiente.
