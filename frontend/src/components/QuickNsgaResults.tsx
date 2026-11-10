import {ResponsiveContainer,ScatterChart,Scatter,XAxis,YAxis,CartesianGrid,Tooltip,Cell,ZAxis} from 'recharts';
import type {QuickJob,QuickSolution} from '../types';
import {fmt,metricLabels} from '../api';
import './quickNsga.css';

export function QuickNsgaResults({job,selected,onSelect,onSimulate,running,replicationId,error}:{job:QuickJob|null;selected:string;onSelect:(id:string)=>void;onSimulate:()=>void;running:boolean;replicationId:number;error:string}){
 const solutions=job?.result?.solutions??[];
 const chosen=solutions.find(s=>s.solution_id===selected);
 const complete=job?.status==='completed';
 const points=solutions.map(s=>({...s,...s.search_means}));
 return <div className="quick-nsga">
  <p className="chart-note">8 individuos · 5 generaciones · 2 seeds (réplicas 1–2) · cruce 0.90 · mutación 0.20 · seed 2026. Máximo 96 simulaciones y 15 minutos. Una búsqueda local a la vez.</p>
  {error&&<p role="alert">{error}</p>}
  {job&&<div role="status" className="quick-progress"><b>{job.status==='completed'?'Búsqueda finalizada':job.status==='failed'?'Búsqueda fallida':job.status==='interrupted'?'Búsqueda interrumpida':'Búsqueda en curso'}</b><dl><dt>Generaciones completadas</dt><dd>{job.generation??0} / 5</dd><dt>Instalaciones evaluadas</dt><dd>{job.installations??0}</dd><dt>Simulaciones realizadas</dt><dd>{job.simulations??0} / 96</dd><dt>Tiempo transcurrido</dt><dd>{fmt(job.elapsed_s??0,1)} s</dd><dt>No dominadas {complete?'finales':'provisionales'}</dt><dd>{job.front_size??0}</dd></dl>{job.error&&<p role="alert">{job.error}</p>}</div>}
  {complete&&<><h3>Optimización exploratoria rápida — NSGA-II</h3><p>Frente nuevo · K={job.result!.K} · promedios de dos semillas de búsqueda. Independiente del frente histórico K=5.</p>
   {solutions.length>0?<>
    <div className="quick-pareto" aria-label="Frente de Pareto exploratorio: distancia media de ida en metros y recurso entregado en RU"><ResponsiveContainer width="100%" height={265}><ScatterChart margin={{top:12,right:12,left:0,bottom:35}}><CartesianGrid strokeDasharray="3 3"/><XAxis type="number" dataKey="mean_distance_m" domain={['dataMin - 20','dataMax + 20']} name="Distancia media de ida" unit=" m" tickFormatter={n=>fmt(n,0)} label={{value:'Distancia media de ida (m)',position:'insideBottom',offset:-20,fontSize:10}}/><YAxis type="number" dataKey="total_resource_obtained" domain={['dataMin - 5','dataMax + 5']} name="Recurso entregado" unit=" RU" width={48} tickFormatter={n=>fmt(n,0)}/><ZAxis range={[85,85]}/><Tooltip formatter={(v,n)=>[fmt(Number(v),2),n]}/><Scatter name="Instalaciones rápidas · RU" data={points} onClick={point=>onSelect((point.payload as QuickSolution).solution_id)}>{points.map(p=><Cell key={p.solution_id} fill={p.solution_id===selected?'#7c4824':'#d3a34e'} stroke="#fff6df" strokeWidth={2}/>)}</Scatter></ScatterChart></ResponsiveContainer></div>
    <small>Eje Y: recursos totales entregados (RU). Cada punto es una instalación; puede existir un único punto.</small>
    <label className="field">Solución rápida<select aria-label="Solución rápida" value={selected} onChange={e=>onSelect(e.target.value)}><option value="">Selecciona un punto o una solución</option>{solutions.map(s=><option key={s.solution_id} value={s.solution_id}>{s.solution_id} · K={s.K} · {fmt(s.search_means.total_resource_obtained,2)} RU · {fmt(s.search_means.mean_distance_m,1)} m</option>)}</select></label>
    {chosen&&<><div className="quick-selected"><b>{chosen.solution_id} · {chosen.K} colmenas</b><p>Vista previa de ubicaciones. Seleccionar no ejecuta búsquedas ni viajes.</p><ul>{chosen.site_ids.map(id=><li key={id}>{id}</li>)}</ul><details><summary>Promedios de búsqueda y otras métricas</summary><dl>{Object.entries(chosen.search_metrics).map(([key,value])=><div key={key}><dt>{metricLabels[key]?.name??key}</dt><dd>{fmt(value,3)} {metricLabels[key]?.unit??''}</dd></div>)}</dl></details></div><p>Simulación individual con réplica {replicationId} (31–100), usando la configuración guardada de esta búsqueda. Sus métricas se muestran aparte de estos promedios.</p><button className="button primary full" disabled={running} onClick={onSimulate}>{running?'Simulando…':'Simular solución seleccionada'}</button></>}
   </>:<p role="status">{job.result?.empty_reason??'Sin soluciones con objetivos definidos.'}</p>}
   <p className="chart-note">Cinco generaciones y dos seeds no demuestran óptimo global ni robustez estadística. Los cambios posteriores de sliders requieren una búsqueda nueva.</p>
  </>}
 </div>;
}

