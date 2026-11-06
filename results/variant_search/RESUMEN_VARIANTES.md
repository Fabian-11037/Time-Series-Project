# Resumen de la búsqueda de variantes

Finalizada el 6 de noviembre de 2026 a las 00:10, hora de Colombia. 4800 ajustes completos, 192 configuraciones, cinco folds y cinco semillas. Duración: 11 h 20 min aproximadamente. Prueba no reevaluada.

| Familia | Configuración | MAE medio ± DE | RMSE medio | R² medio | Mejor época mediana |
|---|---|---:|---:|---:|---:|
| CNN1D | C3_h24_l2_0.0001 | 24.155 ± 0.144 | 37.604 | 0.8766 | 23 |
| LSTM | L2_h72_l2_0.001 | 24.624 ± 0.101 | 37.773 | 0.8755 | 22 |
| MLP | M3_h24_l2_0.001 | 24.992 ± 0.095 | 37.953 | 0.8743 | 18 |

MAE/RMSE en COP/kWh. Por semilla se agrupan las horas de validación de los cinco folds; luego se promedian las cinco métricas. La DE corresponde a inicializaciones. R² de las tres configuraciones ganadoras se recalculó desde sus predicciones, al igual que sus MAE por fold/semilla. Se verificaron 4800 claves únicas y 192 filas de resumen.

Configuración ganadora global: C3, dos convoluciones de 64 filtros, kernel 5, ReLU y Dropout1d=0.1, pooling a siete posiciones y salida densa de 24 valores con Softplus. Historia de 24 horas y Ridge explícito lambda=1e-4.

Las métricas son de selección: el bloque de validación también se utilizó para parada anticipada y selección entre 192 configuraciones. Pueden ser optimistas; no son métricas de prueba ni resultados confirmatorios. Las semillas no reflejan incertidumbre temporal. La prueba 2022–2025 fue consultada anteriormente para las configuraciones del piloto y no se volvió a consultar en esta búsqueda. No trasladar sus R² de prueba a estos nuevos ganadores.

El apagado condicionado registró poweroff_requested después de finalizar y guardar los resultados. Este registro confirma la solicitud de apagado, no constituye por sí solo prueba del apagado físico.
