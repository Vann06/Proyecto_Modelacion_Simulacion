export async function api<T>(path:string,body?:unknown):Promise<T> {
  const response=await fetch('/api/'+path,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!response.ok){let detail='No fue posible obtener los datos';try{detail=JSON.stringify((await response.json()).detail)}catch{/* retain friendly fallback */}throw new Error(detail)}
  return response.json();
}
export function fmt(value:number|null|undefined,digits=1){return value==null||!Number.isFinite(value)?'No definido':value.toLocaleString('es-GT',{maximumFractionDigits:digits})}
export const metricLabels:Record<string,{name:string;unit:string;direction:string}>={
 total_resource_obtained:{name:'Recurso entregado',unit:'synthetic_RU',direction:'↑'},
 mean_resource_per_hive:{name:'Promedio por colmena',unit:'synthetic_RU',direction:'↑'},
 min_resource_per_hive:{name:'Mínimo por colmena',unit:'synthetic_RU',direction:'↑'},
 mean_distance_m:{name:'Distancia media de ida',unit:'m',direction:'↓'},
 total_distance_m:{name:'Distancia total de ida',unit:'m',direction:'↓'},
 p95_distance_m:{name:'P95 de distancia de ida',unit:'m',direction:'↓'},
 competition_pressure:{name:'Presión de competencia',unit:'fracción [0,1]',direction:'↓'},
 hive_balance_jain:{name:'Equilibrio entre colmenas',unit:'índice Jain',direction:'↑'},
 patches_used_count:{name:'Parches utilizados',unit:'parches',direction:'diagnóstico'}};
