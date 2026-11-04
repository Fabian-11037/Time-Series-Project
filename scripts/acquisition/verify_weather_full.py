"""Coteja cada celda meteorológica exportada con las respuestas originales."""
import contextlib
import csv
import gzip
import hashlib
import json

from download_weather_full import OUT, RAW, CITIES, VARIABLES, YEARS, expected_times, now, save_json


def verify():
    audit = json.loads((OUT / 'audit.json').read_text(encoding='utf-8'))
    assert audit['all_checks_pass'], 'La auditoría principal presenta incidencias'
    count = 0
    with contextlib.ExitStack() as stack:
        readers = {}
        for city in CITIES:
            stream = stack.enter_context((OUT / 'cities' / f"{city['id']}.csv").open(encoding='utf-8', newline=''))
            readers[city['id']] = csv.DictReader(stream)
        wide = csv.DictReader(stack.enter_context((OUT / 'clima_ocho_ciudades_horario_2000_2025.csv').open(encoding='utf-8', newline='')))
        for year in YEARS:
            data = json.loads(gzip.decompress((RAW / f'{year}.json.gz').read_bytes()))
            times = expected_times(year)
            for city, location in zip(CITIES, data, strict=True):
                assert location['hourly']['time'] == times
                for i, stamp in enumerate(times):
                    row = next(readers[city['id']])
                    assert row['timestamp_colombia'] == stamp+':00-05:00'
                    for variable, (column, unit) in VARIABLES.items():
                        assert row[column] == str(location['hourly'][variable][i]), (city['id'], stamp, variable)
                        count += 1
            for i, stamp in enumerate(times):
                row = next(wide)
                assert row['timestamp_colombia'] == stamp+':00-05:00'
                for city, location in zip(CITIES, data, strict=True):
                    for variable, (column, unit) in VARIABLES.items():
                        assert row[f"{column}_{city['id'].lower()}"] == str(location['hourly'][variable][i])
        for reader in [*readers.values(), wide]:
            assert next(reader, None) is None, 'Unexpected additional exported rows'
    assert count == 5470272
    for file in json.loads((OUT / 'output_manifest.json').read_text(encoding='utf-8')):
        assert hashlib.sha256((OUT / file['path']).read_bytes()).hexdigest() == file['sha256']
    checks = list(csv.DictReader((OUT / 'coverage_by_month.csv').open(encoding='utf-8', newline='')))
    assert len(checks) == 7488
    assert all(row['expected'] == row['observed_timestamps'] == row['valid_numeric_values'] for row in checks)
    result = dict(status='pass', verified_at=now(), monthly_checks=len(checks),
                  numeric_cells_compared_in_each_export=count, exports_compared=['eight_city_files', 'wide_weather_file'],
                  method='Every exported cell compared to its original annual JSON; exact timestamps and no extra rows')
    save_json(OUT / 'independent_verification.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    verify()
