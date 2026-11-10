import {useState} from 'react';
import type {Comparison,Landscape,Row,Sensitivity,Validation} from '../types';
import {metricLabels} from '../api';
import {conditionComparison,siteChecks,solutionComparison} from '../evidence';
import {Panel,Notice,DataTable,DownloadCSV} from './Common';

export function SolutionEvidence({comparison,landscape,selected,metric}:{comparison:Comparison;landscape:Landscape;selected:string;metric:string}){
 const solution=comparison.nsga_installations.find(s=>s.solution_id===selected);
 const front=comparison.front.solutions.find(s=>s.solution_id===selected);
 if(!solution||!front)return <Notice>No hay una solución archivada con este identificador.</Notice>;
 const checks=siteChecks(front.site_ids,landscape.candidates);
 return <Panel title={`Evaluación de ${selected}`} eyebrow="UBICACIONES CONGELADAS · MOTOR 1.1.0">
  <div className="checks" aria-label="Restricciones de la solución"><span>{checks.count}/5 colmenas</span><span>{checks.valid?'Sitios candidatos válidos':'Revisar candidatos'}</span><span>{checks.distinctIds?'IDs distintos':'IDs repetidos'}</span><span>{checks.distinctCoordinates} coordenadas distintas</span></div>
  <p>Los candidatos proceden de polígonos sin intersección con restricciones. El contrato exige IDs distintos, pero permite coordenadas coincidentes; esto no prueba separación física entre colmenas.</p>
  <DataTable rows={Object.keys(metricLabels).map(m=>({metric:metricLabels[m].name,value:solution[m],unit:metricLabels[m].unit}))} columns={[{key:'metric',label:'Métrica'},{key:'value',label:'Media de 70 seeds'},{key:'unit',label:'Unidad'}]}/>
  <h3>{metricLabels[metric].name}: cambios de medias frente a referencias</h3>
  <DataTable rows={solutionComparison(comparison.summary,solution,metric)} columns={[{key:'baseline',label:'Referencia'},{key:'reference',label:'Media referencia'},{key:'selected',label:'Media seleccionada'},{key:'difference',label:'Cambio absoluto'},{key:'percent',label:'Cambio (%)'}]}/>
  <p>Estos cambios son descriptivos; no se asignan los IC de pareto_047 a otra solución. El signo no determina mejora: recurso ↑, distancia y presión ↓; menos parches no es automáticamente mejor.</p>
  <p><b>pareto_047:</b> elección ilustrativa por distancia normalizada al ideal, pesos iguales y medias de búsqueda congeladas. Explorar otra solución no cambia la comparación oficial ni demuestra un óptimo global.</p>
  <details><summary>Recurso por colmena: qué tenemos</summary><p>Promedio, mínimo y Jain están disponibles para cada solución en la tabla. No hay una serie archivada de las cinco entregas individuales para cada alternativa y sus 70 seeds; no se reconstruye a partir del promedio. Las entregas individuales de las demos 1.1.1 se muestran en Movimiento, con otra identidad.</p></details>
 </Panel>;
}

export function SelectedValidation({validation}:{validation:Validation}){
 return <>
  <Panel title="Tres niveles de evidencia"><div className="three"><div><h3>Verificación interna</h3><p>Restricciones, balances y reproducibilidad del código. No demuestra fidelidad ecológica.</p></div><div><h3>Contraste observacional</h3><p>Datos reales y referentes con límites explícitos. Dietz es descriptivo; Dryad evalúa predictores independientes.</p></div><div><h3>Validación predictiva</h3><p>No lograda para el motor de colmenas. Faltan mediciones equivalentes y evaluación independiente.</p></div></div></Panel>
  <Panel title="Dietz: distancias anunciadas mediante danzas" eyebrow="216 REGISTROS · 18 JULIO–4 AGOSTO 2017">
   <DataTable rows={validation.dietz} columns={[{key:'colony',label:'Colonia'},{key:'n_valid_distances',label:'Registros'},{key:'n_film_dates',label:'Fechas'},{key:'mean_point_distance_m',label:'Media (m)',digits:2},{key:'median_point_distance_m',label:'Mediana (m)'},{key:'p95_point_distance_m',label:'P95 (m)'},{key:'mean_cluster_bootstrap_ci95_low_m',label:'IC media inferior (m)'},{key:'mean_cluster_bootstrap_ci95_high_m',label:'IC media superior (m)'}]}/>
   <p>10 fechas distintas, 27 combinaciones colonia-fecha y 215 relojes válidos. Danzas seleccionadas con tiempo favorable; no son 216 abejas independientes ni GPS. IC descriptivos por fecha de filmación, sin incertidumbre completa de decodificación.</p>
   <Notice>No emparejamos estas tres colonias con nuestras cinco colmenas. Las medias no se utilizan para calcular un error predictivo del simulador.</Notice>
   <div className="inline"><DownloadCSV name="dietz" label="Resumen Dietz"/><a href={validation.sources.sources.Dietz} target="_blank" rel="noreferrer">Fuente Dietz (2018) ↗</a></div>
  </Panel>
  <Panel title="NINA: investigación cerrada" eyebrow="REFERENCIA COMPLEMENTARIA"><p><b>{validation.nina.decision}</b></p><p>{validation.nina.reason} Mayor idoneidad tampoco demostraría menor impacto sobre polinizadores silvestres. No se incorporan rásteres ni puntuaciones de calidad.</p></Panel>
  <Panel title="Correspondencia entre motor y observaciones"><DataTable rows={validation.correspondence.map(r=>({...r,metric:metricLabels[r.metric]?.name??r.metric}))} columns={[{key:'metric',label:'Métrica del simulador'},{key:'reference',label:'Referencia observada'},{key:'unit',label:'Unidad del motor'},{key:'correspondence',label:'Correspondencia'},{key:'limitation',label:'Limitación'}]}/><DownloadCSV name="correspondence" label="Matriz de correspondencia"/></Panel>
 </>;
}

export function SensitivityComparator({data}:{data:Sensitivity}){
 const [condition,setCondition]=useState(data.metadata.conditions.find((c:Row)=>c.parameters.max_foraging_distance_m===1500)?.condition??'base'),[metric,setMetric]=useState('total_resource_obtained');
 const conditions:Row[]=data.metadata.conditions;
 const chosen=conditions.find(c=>c.condition===condition)??conditions[0];
 const current=chosen.condition;
 const parameters=chosen.parameters;
 return <Panel title="Base frente a condición seleccionada" eyebrow={`EXPERIMENTO ARCHIVADO · ${data.metadata.engine_version}`}>
  <div className="two"><label className="field">Condición archivada<select aria-label="Condición archivada" value={current} onChange={e=>setCondition(e.target.value)}>{conditions.map(c=><option key={c.condition}>{c.condition}</option>)}</select></label><label className="field">Métrica de sensibilidad<select aria-label="Métrica de sensibilidad" value={metric} onChange={e=>setMetric(e.target.value)}>{['total_resource_obtained','min_resource_per_hive','mean_distance_m','competition_pressure','hive_balance_jain'].map(m=><option key={m} value={m}>{metricLabels[m].name} ({metricLabels[m].unit})</option>)}</select></label></div>
  <p>Base propia de 1.1.1, K=5. Condición seleccionada: K={parameters.K}, radio {parameters.max_foraging_distance_m} m, recurso inicial {parameters.initial_resource_total} RU, regeneración {parameters.regeneration_rate} × inicial/día.</p>
  <DataTable rows={conditionComparison(data.summary,data.paired,current,metric)} columns={[{key:'method',label:'Método'},{key:'base',label:'Media base'},{key:'selected',label:'Media condición'},{key:'std',label:'DE condición'},{key:'n',label:'Seeds'},{key:'ci_lower',label:'IC condición inferior'},{key:'ci_upper',label:'IC condición superior'},{key:'difference',label:'Cambio absoluto'},{key:'percent',label:'Cambio (%)'},{key:'difference_ci_low',label:'IC cambio inferior'},{key:'difference_ci_high',label:'IC cambio superior'}]}/>
  <p>Unidades: {metricLabels[metric].unit}. Porcentaje no definido si la base es cero; IC del cambio absoluto pareado, no del porcentaje. No disponible indica una condición sin ese método, no cero.</p>
  <h3>Desempeño por colmena cuando cambia K</h3><DataTable rows={data.per_hive_summary.filter(r=>r.condition===current)} columns={[{key:'method',label:'Método'},{key:'K',label:'K'},{key:'mean_resource_per_hive',label:'Media por colmena (RU)'},{key:'std_resource_per_hive',label:'DE entre seeds'},{key:'min_resource_per_hive',label:'Media del mínimo (RU)'},{key:'hive_balance_jain',label:'Jain medio'}]}/>
  <Notice>RANDOM conserva una seed de selección; GREEDY recalcula sitios; NSGA-II conserva pareto_047 y no se reoptimiza. No existen resultados NSGA-II para K=3/8. Aumentar K aumenta también las oportunidades totales de viaje.</Notice>
 </Panel>;
}

export function Glossary(){return <Panel title="Glosario para interpretar los resultados"><div className="glossary">{[
 ['RU','Unidad sintética de recurso. No equivale a una flor, gramo de néctar ni polinización.'],
 ['Radio','Distancia máxima de ida permitida por el escenario, en metros.'],
 ['Regeneración','Fracción del stock inicial que se agrega al cierre de cada día.'],
 ['Competencia','Fracción de intentos con otra colonia activa en el parche al iniciar forrajeo. No mide impacto en abejas silvestres.'],
 ['Pareto','Compromisos no dominados durante búsqueda: mejorar un objetivo puede empeorar otro.'],
 ['Semillas','Controlan el azar reproducible. Las comunes permiten contrastes pareados; no son colonias reales nuevas.'],
 ['Jain','Equilibrio de entregas entre colmenas, de 1/K a 1; no definido si la entrega total es cero.']
 ].map(([term,definition])=><details key={term}><summary>{term}</summary><p>{definition}</p></details>)}</div></Panel>}
