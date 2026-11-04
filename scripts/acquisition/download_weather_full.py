"""ERA5/Open-Meteo completo, ocho ciudades, 2000–2025; descarga y auditoría.

Respuestas originales por año, caché reanudable, cuotas respetadas y sin imputación.
No accede a datos, resultados o prueba de E1.
"""
from __future__ import annotations

import calendar
import contextlib
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'weather_2000_2025'
RAW = OUT / 'raw'
BOGOTA = dt.timezone(dt.timedelta(hours=-5))
CATALOG = json.loads((HERE / 'source_catalog.json').read_text(encoding='utf-8'))
SOURCE = next(x for x in CATALOG['sources'] if x['source_id'] == 'era5_open_meteo')
CITIES = SOURCE['locations']
VARIABLES = {'temperature_2m': ('temperature_2m_c', '°C'),
             'relative_humidity_2m': ('relative_humidity_2m_pct', '%'),
             'precipitation': ('precipitation_preceding_hour_mm', 'mm')}
YEARS = range(2000, 2026)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save_json(path, obj):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    tmp.replace(path)


def params_for(year):
    return dict(latitude=','.join(str(c['latitude']) for c in CITIES),
                longitude=','.join(str(c['longitude']) for c in CITIES),
                start_date=f'{year}-01-01', end_date=f'{year}-12-31',
                hourly=','.join(VARIABLES), models='era5', timezone='America/Bogota',
                temperature_unit='celsius', precipitation_unit='mm')


def fetch(year):
    path = RAW / f'{year}.json.gz'
    meta_path = RAW / f'{year}.meta.json'
    if path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        raw = gzip.decompress(path.read_bytes())
        if meta.get('status') == 'ok' and hashlib.sha256(raw).hexdigest() == meta['sha256_response']:
            return 'cached', meta
    parameters = params_for(year)
    url = 'https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode(parameters)
    errors = []
    for attempt in range(1, 7):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Academic-Colombia-weather-history/1.0'})
            with urllib.request.urlopen(req, timeout=150) as response:
                raw, headers = response.read(), dict(response.headers)
            obj = json.loads(raw)
            if not isinstance(obj, list) or len(obj) != len(CITIES):
                raise ValueError('Expected eight location responses')
            if not all(isinstance(x.get('hourly'), dict) and x['hourly'].get('time') for x in obj):
                raise ValueError('Missing hourly observations')
            tmp = path.with_suffix(path.suffix+'.tmp')
            tmp.write_bytes(gzip.compress(raw, mtime=0))
            tmp.replace(path)
            meta = dict(status='ok', url=url, parameters=parameters, retrieved_at=now(),
                        response_headers=headers, sha256_response=hashlib.sha256(raw).hexdigest(),
                        uncompressed_bytes=len(raw), attempts=attempt, prior_errors=errors)
            save_json(meta_path, meta)
            return 'downloaded', meta
        except Exception as exc:
            detail = exc.read().decode('utf-8', errors='replace')[:500] if isinstance(exc, urllib.error.HTTPError) else None
            errors.append(dict(attempt=attempt, error=repr(exc), detail=detail, at=now()))
            print(json.dumps(dict(year=year, retry=attempt, error=repr(exc), detail=detail)), flush=True)
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {408, 429, 500, 502, 503, 504}:
                break
            if attempt < 6:
                wait = 65 if isinstance(exc, urllib.error.HTTPError) and exc.code == 429 else min(2**attempt, 30)
                time.sleep(wait)
    save_json(RAW / f'{year}.error.json', dict(year=year, url=url, errors=errors))
    raise RuntimeError(f'Could not download year {year}: {errors[-1]}')


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def expected_times(year):
    start, last = dt.datetime(year, 1, 1), dt.datetime(year+1, 1, 1)
    return [(start + dt.timedelta(hours=i)).isoformat(timespec='minutes')
            for i in range(int((last-start).total_seconds()/3600))]


def audit_export():
    cities_dir = OUT / 'cities'
    cities_dir.mkdir(exist_ok=True)
    stats = {c['id']: dict(expected_hours=227928, observed_hours=0, missing_hours=0,
                          duplicate_keys=0, extra_hours=0, nonchronological_years=0,
                          null_or_invalid_by_variable={v: 0 for v in VARIABLES},
                          range_flags_by_variable={v: 0 for v in VARIABLES},
                          min_by_variable={v: None for v in VARIABLES},
                          max_by_variable={v: None for v in VARIABLES}) for c in CITIES}
    issues, monthly, grid_meta, manifest = [], [], [], []
    common_times_ok = True
    with contextlib.ExitStack() as stack:
        city_writers = {}
        for city in CITIES:
            stream = stack.enter_context((cities_dir / f"{city['id']}.csv").open('w', encoding='utf-8', newline=''))
            writer = csv.writer(stream)
            writer.writerow(['timestamp_colombia']+[item[0] for item in VARIABLES.values()])
            city_writers[city['id']] = writer
        wide_stream = stack.enter_context((OUT / 'clima_ocho_ciudades_horario_2000_2025.csv').open('w', encoding='utf-8', newline=''))
        wide_writer = csv.writer(wide_stream)
        wide_writer.writerow(['timestamp_colombia']+[f"{spec[0]}_{city['id'].lower()}" for city in CITIES for spec in VARIABLES.values()])
        for year in YEARS:
            path = RAW / f'{year}.json.gz'
            raw = gzip.decompress(path.read_bytes())
            meta = json.loads((RAW / f'{year}.meta.json').read_text(encoding='utf-8'))
            if hashlib.sha256(raw).hexdigest() != meta['sha256_response']:
                raise RuntimeError(f'Hash mismatch for year {year}')
            data = json.loads(raw)
            expected = expected_times(year)
            expected_set = set(expected)
            manifest.append(dict(year=year, file=f'raw/{year}.json.gz',
                                 sha256_response=meta['sha256_response'], retrieved_at=meta['retrieved_at']))
            for city, location in zip(CITIES, data, strict=True):
                city_id = city['id']
                hourly = location['hourly']
                times = hourly['time']
                counter = Counter(times)
                missing, extra = sorted(expected_set-set(times)), sorted(set(times)-expected_set)
                duplicates = {key: n for key, n in counter.items() if n > 1}
                stat = stats[city_id]
                stat['observed_hours'] += len(times)
                stat['missing_hours'] += len(missing)
                stat['extra_hours'] += len(extra)
                stat['duplicate_keys'] += len(duplicates)
                stat['nonchronological_years'] += times != sorted(times)
                if missing or extra or duplicates:
                    issues.append(dict(city=city_id, year=year, kind='calendar', missing=missing, extra=extra, duplicates=duplicates))
                if times != expected:
                    common_times_ok = False
                if location.get('utc_offset_seconds') != -18000 or location.get('timezone') != 'America/Bogota':
                    issues.append(dict(city=city_id, year=year, kind='unexpected_timezone', actual=location.get('timezone')))
                if abs(location['latitude']-city['latitude']) > .75 or abs(location['longitude']-city['longitude']) > .75:
                    issues.append(dict(city=city_id, year=year, kind='unexpected_grid_location'))
                grid_meta.append(dict(city=city_id, year=year, requested_latitude=city['latitude'],
                                      requested_longitude=city['longitude'], grid_latitude=location['latitude'],
                                      grid_longitude=location['longitude'], elevation=location.get('elevation'),
                                      timezone=location.get('timezone'), utc_offset_seconds=location.get('utc_offset_seconds'),
                                      hourly_units=location.get('hourly_units')))
                month_counts = Counter(t[:7] for t in times)
                for variable, (column, unit) in VARIABLES.items():
                    values = hourly.get(variable, [])
                    if len(values) != len(times):
                        issues.append(dict(city=city_id, year=year, variable=variable, kind='array_length_mismatch'))
                        raise RuntimeError('Array length mismatch; raw data retained')
                    if location.get('hourly_units', {}).get(variable) != unit:
                        issues.append(dict(city=city_id, year=year, variable=variable, kind='unit_mismatch'))
                    good = [x for x in values if finite(x)]
                    stat['null_or_invalid_by_variable'][variable] += len(values)-len(good)
                    if good:
                        old_min, old_max = stat['min_by_variable'][variable], stat['max_by_variable'][variable]
                        stat['min_by_variable'][variable] = min(good) if old_min is None else min(old_min, min(good))
                        stat['max_by_variable'][variable] = max(good) if old_max is None else max(old_max, max(good))
                    flags = sum((x < 0 or x > 100) if variable == 'relative_humidity_2m' else
                                (x < 0) if variable == 'precipitation' else (x < -30 or x > 60) for x in good)
                    stat['range_flags_by_variable'][variable] += flags
                    for month in range(1, 13):
                        prefix = f'{year}-{month:02}'
                        selected = [i for i, t in enumerate(times) if t.startswith(prefix)]
                        monthly.append(dict(city=city_id, variable=variable, month=prefix,
                                            expected=calendar.monthrange(year, month)[1]*24,
                                            observed_timestamps=month_counts[prefix],
                                            valid_numeric_values=sum(finite(values[i]) for i in selected)))
                for i, stamp in enumerate(times):
                    city_writers[city_id].writerow([stamp+':00-05:00']+[hourly[v][i] for v in VARIABLES])
            # Wide export is allowed only when every city has the expected exact ordering.
            if all(x['hourly']['time'] == expected for x in data):
                for i, stamp in enumerate(expected):
                    wide_writer.writerow([stamp+':00-05:00']+[location['hourly'][v][i] for location in data for v in VARIABLES])
            else:
                common_times_ok = False
            print(json.dumps(dict(exported_year=year, expected_hours=len(expected))), flush=True)
    for stat in stats.values():
        stat['calendar_and_values_pass'] = (stat['observed_hours'] == stat['expected_hours']
            and not any(stat[k] for k in ['missing_hours', 'duplicate_keys', 'extra_hours', 'nonchronological_years'])
            and not any(stat['null_or_invalid_by_variable'].values()))
    passed = common_times_ok and not issues and all(x['calendar_and_values_pass'] for x in stats.values())
    report = dict(audited_at=now(), start='2000-01-01', end_inclusive='2025-12-31',
                  source='Open-Meteo Historical Weather API; explicit models=era5',
                  timezone='America/Bogota', expected_hours_per_city=227928,
                  expected_city_hours=1823424, expected_numeric_values=5470272,
                  all_checks_pass=passed, stats_by_city=stats, monthly_checks=len(monthly),
                  common_timestamps_exactly_aligned=common_times_ok,
                  historical_publication_vintages_verified=False)
    save_json(OUT / 'audit.json', report)
    save_json(OUT / 'issues.json', issues)
    save_json(OUT / 'grid_metadata.json', grid_meta)
    save_json(OUT / 'raw_manifest.json', manifest)
    with (OUT / 'coverage_by_month.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(monthly[0]))
        writer.writeheader()
        writer.writerows(monthly)
    table = '\n'.join(f"| {city} | {s['observed_hours']:,} | {s['missing_hours']} | {s['duplicate_keys']} | {sum(s['null_or_invalid_by_variable'].values())} |" for city, s in stats.items())
    text = f'''# Clima horario de ocho ciudades: descarga completa 2000–2025

Auditoría: {dt.datetime.fromisoformat(report['audited_at']).astimezone(BOGOTA).isoformat()} (hora colombiana).

Resultado: **{'APROBADO' if passed else 'CON INCIDENCIAS: consultar audit.json e issues.json'}**.

| Ciudad | Horas recibidas | Horas faltantes | Claves duplicadas | Nulos/no numéricos |
|---|---:|---:|---:|---:|
{table}

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
'''
    (OUT / 'VALIDACION_CLIMA.md').write_text(text, encoding='utf-8')
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and 'raw' not in p.relative_to(OUT).parts and p.name not in {'output_manifest.json', 'download_progress.json'})
    save_json(OUT / 'output_manifest.json', [dict(path=p.relative_to(OUT).as_posix(), bytes=p.stat().st_size,
              sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
    print(json.dumps(dict(done=True, all_checks_pass=passed, numeric_values=5470272)), flush=True)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for index, year in enumerate(YEARS, 1):
        status, meta = fetch(year)
        downloaded += status == 'downloaded'
        save_json(OUT / 'download_progress.json', dict(completed=index, total=26, last_year=year,
                  downloaded=downloaded, updated_at=now(), status=status))
        print(json.dumps(dict(year=year, completed=index, total=26, status=status)), flush=True)
        if status == 'downloaded' and year != 2025:
            headers = meta.get('response_headers', {})
            remaining = float(headers.get('X-RateLimit-Remaining', 600))
            reset = float(headers.get('X-RateLimit-Reset', 0))
            # Approximate next annual query cost is 63; leave margin and honor quota reset.
            wait = max(8, reset-time.time()+1) if remaining < 75 else 8
            time.sleep(min(max(wait, 0), 65))
    audit_export()


if __name__ == '__main__':
    main()
