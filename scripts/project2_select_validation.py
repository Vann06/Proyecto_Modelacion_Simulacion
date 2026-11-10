"""Export only approved summaries from a local research checkout; never copy raw audits."""
from pathlib import Path
import argparse
import hashlib
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research',type=Path,required=True)
    args=parser.parse_args()
    out=ROOT/'results/project2/selected_validation'
    if out.exists():
        raise SystemExit('Selected evidence already exists; refusing to overwrite it.')
    source=args.research/'results/project2'
    distance=source/'historical_validation/observed_distances.csv'
    decision=source/'nina_quality_control/decision.json'
    summary=pd.read_csv(distance).query("scope == 'project_18_day_window'")
    assert summary.n_valid_distances.sum()==216 and len(summary)==3
    nina=json.loads(decision.read_text())
    assert nina['decision']=='NO APTO' and not nina['direction_confirmed']
    out.mkdir(parents=True)
    summary.to_csv(out/'dietz_window_summary.csv',index=False,lineterminator='\n')
    minimal={'decision':'NO APTO para clasificar instalaciones por idoneidad ecológica',
             'reason':'Dirección del índice y vínculo exacto con ESTIMAP no confirmados; el remuestreo altera el rango.',
             'status':'Investigación cerrada; referencia complementaria',
             'ecological_ranking_allowed':False,'raster_included':False,
             'catalog_url':'https://s3-ext-1.nina.no/dms/maps/main/localEA/config.json'}
    (out/'nina_decision.json').write_text(json.dumps(minimal,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=[]
    for metric,unit,reference,kind,limit in [
        ('total_resource_obtained','synthetic_RU','No comparable','Sin equivalencia','Sin medición física equivalente'),
        ('mean_resource_per_hive','synthetic_RU','No comparable','Sin equivalencia','No hay entregas observadas por colonia'),
        ('min_resource_per_hive','synthetic_RU','No comparable','Sin equivalencia','No hay entregas observadas por colonia'),
        ('mean_distance_m','m','Dietz: distancias decodificadas','Contraste parcial','Danzas seleccionadas y colonias distintas; no emparejar viajes'),
        ('total_distance_m','m','No comparable','Sin equivalencia','Falta esfuerzo y registro completo de viajes reales'),
        ('p95_distance_m','m','Dietz: percentiles descriptivos','Contraste parcial','Muestra dependiente y proceso de observación distinto'),
        ('competition_pressure','fracción','No comparable','Sin equivalencia','Coincidencia simulada no equivale a competencia ecológica ni Jaccard'),
        ('hive_balance_jain','índice Jain','No comparable','Sin equivalencia','Sin recursos entregados reales comparables'),
        ('patches_used_count','parches','No comparable','Sin equivalencia','Destinos de danzas no equivalen a parches municipales')]:
        rows.append(dict(metric=metric,unit=unit,reference=reference,correspondence=kind,limitation=limit))
    pd.DataFrame(rows).to_csv(out/'metric_correspondence.csv',index=False,lineterminator='\n')
    provenance={'source_research_branch':'feature/project2-validacion-historica-oslo',
      'sources':{'Dietz':'https://bybi.no/wp-content/uploads/2018/12/Sabrinas-Master-thesis-181210.pdf',
                 'Dryad':'https://doi.org/10.5061/dryad.9kd51c5qk'},
      'source_artifact_hashes':{str(p.relative_to(args.research)):hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [distance,decision]},
      'dietz_filter':"scope == 'project_18_day_window'; distances decoded from appendix, not GPS",
      'dietz_window':['2017-07-18','2017-08-04'],'distinct_dates':10,'colony_dates':27,
      'clock_valid_rows':215,'independent_bees_known':False,
      'limitations':['216 danzas no son 216 réplicas independientes','Filmación selectiva de tiempo favorable',
                      'Bootstrap por fechas no incluye incertidumbre de calibración de distancias',
                      'No hay validación predictiva del motor; los errores Dryad son de referentes independientes'],
      'reproduction':'CSV summaries are the delivery input. Full PDF extraction and NINA source audit remain local to research; this package does not claim to reproduce them.'}
    (out/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Selected four small evidence files; no individual records, inferred coordinates or rasters copied.')


if __name__=='__main__':main()
