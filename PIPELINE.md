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

Se crea una instancia nueva por fold y semilla. `model_factory` debe inicializar los generadores aleatorios de Python, NumPy y el framework utilizado antes de construir el modelo. La preparación no carga los valores de prueba. El ajuste de modelos, su búsqueda, pérdida, métricas y margen práctico deben preregistrarse antes de ejecutarse. La función callback proporciona una extensión del pipeline; los tres modelos aún deben implementarse.

## Función de referencia

Se utiliza la función de timeseries-cv 0.1.5 incorporada en `src/colombia_energy/forward_chaining.py`, con atribución y licencia en `third_party/timeseries-cv/`. El backend opera sobre identificadores de bloques; las ventanas horarias se construyen y purgan posteriormente. Esta separación evita materializar todas las ventanas repetidamente en el backend original.

La distribución publicada emplea los argumentos `numInputs`, `numOutputs`, `numJumps`. Sus ejemplos web utilizan otros nombres. La integración ya contiene la llamada compatible y no necesita instalar el paquete completo, cuya restricción NumPy <2 difiere del entorno fijado del proyecto.

El capítulo 8 incluye el código del pipeline, los cortes efectivos y un ejemplo ejecutado de preparación. Los contrastes anteriores entre 2000–2017 y 2018–2021 se mantienen como diagnósticos del EDA.
