"""Descarga reanudable y auditoría exhaustiva de siete series nacionales XM.

Sólo escribe bajo research/dataset_colombia/xm_2000_2025; no accede a E1.
Usa bloques inclusivos de <=30 días y tres conexiones simultáneas.
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import random
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'xm_2000_2025'
RAW = OUT / 'raw'
START, END = dt.date(2000, 1, 1), dt.date(2025, 12, 31)
SPECS = {
    'PrecBolsNaci': ('hourly', 'precio_bolsa_cop_kwh'),
    'DemaReal': ('hourly', 'demanda_real_kwh'),
    'DemaCome': ('hourly', 'demanda_comercial_kwh'),
    'PorcVoluUtilDiar': ('daily', 'llenado_valor_original'),
    'VoluUtilDiarEner': ('daily', 'reserva_util_kwh'),
    'CapaUtilDiarEner': ('daily', 'capacidad_util_kwh'),
    'AporEner': ('daily', 'aportes_kwh_dia'),
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def chunks():
    start = START
    while start <= END:
        end = min(start + dt.timedelta(days=29), END)
        yield start.isoformat(), end.isoformat()
        start = end + dt.timedelta(days=1)


def request(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                                          'User-Agent': 'Academic-XM-history-download/1.0'})
    with urllib.request.urlopen(req, timeout=65) as response:
        return response.read(), dict(response.headers)


def fetch(job):
    metric, first, last = job
    freq = SPECS[metric][0]
    folder = RAW / metric
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{first}_{last}.json.gz'
    meta_path = folder / f'{first}_{last}.meta.json'
    if path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        raw = gzip.decompress(path.read_bytes())
        if meta.get('status') == 'ok' and hashlib.sha256(raw).hexdigest() == meta['sha256_response']:
            return dict(metric=metric, first=first, last=last, status='cached')
    payload = dict(MetricId=metric, Entity='Sistema', StartDate=first, EndDate=last, Filter=[])
    url = f'https://servapibi.xm.com.co/{freq}'
    errors = []
    for attempt in range(1, 6):
        try:
            raw, headers = request(url, payload)
            data = json.loads(raw)
            if not isinstance(data, dict) or not isinstance(data.get('Items'), list):
                raise ValueError('Response does not contain an Items list')
            if not data['Items']:
                raise ValueError('Empty Items response')
            temp = path.with_suffix(path.suffix + '.tmp')
            temp.write_bytes(gzip.compress(raw, mtime=0))
            temp.replace(path)
            save_json(meta_path, dict(status='ok', requested_at=now(), url=url, payload=payload,
                                     sha256_response=hashlib.sha256(raw).hexdigest(),
                                     uncompressed_bytes=len(raw), response_headers=headers,
                                     item_count=len(data['Items']), attempts=attempt, prior_errors=errors))
            return dict(metric=metric, first=first, last=last, status='downloaded')
        except Exception as exc:
            errors.append(dict(attempt=attempt, error=repr(exc)))
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                break
            if attempt < 5:
                time.sleep(min(2 ** attempt + random.random(), 25))
    save_json(folder / f'{first}_{last}.error.json', dict(url=url, payload=payload, errors=errors, at=now()))
    return dict(metric=metric, first=first, last=last, status='error', errors=errors)


def capture_catalog():
    path = OUT / 'metric_catalog_response.json.gz'
    payload = dict(MetricId='ListadoMetricas', Entity='Sistema', StartDate='2025-01-01', EndDate='2025-01-01')
    try:
        if path.exists():
            raw = gzip.decompress(path.read_bytes())
        else:
            raw, headers = request('https://servapibi.xm.com.co/Lists', payload)
            path.write_bytes(gzip.compress(raw, mtime=0))
            save_json(OUT / 'metric_catalog_meta.json', dict(retrieved_at=now(), payload=payload,
                      url='https://servapibi.xm.com.co/Lists', sha256_response=hashlib.sha256(raw).hexdigest()))
        data = json.loads(raw)
        selected = [entity['Values'] for item in data.get('Items', [])
                    for entity in item.get('ListEntities', [])
                    if entity.get('Values', {}).get('MetricId') in SPECS
                    and entity.get('Values', {}).get('Entity') == 'Sistema']
        save_json(OUT / 'metadata_metricas.json', selected)
    except Exception as exc:
        save_json(OUT / 'metric_catalog_error.json', dict(error=repr(exc), at=now()))


def as_number(value):
    if value is None or value == '':
        return None, 'null'
    try:
        parsed = float(value)
    except (ValueError, TypeError):
        return None, 'not_numeric'
    return (parsed, None) if math.isfinite(parsed) else (None, 'nonfinite')


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def audit():
    days = [(START + dt.timedelta(days=i)).isoformat() for i in range((END-START).days+1)]
    expected_dates = set(days)
    audits, maps, manifest, issues, all_anomalies = {}, {}, [], [], []
    for metric, (freq, column) in SPECS.items():
        records = []
        item_dates = []
        missing_chunks = []
        for first, last in chunks():
            path = RAW / metric / f'{first}_{last}.json.gz'
            meta_path = RAW / metric / f'{first}_{last}.meta.json'
            if not path.exists() or not meta_path.exists():
                missing_chunks.append([first, last])
                continue
            raw = gzip.decompress(path.read_bytes())
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            if hashlib.sha256(raw).hexdigest() != meta['sha256_response']:
                raise RuntimeError(f'Raw response hash mismatch: {path}')
            data = json.loads(raw)
            manifest.append(dict(metric=metric, path=path.relative_to(OUT).as_posix(),
                                 first=first, last=last, sha256_response=meta['sha256_response'],
                                 retrieved_at=meta['requested_at']))
            for item in data.get('Items', []):
                date = item.get('Date')
                item_dates.append(date)
                if not date or not first <= date <= last:
                    issues.append(dict(metric=metric, date=date, kind='item_date_outside_requested_chunk', file=str(path)))
                entities = item.get('HourlyEntities' if freq == 'hourly' else 'DailyEntities', [])
                if not entities:
                    issues.append(dict(metric=metric, date=date, kind='empty_entities'))
                for entity in entities:
                    values = entity.get('Values', {}) if freq == 'hourly' else entity
                    entity_id = entity.get('Id') or entity.get('Code') or entity.get('Name') or values.get('code')
                    if entity_id != 'Sistema':
                        issues.append(dict(metric=metric, date=date, kind='unexpected_entity', entity=entity_id))
                    hours = range(1, 25) if freq == 'hourly' else [None]
                    for hour in hours:
                        raw_value = values.get(f'Hour{hour:02}') if hour else values.get('Value')
                        value, problem = as_number(raw_value)
                        key = f'{date}T{hour-1:02}:00:00-05:00' if hour else date
                        records.append(dict(key=key, date=date, hour=hour, entity=entity_id,
                                            value_raw=raw_value, value=value))
                        if problem:
                            issues.append(dict(metric=metric, date=date, hour=hour, kind=problem))
                        if value is not None and (value < 0 or (metric == 'PorcVoluUtilDiar' and value > 1)):
                            all_anomalies.append(dict(metric=metric, date=date, hour=hour, value=value,
                                                      kind='outside_fraction_0_1' if metric == 'PorcVoluUtilDiar' else 'negative_value'))
        key_counts = Counter(row['key'] for row in records)
        duplicate_keys = {key: n for key, n in key_counts.items() if n > 1}
        date_counts = Counter(item_dates)
        duplicate_item_dates = {key: n for key, n in date_counts.items() if n > 1}
        observed_dates = {row['date'] for row in records}
        missing_dates = sorted(expected_dates - observed_dates)
        extra_dates = sorted(observed_dates - expected_dates)
        expected_keys = {f'{day}T{hour:02}:00:00-05:00' for day in days for hour in range(24)} if freq == 'hourly' else expected_dates
        missing_keys = sorted(expected_keys - set(key_counts))
        extra_keys = sorted(set(key_counts) - expected_keys)
        finite = [row['value'] for row in records if row['value'] is not None]
        audits[metric] = dict(frequency=freq, entity='Sistema', expected_records=len(expected_keys),
                             observed_records=len(records), unique_keys=len(key_counts),
                             valid_numeric_values=len(finite), missing_dates=missing_dates,
                             missing_keys=missing_keys, extra_dates=extra_dates, extra_keys=extra_keys,
                             duplicate_keys=duplicate_keys, duplicate_item_dates=duplicate_item_dates,
                             missing_chunks=missing_chunks, null_or_invalid_values=len(records)-len(finite),
                             min=min(finite) if finite else None, max=max(finite) if finite else None,
                             range_flags=sum(row['metric'] == metric for row in all_anomalies),
                             first_key=min(key_counts) if key_counts else None,
                             last_key=max(key_counts) if key_counts else None)
        audits[metric]['calendar_integrity_pass'] = not any([
            missing_dates, missing_keys, extra_dates, extra_keys, duplicate_keys,
            duplicate_item_dates, missing_chunks, len(records)-len(finite),
            [row for row in issues if row['metric'] == metric],
        ])
        # Every raw occurrence is preserved in per-metric extracts. Never silently drop duplicates.
        write_csv(OUT / f'{metric}.csv', ['key', 'date', 'hour', 'entity', 'value_raw', 'value'], records)
        if duplicate_keys:
            maps[metric] = None
        else:
            maps[metric] = {row['key']: row['value_raw'] for row in records}
        print(json.dumps(dict(audit_metric=metric, **{k: v for k, v in audits[metric].items() if not isinstance(v, (list, dict))})), flush=True)

    for freq, filename in [('hourly', 'xm_nacional_horario_2000_2025.csv'), ('daily', 'xm_hidrologia_diaria_2000_2025.csv')]:
        selected = [metric for metric, spec in SPECS.items() if spec[0] == freq]
        if any(maps[metric] is None for metric in selected):
            continue
        keys = sorted(set().union(*(set(maps[metric]) for metric in selected)))
        fields = ['timestamp_start_colombia', 'timestamp_end_colombia', 'date', 'xm_hour'] if freq == 'hourly' else ['date']
        fields += [SPECS[metric][1] for metric in selected]
        def prepared():
            for key in keys:
                if freq == 'hourly':
                    start = dt.datetime.fromisoformat(key)
                    row = dict(timestamp_start_colombia=key,
                               timestamp_end_colombia=(start+dt.timedelta(hours=1)).isoformat(),
                               date=key[:10], xm_hour=start.hour+1)
                else:
                    row = dict(date=key)
                row.update({SPECS[metric][1]: maps[metric].get(key) for metric in selected})
                yield row
        write_csv(OUT / filename, fields, prepared())

    complete = all(value['calendar_integrity_pass'] for value in audits.values())
    report = dict(audited_at=now(), start=START.isoformat(), end_inclusive=END.isoformat(),
                  timezone='America/Bogota', expected_days=len(days), expected_hours=len(days)*24,
                  scope='Seven national Sistema series; complete calendar audit, not point-in-time publication/vintage certification',
                  all_calendar_checks_pass=complete, metrics=audits,
                  raw_files=len(manifest), source='https://github.com/EquipoAnaliticaXM/API_XM')
    save_json(OUT / 'audit.json', report)
    save_json(OUT / 'issues.json', issues)
    save_json(OUT / 'range_flags.json', all_anomalies)
    save_json(OUT / 'raw_manifest.json', manifest)
    table = '\n'.join(f"| {metric} | {value['frequency']} | {value['observed_records']:,} | {len(value['missing_keys']):,} | {len(value['duplicate_keys']):,} | {value['null_or_invalid_values']:,} |" for metric, value in audits.items())
    text = f'''# Descarga completa y auditoría XM: 2000–2025

Auditoría generada: {report['audited_at']}.

Resultado de integridad del calendario: **{'APROBADO' if complete else 'CON INCIDENCIAS; consultar audit.json e issues.json'}**.

Periodo inclusivo: 2000-01-01 a 2025-12-31. Entidad: **Sistema nacional**. Calendario esperado: {len(days):,} días y {len(days)*24:,} horas por serie horaria.

| Métrica | Frecuencia | Valores recibidos | Fechas/horas faltantes | Claves duplicadas | Nulos/no válidos |
|---|---|---:|---:|---:|---:|
{table}

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
'''
    (OUT / 'VALIDACION_COMPLETA.md').write_text(text, encoding='utf-8')
    output_files = [path for path in OUT.iterdir() if path.is_file() and path.name not in {'download_progress.json', 'output_manifest.json'}]
    save_json(OUT / 'output_manifest.json', [dict(path=path.name, bytes=path.stat().st_size,
              sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(output_files)])
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = now()
    capture_catalog()
    jobs = [(metric, first, last) for first, last in chunks() for metric in SPECS]
    counts, failures = Counter(), []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch, job) for job in jobs]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            counts[result['status']] += 1
            if result['status'] == 'error':
                failures.append(result)
            if i % 35 == 0 or i == len(jobs) or result['status'] == 'error':
                progress = dict(started_at=started, updated_at=now(), completed=i, total=len(jobs), counts=dict(counts), failures=failures)
                save_json(OUT / 'download_progress.json', progress)
                print(json.dumps({k: v for k, v in progress.items() if k != 'failures'}), flush=True)
    report = audit()
    print(json.dumps(dict(done=True, all_calendar_checks_pass=report['all_calendar_checks_pass'], failures=len(failures))), flush=True)


if __name__ == '__main__':
    main()
