# Descarga completa y auditoría XM: 2000–2025

Auditoría generada: 2026-11-04T00:03:25.871515+00:00.

Resultado de integridad del calendario: **APROBADO**.

Periodo inclusivo: 2000-01-01 a 2025-12-31. Entidad: **Sistema nacional**. Calendario esperado: 9,497 días y 227,928 horas por serie horaria.

| Métrica | Frecuencia | Valores recibidos | Fechas/horas faltantes | Claves duplicadas | Nulos/no válidos |
|---|---|---:|---:|---:|---:|
| PrecBolsNaci | hourly | 227,928 | 0 | 0 | 0 |
| DemaReal | hourly | 227,928 | 0 | 0 | 0 |
| DemaCome | hourly | 227,928 | 0 | 0 | 0 |
| PorcVoluUtilDiar | daily | 9,497 | 0 | 0 | 0 |
| VoluUtilDiarEner | daily | 9,497 | 0 | 0 | 0 |
| CapaUtilDiarEner | daily | 9,497 | 0 | 0 | 0 |
| AporEner | daily | 9,497 | 0 | 0 | 0 |

## Archivos para usar

- `xm_nacional_horario_2000_2025.csv`: precio de bolsa, demanda real y demanda comercial, unidos por hora sin imputación.
- `xm_hidrologia_diaria_2000_2025.csv`: llenado original, reserva útil, capacidad útil y aportes, unidos por fecha sin imputación.
- Un CSV por métrica conserva cada ocurrencia recibida y su valor original, incluso si hubiera duplicados.
- `raw/`: respuestas originales comprimidas sin modificar su JSON; cada archivo tiene petición, fecha de recuperación y SHA-256 en su archivo `.meta.json`.
- `audit.json`, `issues.json`, `range_flags.json` y `raw_manifest.json`: resultados y procedencia verificables.

## Convenciones y alcance

- `Hour01` se representa como el intervalo local 00:00–01:00 y `Hour24` como 23:00–00:00 del día siguiente. Se conserva `xm_hour` para evitar ambigüedad con el nombre del campo original. Zona America/Bogota, UTC−05:00.
- El precio conserva COP/kWh. Las dos demandas y magnitudes de energía hidrológica conservan las unidades de la API; véase el catálogo guardado para su definición. Las columnas de energía se expresan en kWh y no se convierten a potencia.
- El llenado se guarda tal como lo devuelve XM. Los valores fuera del intervalo 0–1 quedan en `range_flags.json`: requieren verificar la definición histórica y no se recortan, normalizan ni imputan.
- Las banderas de rango no son fechas faltantes ni duplicados. El resultado de calendario no certifica por sí solo plausibilidad física o estabilidad de definiciones históricas.
- La descarga actual puede contener revisiones de XM. Las fechas/horas representan el fenómeno, **no una fecha histórica de publicación verificada**. El uso como covariable requiere su política de disponibilidad y revisión.
- No se crean particiones de entrenamiento/prueba ni se consultan datos del E1. No se agregan textos ni grupos temáticos.

Fuente y límites de consulta: [documentación oficial XM](https://github.com/EquipoAnaliticaXM/API_XM). Descarga en bloques inclusivos de hasta 30 días, tres conexiones simultáneas, reintentos y caché reanudable.
