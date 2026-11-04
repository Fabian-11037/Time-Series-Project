"""Política de entradas del E1 colombiano: sin ningún atributo derivado de texto."""
from .data import TARGET

NUMERIC_E1={TARGET,'demanda_real_kwh','demanda_comercial_kwh',
    'llenado_valor_original','reserva_util_kwh','capacidad_util_kwh','aportes_kwh_dia'}
WEATHER_PREFIXES=('temperature_2m_c_','relative_humidity_2m_pct_','precipitation_preceding_hour_mm_')
CITIES={'bogota','medellin','cali','barranquilla','cartagena','bucaramanga','pereira','cucuta'}

def assert_e1_features(names):
    for name in names:
        if name in NUMERIC_E1:continue
        if any(name==prefix+city for prefix in WEATHER_PREFIXES for city in CITIES):continue
        if name in {'hour_sin','hour_cos','week_sin','week_cos','year_sin','year_cos'}:continue
        raise ValueError('E1 sólo admite las variables numéricas declaradas: '+name)
    return True
