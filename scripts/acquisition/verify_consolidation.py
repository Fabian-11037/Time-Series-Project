"""Verificaciones de integridad y barreras temporales del paquete candidato."""
import datetime as dt
import hashlib
import json
from pathlib import Path

from consolidate import HERE, OUT, canonical_url, split_for_interval, usable_before_origin


def rows(name):
    return [json.loads(line) for line in (OUT / name).read_text(encoding='utf-8').splitlines() if line]


def verify():
    summary = json.loads((OUT / 'summary.json').read_text(encoding='utf-8'))
    numeric, news = rows('numeric_observations.jsonl'), rows('news_observations.jsonl')
    assert len(numeric) == summary['numeric_observations']
    assert len(news) == summary['news_unique_url_title_versions']
    assert len({row['observation_id'] for row in numeric}) == len(numeric)
    assert len({row['news_id'] for row in news}) == len(news)
    for row in news:
        assert not {'topic', 'topic_cluster', 'anticipatory_label', 'sentiment', 'relevance_score', 'themes'} & row.keys()
    for row in numeric:
        if row['metric'] == 'PorcVoluUtilDiar' and row['value_raw'] > 1:
            assert row['quality_flags']  # Anomalous values retained and flagged, never clipped.
    assert any(row['metric'] == 'PorcVoluUtilDiar' and row['value_raw'] == 1.49144 for row in numeric)
    assert any(row['temporal_status'] == 'quarantine_date_conflict' for row in news)
    for record in json.loads((OUT / 'input_manifest.json').read_text(encoding='utf-8')):
        path = HERE.parent.parent / record['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], path
    for record in json.loads((OUT / 'bundle_manifest.json').read_text(encoding='utf-8')):
        assert hashlib.sha256((OUT / record['path']).read_bytes()).hexdigest() == record['sha256']
    assert sum(row['expected_hours'] for row in rows('monthly_inventory.jsonl')) == 227928
    assert all(row['complete_text_corpus_count'] is None for row in rows('monthly_inventory.jsonl'))
    assert split_for_interval('2017-12-31T23:00:00-05:00', '2018-01-01T00:00:00-05:00') == 'train'
    assert split_for_interval('2017-12-31T23:00:00-05:00', '2018-01-01T01:00:00-05:00') == 'purge_or_outside_period'
    assert split_for_interval('2021-12-31T23:00:00-05:00', '2022-01-01T01:00:00-05:00') == 'purge_or_outside_period'
    assert split_for_interval('2022-01-01T00:00:00-05:00', '2022-01-01T01:00:00-05:00') == 'test'
    assert split_for_interval('2018-01-01T05:00:00+00:00', '2018-01-01T06:00:00+00:00') == 'validation'
    verified = dict(temporal_status='verified_version_available', quality_flags=[],
                    use_status='permitted', available_at_verified='2020-01-02T00:00:00-05:00')
    assert not usable_before_origin(verified, '2020-01-01T23:00:00-05:00')
    assert usable_before_origin(verified, '2020-01-02T00:00:00-05:00')
    assumed = dict(verified, temporal_status='historical_version_unverified',
                   available_at_verified=None, available_at_assumed='2000-01-01T00:00:00-05:00')
    assert not usable_before_origin(assumed, '2020-01-02T00:00:00-05:00')
    assert not usable_before_origin(dict(verified, quality_flags=['date_conflict']), '2020-01-02T00:00:00-05:00')
    assert canonical_url('http://www.semana.com:80/919/a.htm#02') == 'http://www.semana.com/919/a.htm#02'
    for row in news:
        date = row.get('publication_date_claimed')
        if date:
            expected = dt.date.fromisoformat(date[:10]) + dt.timedelta(days=1)
            assert row['available_at_assumed'] == f'{expected.isoformat()}T00:00:00-05:00'
    print('OK: integridad, procedencia, separación de muestras/cobertura, ausencia de temas y barreras temporales.')


if __name__ == '__main__':
    verify()
