"""Recalcula frecuencias bibliográficas sin acceder a datos ni entrenamientos."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def main():
    directory = ROOT / 'literature/baseline_review'
    studies = pd.read_csv(directory/'studies.csv', keep_default_na=False)
    records = pd.read_csv(directory/'extractions.csv', keep_default_na=False)
    registry = pd.read_csv(directory/'retrieval_registry.csv', keep_default_na=False)
    screening = pd.read_csv(directory/'screening_inherited.csv', keep_default_na=False)
    assert studies.study_id.is_unique and registry.study_id.is_unique
    assert studies.identificador.is_unique
    assert screening.record_id.is_unique
    assert set(records.study_id) <= set(studies.study_id)
    assert set(records.papel) <= {'comparador','comparador_benchmark','propuesto','componente','ablacion','mencion'}
    joined = records.merge(studies[['study_id','sha256']], on='study_id', suffixes=('_record','_study'))
    assert (joined.sha256_record == joined.sha256_study).all()
    empirical = set(studies.loc[studies.estrato != 'contexto_revision','study_id'])
    point = set(studies.loc[studies.estrato == 'puntual','study_id'])
    peer = set(studies.loc[(studies.estrato == 'puntual') & (studies.preprint == 0),'study_id'])
    baseline = records.loc[records.papel.isin({'comparador','comparador_benchmark'}) & (records.modelo_neuronal_objetivo == 1)]
    presence = baseline[['study_id','familia']].drop_duplicates()
    rows = []
    for family, group in presence.groupby('familia'):
        ids = set(group.study_id)
        rows.append(dict(familia=family, estudios_puntuales=len(ids & point),
            denominador_puntual=len(point), porcentaje_puntual=round(100*len(ids & point)/len(point),2),
            estudios_puntuales_sin_preprints=len(ids & peer), denominador_sin_preprints=len(peer),
            estudios_ampliados=len(ids & empirical), denominador_ampliado=len(empirical),
            ids_puntuales=';'.join(sorted(ids & point)), ids_ampliados=';'.join(sorted(ids & empirical))))
    frequency = pd.DataFrame(rows).sort_values(['estudios_puntuales','familia'], ascending=[False,True])
    frequency.to_csv(directory/'baseline_frequencies.csv', index=False, encoding='utf-8', lineterminator='\n')
    summary = dict(date='2026-11-06', inherited_screened=len(screening),
        inherited_included=int((screening.decision == 'incluido').sum()),
        fulltexts_reviewed=len(studies), empirical_reviewed=len(empirical), point_forecast_studies=len(point),
        related_market_studies=int((studies.estrato=='mercado_relacionado').sum()),
        probabilistic_studies=int((studies.estrato=='probabilistico').sum()),
        reviews_excluded=int((studies.estrato=='contexto_revision').sum()),
        pending_fulltexts=int((registry.estado=='pendiente_texto_completo').sum()),
        model_records=len(records), single_reviewer=True, systematic_search_complete=False,
        selection_post_experiments=True)
    (directory/'review_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(summary,ensure_ascii=False))

if __name__ == '__main__':
    main()
