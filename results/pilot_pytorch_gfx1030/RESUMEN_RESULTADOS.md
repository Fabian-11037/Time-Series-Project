# Resultados del piloto PyTorch E1

Ejecución del 5 de noviembre de 2026. Desarrollo 2000–2021; validaciones consecutivas de 2018–2021. Prueba 2022–2025 sin evaluación.

Se completaron 75 ajustes: tres familias, cinco folds expansivos y cinco semillas, con 30 épocas fijas por ajuste. Contexto de 168 horas, horizonte de 24 horas, exclusivamente variables numéricas y calendario.

| Modelo | MAE medio ± DE entre semillas (COP/kWh) | RMSE medio (COP/kWh) | MAE / repetición semanal |
|---|---:|---:|---:|
| CNN1D | 25.307 ± 0.189 | 38.529 | 0.630 |
| LSTM | 26.382 ± 0.453 | 40.155 | 0.657 |
| MLP | 32.024 ± 0.991 | 46.789 | 0.797 |

La repetición semanal obtuvo MAE 40.157 COP/kWh sobre los mismos orígenes. El menor MAE descriptivo corresponde a CNN1D. La razón respecto a la referencia menor que 1 representa menor error. No es MASE.

Para cada semilla se agrupan todas las horas de validación de los cinco folds, ponderando por su cantidad. Luego se promedian esas cinco métricas; la desviación estándar corresponde a inicializaciones, no a incertidumbre temporal. El RMSE de cada semilla se calcula desde los errores cuadrados agrupados, no promediando RMSE de folds.

## Desglose temporal

| Fold | Modelo | MAE medio (COP/kWh) | RMSE medio (COP/kWh) | MAE semanal |
|---|---|---:|---:|---:|
| 1 | CNN1D | 15.824 | 23.212 | 20.015 |
| 1 | LSTM | 15.909 | 23.523 | 20.015 |
| 1 | MLP | 18.462 | 25.761 | 20.015 |
| 2 | CNN1D | 27.146 | 37.733 | 43.176 |
| 2 | LSTM | 28.099 | 39.261 | 43.176 |
| 2 | MLP | 37.332 | 49.714 | 43.176 |
| 3 | CNN1D | 40.197 | 55.798 | 66.662 |
| 3 | LSTM | 44.611 | 59.569 | 66.662 |
| 3 | MLP | 54.107 | 69.354 | 66.662 |
| 4 | CNN1D | 24.859 | 36.814 | 43.641 |
| 4 | LSTM | 24.272 | 36.570 | 43.641 |
| 4 | MLP | 30.286 | 42.627 | 43.641 |
| 5 | CNN1D | 18.541 | 31.498 | 27.360 |
| 5 | LSTM | 19.056 | 32.877 | 27.360 |
| 5 | MLP | 19.979 | 33.967 | 27.360 |

## Ejecución y límites

PyTorch 2.9.1+rocm6.4, ROCm 6.4.43484-123eb5128, Python 3.12.3, AMD Radeon RX 6700 XT (12 GB). Se utilizó `HSA_OVERRIDE_GFX_VERSION=10.3.0`: la GPU real gfx1031 produjo `invalid device function` sin esa variable. El cambio se limitó al proceso. La compatibilidad se verificó mediante operaciones GPU y los entrenamientos; no implica soporte oficial del dispositivo.

Tiempo de ajuste acumulado: 5.43 minutos; no incluye preparación de datos ni inicialización. Parámetros: CNN1D: 16,504, LSTM: 9,880, MLP: 805,592.

Las entradas y la escala auxiliar del objetivo se ajustaron sólo con entrenamiento de cada fold. El modelo de la época 30 se conservó sin selección por validación. Se guardan pesos, escaladores, curvas, predicciones y métricas. Las métricas se recalcularon desde las predicciones de los 75 ajustes y se verificaron 300 artefactos.

Este resultado es exploratorio: faltan la extracción sistemática de arquitecturas de los textos completos, el margen práctico δ, el análisis de potencia y un diseño confirmatorio con dependencia temporal y multiplicidad. No se afirman significancia ni superioridad final, y no se consultó prueba para seleccionar configuraciones. Las series y rezagos conservan las limitaciones retrospectivas descritas en el contexto.

## Reproducción

Desde la raíz del repositorio, con el entorno `mlenv` activado:

```bash
HSA_OVERRIDE_GFX_VERSION=10.3.0 python scripts/train_pytorch.py --output results/pilot_pytorch_gfx1030
python scripts/summarize_pytorch.py results/pilot_pytorch_gfx1030
```

El primer comando reanuda ejecuciones completas; una nueva configuración requiere otra carpeta de salida. Las versiones instaladas están en `environment_freeze.txt`; este registro no sustituye el bloqueo del EDA ni exige instalar todo el entorno en otro equipo.

## R² de validación

Se concatenan las predicciones de los cinco folds y las 24 horas de cada origen para cada semilla. R² = 1 − SSE/SST respecto a la media global de las etiquetas de validación; luego se calcula media y desviación estándar entre cinco semillas. No es el promedio de R² por fold ni por horizonte.

| Modelo | R² medio | DE entre semillas |
|---|---:|---:|
| CNN1D | 0.870421 | 0.001241 |
| LSTM | 0.859229 | 0.004404 |
| MLP | 0.808848 | 0.007975 |
