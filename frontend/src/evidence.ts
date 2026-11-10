import type {Candidate,Resource,Row,Run} from './types';

export const parameterHelp:Record<string,string>={
 K:'Presupuesto de colonias. La media de oportunidades se conserva por colmena, por lo que cambia el total.',
 resource_factor:'Multiplica el stock inicial sintético base de 1 000 RU; se reparte por superficie exclusiva.',
 regeneration:'Fracción del recurso inicial que se agrega al cierre; no del stock restante.',
 radius_m:'Límite entre puntos representativos de colmena y parche, en metros.',
 alpha:'Peso de otras colonias activas al seleccionar parche; no mide presión de abejas silvestres.',
 beta:'Exponente adimensional que penaliza distancia en la selección probabilística.',
 departures:'Media Poisson de oportunidades por colmena y día; no representa una población finita de abejas.',
 demand_mean:'Media de demanda exponencial de recurso sintético por viaje; la disponibilidad limita el consumo.',
 speed_m_s:'Convierte distancia en tiempo de viaje; no cambia la velocidad visual del reproductor.'
};

export const finite=(x:unknown):x is number=>typeof x==='number'&&Number.isFinite(x);
export function percentChange(value:unknown,base:unknown):number|null {
 return finite(value)&&finite(base)&&base!==0?100*(value-base)/Math.abs(base):null;
}
export function resourceDays(run:Run|null):Row[]{
 return run?.days.map(d=>({date:d.date,initial:d.initial.reduce((a,b)=>a+b,0),consumption:d.consumption,
  regeneration:d.regeneration,final:d.final.reduce((a,b)=>a+b,0)}))??[];
}
export function siteChecks(ids:string[],candidates:Candidate[],K=5){
 const selected=ids.map(id=>candidates.find(s=>s.site_id===id));
 return {count:ids.length,expected:K,valid:selected.every(Boolean)&&ids.length===K,
  distinctIds:new Set(ids).size===ids.length,
  distinctCoordinates:new Set(selected.filter(Boolean).map(s=>`${s!.x_m},${s!.y_m}`)).size};
}
export function accessDistances(patch:Resource|undefined,ids:string[],candidates:Candidate[]):Row[]{
 if(!patch)return [];
 return ids.flatMap(id=>{const s=candidates.find(s=>s.site_id===id);return s?[{site_id:id,
  distance_m:Math.hypot(s.x_m-patch.resource_x_m,s.y_m-patch.resource_y_m)}]:[]});
}
export function conditionComparison(summary:Row[],paired:Row[],condition:string,metric:string):Row[]{
 return ['RANDOM','GREEDY','NSGA2'].map(method=>{
  const a=summary.find(r=>r.condition===condition&&r.method===method&&r.metric===metric);
  const b=summary.find(r=>r.condition==='base'&&r.method===method&&r.metric===metric);
  const p=paired.find(r=>r.condition===condition&&r.method===method&&r.metric===metric);
  return {method,base:b?.mean??null,selected:a?.mean??null,std:a?.std??null,
   ci_lower:a?.ci_lower??null,ci_upper:a?.ci_upper??null,n:a?.n??null,
   difference:finite(a?.mean)&&finite(b?.mean)?a.mean-b.mean:null,
   percent:percentChange(a?.mean,b?.mean),difference_ci_low:condition==='base'&&a?0:p?.ci_lower??null,
   difference_ci_high:condition==='base'&&a?0:p?.ci_upper??null};
 });
}
export function solutionComparison(summary:Row[],solution:Row,metric:string):Row[]{
 return ['RANDOM','GREEDY'].map(method=>{
  const baseline=summary.find(r=>r.method===method&&r.metric===metric)?.mean;
  return {baseline:method,reference:baseline??null,selected:solution[metric]??null,
   difference:finite(baseline)&&finite(solution[metric])?solution[metric]-baseline:null,
   percent:percentChange(solution[metric],baseline)};
 });
}
