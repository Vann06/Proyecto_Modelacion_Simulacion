"""Audit Dietz data and enforce the feasibility checkpoint before simulation."""
from pathlib import Path
import argparse,json,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bee_sim.analysis.project2_historical_audit import (SOURCE_URL,SOURCE_SHA256,COLONIES,extract_tables,
    annotate_observations,implied_hives,distance_inventory,conditional_geography,feasibility_report,
    require_historical_feasibility,sha256)


def verify_manual(frame):
    checks=json.loads((ROOT/'data/project2/historical_manual_checks.json').read_text(encoding='utf-8'))
    if checks['source_sha256']!=SOURCE_SHA256:raise ValueError('Muestra visual de otra versión')
    rows=[]
    for expected in checks['checks']:
        actual=frame.loc[frame.colony.eq(expected['colony'])&frame.source_row.eq(expected['source_row'])]
        if len(actual)!=1:raise ValueError('Registro visual ambiguo')
        row=actual.iloc[0]
        for name,value in expected.items():
            if isinstance(value,(int,float)):ok=np.isclose(float(row[name]),value,rtol=0,atol=1e-7)
            else:ok=str(row[name])==value
            if not ok:raise ValueError(f'Muestra visual no coincide: {expected["colony"]}/{expected["source_row"]}/{name}')
        rows.append({'record_id':row.record_id,'source_page':row.source_page,'checked_fields':','.join(expected),
                     'visual_sample_match':True,'review_date_local':checks['review_date_local']})
    return pd.DataFrame(rows)


def save_csv(df,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False,lineterminator='\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['audit','simulate'],nargs='?',default='audit')
    parser.add_argument('--pdf',type=Path,default=ROOT/'.build/historical/dietz_2018.pdf')
    parser.add_argument('--download-source',action='store_true',help='cache the PDF locally, never in tracked data')
    args=parser.parse_args()
    out=ROOT/'results/project2/historical_validation';processed=ROOT/'data/project2/processed'
    if args.command=='simulate':
        path=out/'feasibility.json'
        if not path.exists():parser.error('Ejecutar audit primero; no hay ubicaciones verificadas')
        require_historical_feasibility(json.loads(path.read_text()))
        raise SystemExit('No hay adaptador histórico implementado: no se alteró el motor común.')
    if args.download_source:
        import requests
        # Source download goes only to the explicitly ignored project cache.
        target=ROOT/'.build/historical/dietz_2018.pdf';target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            response=requests.get(SOURCE_URL,timeout=60);response.raise_for_status()
            import hashlib
            if hashlib.sha256(response.content).hexdigest()!=SOURCE_SHA256:raise ValueError('Fuente remota distinta; no guardar')
            target.write_bytes(response.content)
        args.pdf=target
    if not args.pdf.exists():parser.error('Falta PDF local; usar --pdf o --download-source (no se redistribuye el PDF).')
    raw=extract_tables(args.pdf);frame=annotate_observations(raw);hives=implied_hives(frame)
    out.mkdir(parents=True,exist_ok=True)
    manual=verify_manual(frame)
    save_csv(frame,processed/'historical_foraging.csv');save_csv(hives,processed/'historical_hives.csv')
    save_csv(manual,out/'manual_verification.csv')
    inventory=[]
    for colony,g in frame.groupby('colony',sort=False):
        inventory.append({'colony':colony,'rows':len(g),'valid_distances_all_dates':int(g.distance_valid.sum()),
          'first_date':g.date.min(),'last_date':g.date.max(),'n_film_dates':g.date.nunique(),
          'rows_in_project_window':int(g.inside_project_window.sum()),
          'distance_eligible_in_project_window':int(g.distance_analysis_eligible.sum()),
          'clock_eligible_in_project_window':int(g.timed_analysis_eligible.sum()),
          'invalid_clocks_all_dates':int((~g.clock_valid).sum()),
          'id_prefix_mismatches':int((~g.id_prefix_consistent).sum())})
    save_csv(pd.DataFrame(inventory),out/'observations_by_colony.csv')
    cols=['record_id','colony','source_page','source_row','date','inside_project_window','distance_valid',
          'clock_valid','id_prefix_consistent','dance_id_duplicated','distance_analysis_eligible',
          'timed_analysis_eligible','distance_exclusion_reason','origin_residual_source_units']
    save_csv(frame[cols],out/'inclusion_exclusion.csv')
    save_csv(frame.loc[~frame.distance_valid|~frame.clock_valid|~frame.id_prefix_consistent|
                       frame.dance_id_duplicated|~frame.origin_consistent_within_0_1_source_unit],out/'flagged_records.csv')
    stats=distance_inventory(frame);save_csv(stats,out/'observed_distances.csv')
    save_csv(frame.groupby(['colony','date']).size().rename('n_dances').reset_index(),out/'observations_by_date.csv')
    published=[]
    for colony,mean,low,high,minimum,maximum in [('Bygdoy',688.39,685.95,690.84,.007,4039.79),
      ('Ulleval 1',490.95,488.03,493.87,.006,5236.82),('Ulleval 2',425.27,422.98,427.56,.019,2741.46)]:
        g=frame.loc[frame.colony.eq(colony)]
        published.append({'colony':colony,'published_n':COLONIES[colony],'recovered_n':len(g),
          'published_posterior_mean_m':mean,'published_ci_low_m':low,'published_ci_high_m':high,
          'published_posterior_min_m':minimum,'published_posterior_max_m':maximum,
          'appendix_mean_including_negative_m':g.distance_m.mean(),
          'appendix_mean_nonnegative_m':g.loc[g.distance_valid,'distance_m'].mean(),
          'difference_of_distinct_estimands_m':g.loc[g.distance_valid,'distance_m'].mean()-mean,
          'comparison_status':'counts_reproduced; point_estimates_are_not_posterior_samples; not_simulator_error'})
    save_csv(pd.DataFrame(published),out/'published_summary_check.csv')
    details,coverage,hypotheses=conditional_geography(frame,hives,processed/'oslo_parks.geojson')
    save_csv(details,out/'destinations_crs_hypotheses.csv');save_csv(coverage,out/'park_coverage_conditional.csv')
    save_csv(hypotheses,out/'hive_crs_hypotheses.csv')
    save_csv(pd.DataFrame([
      {'analysis':'Jaccard_all_probability_cells','published_value':.50,'source_page':32,'reproduced_value':None,'status':'not_reproducible_without_original_probability_rasters_and_grid'},
      {'analysis':'Jaccard_within_50th_distance_percentile','published_value':.39,'source_page':32,'reproduced_value':None,'status':'point_cell_overlap_would_be_a_different_statistic'}]),out/'overlap_comparability.csv')
    decision=feasibility_report(hives)
    (out/'feasibility.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
    from pypdf import PdfReader
    reader=PdfReader(args.pdf);text='\n'.join(p.extract_text() for p in reader.pages)
    evidence={'source_url':SOURCE_URL,'pdf_sha256':sha256(args.pdf),'pages':62,'appendix_pages':list(range(50,60)),
      'extracted_rows':len(frame),'dual_pdf_parser_all_cells_agree':True,'visually_checked_rows':len(manual),
      'public_open_access_checkbox_page':2,'explicit_reuse_license_found':False,'pdf_in_repository':False,
      'derived_records_redistribution_requires_human_rights_review':True,
      'crs_terms_found':sorted(set(__import__('re').findall(r'\b(?:EPSG\s*:?\s*\d+|WGS\s*84|ETRS\s*89|UTM)\b',text,flags=__import__('re').I))),
      'geopdf_reference_available':any('/VP' in p or '/LGIDict' in p for p in reader.pages),'embedded_data_files':list(reader.attachments),
      'year_conflict':{'methods_and_appendix':2017,'results_page_27_written_year':2018,'action':'preserve_source_dates_2017; flag_text_typo_not_correct_rows'},
      'published_sampling':'28 filming dates, 1-2 h/hive/day, selected suitable weather; not continuous observation',
      'uncertainty':'Sussex calibration; 1000 modeled distances/headings per dance; von Mises kappa=24.9; posterior rasters not included',
      'coordinate_hypotheses':['EPSG:25832','EPSG:32632'],'project_crs':'EPSG:25833',
      'conditional_coverage_rule':'point center covered_by original 737-park union; no RU or coordinate assertion',
      'bootstrap_seed_for_descriptive_data_only':20261108,'bootstrap_unit':'filming_date',
      'simulation_seed_bank':'not_generated_because_feasibility_checkpoint_failed',
      'module_location_reason':'analysis directory avoids changing engine hash which includes every project2/*.py'}
    (out/'source_audit.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    findings=[
      ['Georreferenciación pendiente','0 CRS declarados y 0 archivos GIS adjuntos en PDF','Falta proyecto R/QGIS o metadatos','No inicializar colmenas verificadas','Solicitar CRS/datum y coordenadas originales','Esencial'],
      ['Dos colmenas cercanas: discrepancia','Orígenes implícitos separados 3,010 unidades vs ~0,2 m en texto','Redondeo o procesamiento por aclarar','No fijar ni colapsar dos sitios inventados','Confirmar ambos orígenes con fuente primaria','Esencial'],
      ['Calidad de registros','506 filas; 1 distancia negativa, 2 relojes inválidos, 5 discrepancias de IDs','Transcripción/procesamiento de fuente por revisar','Filtros separados y trazabilidad por fila','No reparar automáticamente; pedir aclaración','Alta'],
      ['Cobertura temporal parcial','216/506 filas dentro de 18 días, 9/10/8 fechas por colonia','Filmación selectiva con buen clima','No comparar todos los días/horas como observados','Alinear fechas, esfuerzo y selección de danzas','Alta'],
      ['Cola de distancias supera radio','Ullevål 1: 3/97 distancias puntuales >3 km; máximo 4205,4 m','Radio fijo podría truncar destinos','No asumir que 3 km cubre toda la muestra','Estudiar radio tras confirmar ubicaciones, sin ajustar para parecerse','Alta'],
      ['Posible falta de recursos fuera de parques','Bajo UTM32 supuesto: 89,66%/100%/96,88% fuera del catálogo','Jardines privados, campos u omisión cartográfica; no verificado individualmente','Cobertura condicional no equivale a ausencia de flores','Confirmar CRS y auditar catálogo de recursos urbanos','Alta'],
      ['Solapamiento no comparable','Jaccard publicado 0,50/0,39; sin superficies originales','Puntos del anexo no son nubes de probabilidad','No comparar con competition_pressure ni ocupación puntual','Obtener rásteres de probabilidad y rejilla','Alta'],
      ['Proceso de observación no modelado','1–2 h/colmena/día con buen clima; danzas tras forrajeo rentable','Sesgo de selección de retornos y recurso','Todos los viajes del motor no son todas las danzas','Diseñar operador de observación separado','Alta'],
      ['Competencia externa ausente','3 colonias de ~60000 abejas adicionales citadas en Sogn; observadas ~5000/colonia','Entorno no representado por solo nuestras colonias','Presión interna no mide competencia ecológica total','Investigar presión externa/reclutamiento con evidencia adicional','Media'],
      ['Fuente NINA numérica adicional','GeoTIFF nativo 1 m, EPSG:25832, licencia CC-BY 4.0, contexto 2022','Catálogo distinto del servicio TilesOnly','No reemplazar ni convertir índice a RU','Resolver semántica/rango y evaluar resumen nativo','Media'],
      ['Optimización conserva alcance','70 seeds históricas y archivos originales no modificados','Validación histórica todavía no habilitada','No afirmar NSGA-II validado en realidad','No repetir búsqueda ahora; nueva identidad solo si cambia modelo','Alta']]
    save_csv(pd.DataFrame(findings,columns=['Hallazgo','Evidencia cuantitativa','Posible causa',
      'Implicación para el modelo','Cambio recomendado','Prioridad']),out/'findings_recommendations.csv')
    save_csv(pd.DataFrame([
      ['Observaciones por colonia','completo','observations_by_colony.csv'],
      ['Incluidos/excluidos','completo_con_filtros_separados','inclusion_exclusion.csv'],
      ['Cobertura de parques','solo_condicional_CRS_no_verificado','park_coverage_conditional.csv'],
      ['Distancias observadas y simuladas','solo_observadas; simulación_no_habilitada','observed_distances.csv'],
      ['Errores absolutos/relativos del simulador','no_calculados_por_falta_de_correspondencia_verificada','No sustituir con diferencias entre estimandos del PDF'],
      ['Resultados por semilla histórica','no_generados; 0 simulaciones','El checkpoint detuvo la fase experimental'],
      ['Solapamiento comparable','no_reproducible_con_datos_disponibles','overlap_comparability.csv'],
      ['Limitaciones/mejoras','completo','findings_recommendations.csv']],
      columns=['requested_output','status','evidence_or_reason']),out/'requested_outputs_status.csv')
    # Every plot below is backed by the exported tables above.
    fig,ax=plt.subplots(figsize=(10,4))
    for colony,color in zip(COLONIES,['#b68d34','#287c68','#697ab7']):
        values=frame.loc[frame.colony.eq(colony)&frame.distance_analysis_eligible,'distance_m']
        ax.hist(values,bins=np.arange(0,4501,250),histtype='step',lw=2,label=f'{colony} (n={len(values)})',color=color)
    ax.set(xlabel='Distancia puntual del anexo (m)',ylabel='Danzas',title='18 julio–4 agosto 2017: estimaciones de danzas, no vuelos GPS')
    ax.legend();fig.tight_layout();fig.savefig(out/'observed_distance_distribution.png',dpi=150);plt.close(fig)
    # Coordinate display is explicitly conditional, never used to initialize hives.
    import geopandas as gpd
    parks=gpd.read_file(processed/'oslo_parks.geojson').to_crs(25833)
    fig,ax=plt.subplots(figsize=(8,7));parks.plot(ax=ax,color='#d7e4d5',edgecolor='#aac0a7',linewidth=.2)
    for colony,color in zip(COLONIES,['#b68d34','#287c68','#697ab7']):
        d=details.loc[details.assumed_epsg.eq(25832)&details.colony.eq(colony)]
        ax.scatter(d.project_x_m_conditional,d.project_y_m_conditional,s=10,alpha=.6,color=color,label=colony)
    ax.set(xlabel='Easting condicional EPSG:25833 (m)',ylabel='Northing condicional EPSG:25833 (m)',
      title='Solo diagnóstico: fuente SUPUESTA EPSG:25832\nCRS y colmenas históricas SIN VERIFICAR')
    ax.legend();fig.tight_layout();fig.savefig(out/'conditional_park_coverage.png',dpi=150);plt.close(fig)
    print(pd.DataFrame(inventory).to_string(index=False));print(json.dumps(decision,indent=2))

if __name__=='__main__':main()
