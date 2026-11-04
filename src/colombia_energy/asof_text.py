"""Selección estricta de texto con disponibilidad de la versión acreditada.

No aprende ni clasifica temas. No modifica los datos/preregistros del E1.
"""
import datetime as dt
import re

ALLOWED_SOURCES={'El Tiempo','El Espectador','Semana','Portafolio','La República',
                 'El Colombiano','Dinero','IDEAM','XM'}


def aware(value):
    parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp must have an explicit timezone')
    return parsed


def eligible(record,origin):
    cutoff=aware(origin)
    if (record.get('source') or record.get('medium')) not in ALLOWED_SOURCES:
        return False
    if record.get('availability_status')!='verified_archived_version':
        return False
    if record.get('availability_proof')!='wayback_payload_digest_and_capture':
        return False
    clean_flag=record.get('quarantined',False) in (False,0,None,'','0','false','False')
    if not re.fullmatch('[0-9a-f]{64}',record.get('version_sha256') or '') or not clean_flag:
        return False
    available=record.get('available_at_verified')
    captured=record.get('capture_at_verified')
    if not available or not captured:
        return False
    # Both refer to the exact version, never to the report's reference period.
    return aware(captured)<=aware(available)<=cutoff


def eligible_retrospective(record,origin):
    """Escenario autorizado: fecha declarada, SIN certificar versión histórica."""
    cutoff=aware(origin)
    if (record.get('source') or record.get('medium')) not in ALLOWED_SOURCES:
        return False
    if record.get('quarantined',False) not in (False,0,None,'','0','false','False'):
        return False
    assumed=record.get('available_at_assumed')
    if not assumed or record.get('assumed_availability_basis') not in {
            'declared_timestamp_unverified_version','next_day_after_declared_date_unverified_version'}:
        return False
    return aware(assumed)<=cutoff


def select_before_origin(records,origin,scenario='verified'):
    aware(origin)
    if scenario not in {'verified','declared_dates'}:
        raise ValueError('Choose verified or declared_dates explicitly')
    rule=eligible if scenario=='verified' else eligible_retrospective
    field='available_at_verified' if scenario=='verified' else 'available_at_assumed'
    selected=[r for r in records if rule(r,origin)]
    return sorted(selected,key=lambda r:(aware(r[field]),r['id']))


def verify_guards():
    good=dict(id='a',source='IDEAM',availability_status='verified_archived_version',
              availability_proof='wayback_payload_digest_and_capture',version_sha256='a'*64,
              capture_at_verified='2020-12-15T10:00:00-05:00',
              available_at_verified='2020-12-15T10:00:00-05:00',
              publication_date_claimed='2020-12-01',reference_period='2021-01')
    assert eligible(good,'2020-12-15T10:00:00-05:00')
    assert not eligible(good,'2020-12-15T09:59:59-05:00')
    assert eligible(good,'2020-12-15T15:00:00+00:00')
    assert not eligible(dict(good,source='El Heraldo'),'2025-01-01T00:00:00-05:00')
    assert not eligible(dict(good,availability_status='unverified'), '2025-01-01T00:00:00-05:00')
    assert not eligible(dict(good,available_at_verified=None,
                             available_at_assumed='2020-12-02T00:00:00-05:00'),'2021-01-01T00:00:00-05:00')
    assert not eligible(dict(good,capture_at_verified='2026-11-03T00:00:00-05:00',
                             available_at_verified='2026-11-03T00:00:00-05:00'),'2021-01-01T00:00:00-05:00')
    assert not eligible(dict(good,quarantined=True),'2025-01-01T00:00:00-05:00')
    assert eligible(dict(good,quarantined='0'),'2020-12-15T10:00:00-05:00')
    assert not eligible(dict(good,quarantined='1'),'2025-01-01T00:00:00-05:00')
    assert not eligible(dict(good,version_sha256='not-a-hash'),'2025-01-01T00:00:00-05:00')
    declared=dict(good,availability_status='historical_version_unverified',
        available_at_verified=None,capture_at_verified=None,version_sha256=None,
        available_at_assumed='2020-12-02T00:00:00-05:00',
        assumed_availability_basis='next_day_after_declared_date_unverified_version')
    assert eligible_retrospective(declared,'2020-12-02T00:00:00-05:00')
    assert not eligible_retrospective(declared,'2020-12-01T23:59:59-05:00')
    assert not eligible(declared,'2025-01-01T00:00:00-05:00')
    assert not eligible_retrospective(dict(declared,available_at_assumed=None),'2025-01-01T00:00:00-05:00')
    assert [r['id'] for r in select_before_origin([declared],'2020-12-02T00:00:00-05:00','declared_dates')]==['a']
    try:select_before_origin([good],'2020-12-15T10:00:00')
    except ValueError:pass
    else:raise AssertionError('Naive origin accepted')
    assert [r['id'] for r in select_before_origin([dict(good,id='b'),good],
            '2020-12-15T10:00:00-05:00')]==['a','b']
    print('OK: versiones, captura, fechas futuras, supuestos, fuentes excluidas y zona horaria.')


if __name__=='__main__':verify_guards()
