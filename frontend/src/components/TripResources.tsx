import {useState} from 'react';
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,CartesianGrid,Tooltip,Legend} from 'recharts';
import type {Run,Landscape,Trip} from '../types';
import {fmt} from '../api';
import {resourceDays} from '../evidence';
import {Panel,Notice,Stat,DataTable,DownloadRows} from './Common';

const key=(t:Trip)=>`${t.hive_slot}-${t.trip_slot}`;
export function TripInspector({run,date,landscape,selected,onSelect}:{run:Run|null;date:string;landscape:Landscape;selected:string;onSelect:(id:string)=>void}){
 const [hive,setHive]=useState('all');
 const trips=run?.trips.filter(t=>t.date===date&&(hive==='all'||t.hive_slot===Number(hive)))??[];
 const trip=trips.find(t=>key(t)===selected)??trips[0];
 const eventTime=(event:string)=>{const e=run?.events.find(e=>e.date===date&&e.hive_slot===trip?.hive_slot&&e.trip_slot===trip?.trip_slot&&e.event===event);return e?`${fmt(e.time_min,2)} min`:'No registrado'};
 const park=landscape.parks.features.find(p=>p.properties?.patch_id===trip?.patch_id)?.properties;
 return <Panel title="Inspector de viajes" eyebrow="REGISTROS DEL MOTOR · MINUTOS DESDE EL INICIO DEL DÍA">
  <div className="two"><label className="field">Filtrar colmena<select value={hive} onChange={e=>setHive(e.target.value)}><option value="all">Todas las colmenas</option>{run?.sites.map((_,i)=><option key={i} value={i}>Colmena {i+1}</option>)}</select></label>
  <label className="field">Viaje del día<select aria-label="Viaje del día" disabled={!trips.length} value={trip?key(trip):''} onChange={e=>onSelect(e.target.value)}>{!trips.length&&<option value="">Sin viajes</option>}{trips.map(t=><option key={key(t)} value={key(t)}>Colmena {t.hive_slot+1} · viaje {t.trip_slot+1} · salida {fmt(t.departure_min)} min</option>)}</select></label></div>
  {trip?<><p><b>{date}</b> · Colmena {trip.hive_slot+1} · {park?.display_name||park?.Navn||'Parque sin nombre'}</p><p className="mono">Origen: {trip.site_id}<br/>Parche: {trip.patch_id}</p>
  <DataTable rows={[
   {variable:'Salida registrada',value:eventTime('departure')},{variable:'Llegada registrada',value:eventTime('arrival')},
   {variable:'Inicio de recolección',value:eventTime('foraging_start')},{variable:'Final de recolección',value:eventTime('foraging_end')},
   {variable:'Regreso registrado',value:eventTime('return')},{variable:'Regreso exitoso dentro del día',value:trip.returned?'Sí':'No'},
   {variable:'Distancia de ida del log (m)',value:trip.one_way_distance_m??null},
   {variable:'Recurso consumido (synthetic_RU)',value:trip.resource_consumed},
   {variable:'Recurso entregado (synthetic_RU)',value:trip.resource_delivered}
  ]} columns={[{key:'variable',label:'Variable'},{key:'value',label:'Valor'}]}/>
  <p>Consumo y entrega pueden diferir si el viaje no regresa dentro del día. Los tiempos mostrados provienen de eventos registrados; una llegada o regreso programado no se presenta como observado.</p></>:<Notice>No hay viajes registrados para este día y filtro. No se inventan trayectos.</Notice>}
  <DownloadRows rows={trips.map(t=>({...t}))} name={`viajes-${run?.method}-${date}-seed-${run?.provenance.seed}.csv`} label="Descargar viajes filtrados"/>
  <p className="chart-note">Selecciona también un ícono del mapa. Cada ícono representa un viaje simulado, no una abeja identificada ni una trayectoria GPS.</p>
 </Panel>;
}

export function ResourceEvolution({run,date}:{run:Run|null;date:string}){
 const days=resourceDays(run),selected=days.find(d=>d.date===date);
 if(!selected)return <Notice>No hay balances de recursos disponibles.</Notice>;
 return <Panel title="Recursos durante los 18 días" eyebrow={`BALANCES ARCHIVADOS · ${run?.provenance.engine_version}`}>
  <p>Para cada día: stock final = stock inicial − consumo + regeneración. Son cantidades sintéticas del modelo; la regeneración se agrega al cierre y no representa floración medida.</p>
  <div className="stats-grid">{[['initial','Stock inicial'],['consumption','Consumo'],['regeneration','Regeneración'],['final','Stock final']].map(([field,label])=><Stat key={field} label={`${label} · ${date}`} value={fmt(selected[field])} unit="RU"/>)}</div>
  <ResponsiveContainer width="100%" height={300}><LineChart data={days} margin={{left:5,right:20,bottom:25}}><CartesianGrid stroke="#e4e9e1"/><XAxis dataKey="date" tickFormatter={x=>String(x).slice(5)} label={{value:'Fecha de simulación',position:'insideBottom',offset:-15}}/><YAxis width={65} label={{value:'synthetic_RU',angle:-90,position:'insideLeft'}}/><Tooltip/><Legend verticalAlign="top"/>
   <Line dataKey="initial" name="Stock inicial" stroke="#7381b5" dot={false}/><Line dataKey="consumption" name="Consumo" stroke="#b98b37" dot={false}/><Line dataKey="regeneration" name="Regeneración" stroke="#aa6970" dot={false}/><Line dataKey="final" name="Stock final" stroke="#397b67" strokeWidth={2} dot={false}/>
  </LineChart></ResponsiveContainer>
  <DownloadRows rows={days.map(d=>({...d,method:run?.method,seed:run?.provenance.seed,engine_version:run?.provenance.engine_version}))} name={`recursos-${run?.method}-seed-${run?.provenance.seed}.csv`} label="Descargar balances diarios"/>
  <details><summary>Ver balances diarios numéricos</summary><DataTable rows={days} columns={[{key:'date',label:'Fecha'},{key:'initial',label:'Inicial (RU)'},{key:'consumption',label:'Consumo (RU)'},{key:'regeneration',label:'Regeneración (RU)'},{key:'final',label:'Final (RU)'}]}/></details>
  <Panel title="Entregas por colmena de esta corrida"><DataTable rows={run?.per_hive.map(r=>({...r,hive:Number(r.hive_slot)+1}))??[]} columns={[{key:'hive',label:'Colmena'},{key:'site_id',label:'Sitio'},{key:'resource_delivered',label:'Entregado (RU)'}]}/><p>Una corrida {run?.method}, seed {run?.provenance.seed}, motor 1.1.1. No son promedios de las 70 réplicas históricas.</p></Panel>
 </Panel>;
}
