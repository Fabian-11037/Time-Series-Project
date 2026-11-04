# Clima horario de ocho ciudades: descarga completa 2000–2025

Auditoría: 2026-11-03T19:18:20.551457-05:00 (hora colombiana).

Resultado: **APROBADO**.

| Ciudad | Horas recibidas | Horas faltantes | Claves duplicadas | Nulos/no numéricos |
|---|---:|---:|---:|---:|
| Bogota | 227,928 | 0 | 0 | 0 |
| Medellin | 227,928 | 0 | 0 | 0 |
| Cali | 227,928 | 0 | 0 | 0 |
| Barranquilla | 227,928 | 0 | 0 | 0 |
| Cartagena | 227,928 | 0 | 0 | 0 |
| Bucaramanga | 227,928 | 0 | 0 | 0 |
| Pereira | 227,928 | 0 | 0 | 0 |
| Cucuta | 227,928 | 0 | 0 | 0 |

Se buscaron 227.928 horas por ciudad, para 1.823.424 combinaciones ciudad-hora y **5.470.272 valores numéricos** en tres variables. Se auditan los 312 meses para cada ciudad y variable: 7.488 comprobaciones mensuales.

## Entregables

- `clima_ocho_ciudades_horario_2000_2025.csv`: 227.928 filas horarias esperadas y 24 columnas numéricas, tres por ciudad.
- `cities/`: ocho archivos individuales con hora, temperatura, humedad relativa y precipitación.
- `raw/`: 26 respuestas anuales originales comprimidas, con URL, parámetros, fecha de recuperación y SHA-256.
- `grid_metadata.json`: coordenadas solicitadas y de la celda utilizada, elevación y unidades por ciudad y año.
- `coverage_by_month.csv`, `audit.json` e `issues.json`: detalle verificable del control de calidad.

## Interpretación temporal y espacial

La temperatura a 2 m (°C) y la humedad relativa a 2 m (%) corresponden al instante indicado. **La precipitación en mm es la suma de la hora precedente**, por ejemplo, la etiqueta 01:00 representa 00:00–01:00. Se conserva esa etiqueta y se explicita en el nombre `precipitation_preceding_hour_mm`; no se desplaza para aparentar que la lluvia futura era conocida al iniciar la hora.

Se solicitó expresamente `models=era5` en todas las consultas, con zona America/Bogota, unidades Celsius/mm y las mismas ocho coordenadas investigadas. Se conserva la selección de celda terrestre y el ajuste de elevación predeterminados de Open-Meteo, con sus metadatos. Son datos de una celda asociada al punto de cada ciudad, **no una media espacial municipal ni mediciones directas de una estación**.

Se conserva cada valor recibido. No se rellenan huecos, eliminan duplicados o interpolan observaciones para aprobar la auditoría. Los controles de rango se registran en `audit.json`.

ERA5 es un reanálisis retrospectivo. Tener calendario completo no certifica que esta versión estuviera disponible en la fecha original. Para pronóstico operativo se requieren reglas de disponibilidad y rezagos documentados. La temperatura/humedad/lluvia realizadas del horizonte futuro no son covariables conocidas.

Fuente y atribución: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), basado en ERA5 de ECMWF/Copernicus. Condiciones: [licencia y términos de Open-Meteo](https://open-meteo.com/en/terms). Conservación de la fuente y fecha de recuperación en los metadatos.
