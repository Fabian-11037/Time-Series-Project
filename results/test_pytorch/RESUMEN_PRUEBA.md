# Evaluación de prueba de los tres modelos

Fecha: 5 de noviembre de 2026. Evaluación autorizada explícitamente por el usuario después del piloto. Arquitecturas, hiperparámetros y cinco semillas congelados antes de consultar prueba. Los 15 modelos se reentrenaron desde cero durante 30 épocas con desarrollo 2000–2021; todos los checkpoints se guardaron antes de abrir prueba.

Prueba: 2022–2025, 1461 orígenes diarios y 35064 horas por semilla. Pronóstico diario de las próximas 24 horas con contexto de 168 horas y pesos fijos. Los orígenes posteriores incorporan observaciones pasadas de prueba disponibles según rezagos de 24 horas y dos días, sin actualizar pesos ni escaladores. No es un único pronóstico a cuatro años.

| Modelo | R² medio ± DE | MAE medio ± DE (COP/kWh) | RMSE medio ± DE (COP/kWh) |
|---|---:|---:|---:|
| CNN1D | 0.8151 ± 0.0033 | 81.618 ± 0.868 | 155.206 ± 1.402 |
| MLP | 0.7925 ± 0.0167 | 96.453 ± 5.286 | 164.332 ± 6.449 |
| LSTM | 0.6726 ± 0.0066 | 101.644 ± 1.533 | 206.538 ± 2.084 |

Referencia semanal: MAE 133.636, RMSE 235.198 COP/kWh; R² 0.5754.

Se reportan medias y desviaciones estándar entre cinco semillas; no se eligió la mejor semilla ni se promediaron predicciones como ensemble. R² se calcula sobre todas las horas concatenadas de prueba. La variación entre semillas no representa incertidumbre temporal.

CNN1D presenta el menor error descriptivo entre las redes. Los errores absolutos son mayores que en validación; el R² depende también de la variabilidad del objetivo y no permite comparar directamente la dificultad de ambos periodos. No se realizaron ajustes a partir de estos resultados ni pruebas de significancia.

El periodo de prueba ya fue consultado: no debe volver a tratarse como prueba intacta para futuros ajustes. Permanecen pendientes los requisitos confirmatorios bibliográficos y estadísticos del E1. Las limitaciones de datos retrospectivos y rezagos supuestos siguen vigentes.

Artefactos: `configuration.json`, `preprocessing.json`, `metrics_per_seed.csv`, `summary.csv`, referencia semanal, curvas, checkpoints, predicciones y manifiesto de 60 archivos. Las métricas de los 15 ajustes se recalcularon desde sus predicciones. El protocolo es `PROTOCOLO_PRUEBA_2026-11-05.md`; la entrada separada es `scripts/evaluate_test_pytorch.py --evaluate-test`, que impide repetir automáticamente una prueba ya abierta.
