"""Verifica independientemente los CSV exportados y su cobertura mensual.

No consulta la red, no rellena valores ni elimina duplicados. La auditoría principal
ya coteja todas las claves contra las respuestas originales; aquí se verifica la
exportación final y se compara cada celda consolidada con los extractos por métrica.
"""
import calendar
import csv
import datetime as dt
import hashlib
import json
from collections import Counter
from decimal import Decimal

from download_xm_full import OUT, SPECS


def verify():
    result = json.loads((OUT / 'audit.json').read_text(encoding='utf-8'))
    assert result['expected_days'] == 9497
    assert result['expected_hours'] == 227928
    assert result['all_calendar_checks_pass'], 'La auditoría de respuestas originales tiene incidencias'
    monthly = []
    for metric, (frequency, column) in SPECS.items():
        seen = set()
        counts = Counter()
        previous = None
        step = dt.timedelta(hours=1) if frequency == 'hourly' else dt.timedelta(days=1)
        with (OUT / f'{metric}.csv').open(encoding='utf-8', newline='') as stream:
            for row in csv.DictReader(stream):
                key = row['key']
                assert key not in seen, (metric, 'duplicate', key)
                seen.add(key)
                assert row['entity'] == 'Sistema'
                assert row['value_raw'] != '' and Decimal(row['value_raw']).is_finite()
                instant = dt.datetime.fromisoformat(key) if frequency == 'hourly' else dt.date.fromisoformat(key)
                if previous is not None:
                    assert instant - previous == step, (metric, 'nonconsecutive', previous, instant)
                previous = instant
                counts[key[:7]] += 1
        assert len(seen) == (227928 if frequency == 'hourly' else 9497)
        for year in range(2000, 2026):
            for month in range(1, 13):
                period = f'{year}-{month:02}'
                expected = calendar.monthrange(year, month)[1] * (24 if frequency == 'hourly' else 1)
                assert counts[period] == expected, (metric, period, counts[period], expected)
                monthly.append(dict(metric=metric, frequency=frequency, month=period,
                                    expected=expected, observed=counts[period], missing=expected-counts[period]))

    # Compare every consolidated numeric cell with its source-specific extract.
    for frequency, filename in [('hourly', 'xm_nacional_horario_2000_2025.csv'),
                                ('daily', 'xm_hidrologia_diaria_2000_2025.csv')]:
        expected_rows = 227928 if frequency == 'hourly' else 9497
        for metric, (freq, column) in SPECS.items():
            if freq != frequency:
                continue
            with (OUT / filename).open(encoding='utf-8', newline='') as wide_stream, \
                 (OUT / f'{metric}.csv').open(encoding='utf-8', newline='') as source_stream:
                wide, source = csv.DictReader(wide_stream), csv.DictReader(source_stream)
                count = 0
                for a, b in zip(wide, source, strict=True):
                    key = a['timestamp_start_colombia'] if frequency == 'hourly' else a['date']
                    assert key == b['key']
                    assert Decimal(a[column]) == Decimal(b['value_raw']), (metric, key)
                    if frequency == 'hourly':
                        assert int(a['xm_hour']) == dt.datetime.fromisoformat(key).hour + 1
                        assert dt.datetime.fromisoformat(a['timestamp_end_colombia']) - dt.datetime.fromisoformat(key) == dt.timedelta(hours=1)
                    count += 1
                assert count == expected_rows

    for record in json.loads((OUT / 'output_manifest.json').read_text(encoding='utf-8')):
        path = OUT / record['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], path
    with (OUT / 'coverage_by_month.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['metric', 'frequency', 'month', 'expected', 'observed', 'missing'])
        writer.writeheader()
        writer.writerows(monthly)
    validation = dict(status='pass', verified_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                      monthly_metric_checks=len(monthly), all_monthly_checks_pass=True,
                      numeric_cells_compared=227928*3+9497*4,
                      checks=['original_export_hashes', 'no_duplicate_keys', 'consecutive_intervals',
                              '312_months_per_metric', 'no_null_numeric_values',
                              'every_consolidated_cell_matches_metric_extract', 'hour_labels_and_interval_length'])
    (OUT / 'independent_verification.json').write_text(json.dumps(validation, indent=2)+'\n', encoding='utf-8')
    # Extend the existing output manifest without changing hashes of prior files.
    manifest = json.loads((OUT / 'output_manifest.json').read_text(encoding='utf-8'))
    for name in ['coverage_by_month.csv', 'independent_verification.json']:
        path = OUT / name
        manifest = [row for row in manifest if row['path'] != name]
        manifest.append(dict(path=name, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (OUT / 'output_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(validation))


if __name__ == '__main__':
    verify()
