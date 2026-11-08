import {ResponsiveContainer,BarChart,Bar,XAxis,YAxis,CartesianGrid,Tooltip,ErrorBar,Cell,LineChart,Line,Legend,ScatterChart,Scatter,ZAxis} from 'recharts';
import type {Row} from '../types';
import {fmt} from '../api';
const palette=['#b98b37','#397b67','#7381b5'];
export function ComparisonBars({rows,metric,unit}:{rows:Row[];metric:string;unit:string}){const d:Row[]=rows.filter(r=>r.metric===metric).map(r=>({...r,error:[r.mean-r.ci95_low,r.ci95_high-r.mean]}));return <div className="chart"><ResponsiveContainer width="100%" height={270}><BarChart data={d} margin={{top:16,right:18,left:0,bottom:10}}><CartesianGrid vertical={false} stroke="#e9ece6"/><XAxis dataKey="method" tickLine={false}/><YAxis tickFormatter={n=>fmt(n,0)} width={54}/><Tooltip formatter={v=>[fmt(Number(v)),unit]}/><Bar dataKey="mean" name={unit} radius={[5,5,0,0]} maxBarSize={65}><ErrorBar dataKey="error" width={7} stroke="#29483f"/>{d.map((r,i)=><Cell key={r.method} fill={palette[i%3]}/>)}</Bar></BarChart></ResponsiveContainer><p className="chart-note">Media · {unit} · IC 95% condicionales</p></div>}
export function Pareto({rows,selected,onSelect}:{rows:Row[];selected:string;onSelect:(id:string)=>void}){const d=rows.filter(r=>!r.physical_duplicate);return <ResponsiveContainer width="100%" height={310}><ScatterChart margin={{top:16,right:25,bottom:30,left:15}}><CartesianGrid strokeDasharray="3 3" stroke="#e4e9e1"/><XAxis type="number" dataKey="mean_distance_m" name="Distancia de ida" unit=" m" domain={['dataMin - 20','dataMax + 20']} tickFormatter={n=>fmt(n,0)}/><YAxis type="number" dataKey="total_resource_obtained" name="Recurso entregado" domain={['dataMin - 5','dataMax + 5']} tickFormatter={n=>fmt(n,0)}/><ZAxis range={[65,65]}/><Tooltip cursor={{strokeDasharray:'3 3'}} formatter={(v,n)=>[fmt(Number(v)),n]}/><Scatter name="Alternativas físicas" data={d} onClick={(p:any)=>onSelect(p.solution_id)}>{d.map(r=><Cell key={r.solution_id} fill={r.solution_id===selected?'#d69a2f':'#628d7b'} stroke={r.solution_id===selected?'#1b4037':'white'} strokeWidth={2}/>)}</Scatter></ScatterChart></ResponsiveContainer>}
export function Convergence({rows}:{rows:Row[]}){return <ResponsiveContainer width="100%" height={250}><LineChart data={rows} margin={{right:20,left:0,bottom:10}}><CartesianGrid stroke="#e4e9e1"/><XAxis dataKey="generation" label={{value:'Generación',position:'insideBottom',offset:-6}}/><YAxis width={60}/><Tooltip/><Legend verticalAlign="top"/><Line type="monotone" dataKey="best_total_resource_obtained" name="Mejor recurso en búsqueda (RU)" stroke="#397b67" dot={false}/></LineChart></ResponsiveContainer>}
export function SensitivityPlot({rows,metric}:{rows:Row[];metric:string}) {
 const order=['base','resource_low','resource_high','K3','K8','competition_off','competition_high','radius_short','radius_long','regeneration_off','regeneration_high','distance_low','distance_high','activity_high'];
 const available=new Set(rows.filter(r=>r.metric===metric).map(r=>r.condition));
 const conditions=order.filter(c=>available.has(c));
 const data=conditions.map(c=>({condition:c,...Object.fromEntries(rows.filter(r=>r.condition===c&&r.metric===metric).map(r=>[r.method,r.mean]))}));
 return <div className="chart" style={{overflowX:'auto'}}>
  <div style={{minWidth:900}}>
   <ResponsiveContainer width="100%" height={355}>
    <BarChart data={data} margin={{top:20,right:16,left:0,bottom:78}} barGap={2}>
     <CartesianGrid vertical={false} stroke="#e4e9e1"/>
     <XAxis dataKey="condition" angle={-38} textAnchor="end" interval={0} tick={{fontSize:10}}/>
     <YAxis width={65} tickFormatter={n=>fmt(n,0)}/>
     <Tooltip formatter={v=>fmt(Number(v))}/>
     <Legend verticalAlign="top"/>
     {['RANDOM','GREEDY','NSGA2'].map((m,i)=><Bar key={m} dataKey={m} name={m==='NSGA2'?'NSGA-II congelado':m} fill={palette[i]} maxBarSize={24}/>)}
    </BarChart>
   </ResponsiveContainer>
  </div>
  <p className="chart-note">Cada grupo es una condición independiente de sensibilidad (OAT), no una serie temporal. NSGA-II no fue recalculado ni tiene resultados para K=3/8.</p>
 </div>;
}
