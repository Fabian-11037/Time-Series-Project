# Importancia por permutación en validación

Último fold: 2021-03-15 00:00:00-05:00 a 2021-12-31 00:00:00-05:00; 292 orígenes. Modelos del piloto, cinco semillas, tres permutaciones por variable y semilla. No se modificaron pesos ni se consultó prueba.

Se intercambia entre orígenes la trayectoria completa de 168 horas de una variable, preservando el orden dentro de cada trayectoria. Los pares seno/coseno del calendario se permutan conjuntamente. Importancia = MAE permutado − MAE original, en COP/kWh. Mayor valor indica mayor dependencia predictiva en este bloque. Se promedian primero las tres repeticiones y después las cinco semillas; DE corresponde a semillas.

La permutación puede romper correlaciones y crear combinaciones poco habituales. Variables correlacionadas pueden compartir o esconder importancia. No es causalidad, significancia estadística ni una medida de dispersión de la variable. El calendario horario es idéntico entre ventanas diarias y esta permutación no puede medir su importancia. Este diagnóstico se limita al último fold de validación y no atribuye importancia a los modelos finales reentrenados con todo desarrollo.

## MLP

| Variable | Aumento MAE | DE entre semillas |
|---|---:|---:|
| precio_bolsa_cop_kwh | 35.3280 | 2.5556 |
| aportes_kwh_dia | 2.6227 | 0.1914 |
| reserva_util_kwh | 2.2710 | 0.5869 |
| calendar_year | 1.8645 | 0.7360 |
| calendar_week | 1.5499 | 0.2712 |
| precipitation_preceding_hour_mm_bogota | 0.5486 | 0.1677 |
| relative_humidity_2m_pct_barranquilla | 0.4727 | 0.2392 |
| demanda_real_kwh | 0.2906 | 0.0644 |
| demanda_comercial_kwh | 0.2856 | 0.0753 |
| relative_humidity_2m_pct_cali | 0.2788 | 0.1429 |

## LSTM

| Variable | Aumento MAE | DE entre semillas |
|---|---:|---:|
| precio_bolsa_cop_kwh | 38.4942 | 2.0060 |
| aportes_kwh_dia | 2.7980 | 0.3780 |
| reserva_util_kwh | 2.7971 | 1.7437 |
| calendar_year | 1.5717 | 0.4864 |
| calendar_week | 1.1847 | 0.1943 |
| llenado_valor_original | 0.4026 | 0.7710 |
| relative_humidity_2m_pct_barranquilla | 0.1449 | 0.1282 |
| relative_humidity_2m_pct_pereira | 0.1269 | 0.0935 |
| precipitation_preceding_hour_mm_cali | 0.0750 | 0.0467 |
| precipitation_preceding_hour_mm_barranquilla | 0.0634 | 0.0362 |

## CNN1D

| Variable | Aumento MAE | DE entre semillas |
|---|---:|---:|
| precio_bolsa_cop_kwh | 41.6914 | 0.9472 |
| aportes_kwh_dia | 2.3230 | 0.1778 |
| reserva_util_kwh | 1.7590 | 0.8129 |
| calendar_year | 1.1991 | 0.4788 |
| calendar_week | 1.1156 | 0.3957 |
| relative_humidity_2m_pct_barranquilla | 0.3514 | 0.5336 |
| temperature_2m_c_cartagena | 0.3479 | 0.2048 |
| precipitation_preceding_hour_mm_bogota | 0.2280 | 0.0774 |
| llenado_valor_original | 0.2244 | 0.2607 |
| relative_humidity_2m_pct_cartagena | 0.1173 | 0.0703 |
