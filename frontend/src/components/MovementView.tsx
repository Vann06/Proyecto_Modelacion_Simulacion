import {useEffect,useMemo,useState} from 'react';
import type {ReactNode} from 'react';
import {Play,Pause,RotateCcw,ArrowRight,MousePointer2,Route,Hexagon,Layers} from 'lucide-react';
import type {Landscape,Method,Run,Row} from '../types';
import {activeTrips,stocks} from '../visualization';
import {colonyColor,currentTripState,foragingActivity,sharedForagingWindows,sharedForagingEpisodes,sharedEpisodeCounts,tripKey,movementName} from '../movementModel';
import {MovementMap} from './MovementMap';
import type {MovementSelection} from './MovementMap';
import {TripInspector,ResourceEvolution} from './TripResources';
import {fmt,metricLabels} from '../api';
import {accessDistances} from '../evidence';
import {DataTable} from './Common';
import './movement.css';

interface Props {weather?:Row[];scenarioControls?:ReactNode;installationPreview?:{sites:string[];parameters:Run['parameters'];label:string};landscape:Landscape;run:Run|null;running:boolean;onLoadDemo:(method:Exclude<Method,'MANUAL'>)=>void;
 day:number;setDay:(day:number)=>void;minute:number;setMinute:(minute:number)=>void;
 playing:boolean;setPlaying:(playing:boolean)=>void;speed:number;setSpeed:(speed:number)=>void;}

export function MovementView({weather=[],scenarioControls,installationPreview,landscape,run:sourceRun,running,onLoadDemo,day,setDay,minute,setMinute,playing,setPlaying,speed,setSpeed}:Props){
 const run=useMemo(()=>installationPreview&&sourceRun?{...sourceRun,kind:'quick_nsga_preview',method:'NSGA2' as const,sites:installationPreview.sites,parameters:installationPreview.parameters,trips:[],events:[],days:[],per_hive:[],metrics:{}}:sourceRun,[sourceRun,installationPreview]);
 const [selection,setSelection]=useState<MovementSelection>({kind:'hive',slot:0});
 const [explorerOpen,setExplorerOpen]=useState(true);
 useEffect(()=>{setSelection({kind:'hive',slot:0});},[run]);
 const date=run?.days[day]?.date??'';
 const today=useMemo(()=>run?.trips.filter(t=>t.date===date)??[],[run,date]);
 const bees=useMemo(()=>activeTrips(run,date,minute,landscape.candidates,landscape.resources),[run,date,minute,landscape]);
 const stock=useMemo(()=>stocks(run,date,minute),[run,date,minute]);
 const activity=useMemo(()=>foragingActivity(today,date,minute),[today,date,minute]);
 const shared=useMemo(()=>sharedForagingWindows(today,date),[today,date]);
 const episodes=useMemo(()=>sharedForagingEpisodes(shared),[shared]);
 const episodeCounts=useMemo(()=>sharedEpisodeCounts(episodes,minute),[episodes,minute]);
 const totalEpisodes=[...episodeCounts.values()].reduce((sum,n)=>sum+n,0);
 const sharedNow=[...activity].filter(([,a])=>a.colonies.length>1);
 if(!run)return <div className="movement-view"><p role="status">No hay logs disponibles para reproducir.</p></div>;
 const dayMinutes=Number(run.parameters.day_minutes);
 const selectedTrip=selection?.kind==='trip'?today.find(t=>tripKey(t)===selection.key):undefined;
 const patchId=selection?.kind==='park'?selection.id:selectedTrip?.patch_id;
 const park=landscape.parks.features.find(f=>f.properties?.patch_id===patchId)?.properties;
 const parkName=movementName(park?.display_name||park?.Navn||patchId);
 const resource=landscape.resources.find(r=>r.patch_id===patchId);
 const totalArea=landscape.resources.reduce((sum,r)=>sum+r.exclusive_area_m2,0);
 const observedWeather=weather.find(w=>w.date===date);
 const hive=selection?.kind==='hive'?landscape.candidates.find(c=>c.site_id===run.sites[selection.slot]):undefined;
 const hiveTrips=selection?.kind==='hive'?today.filter(t=>t.hive_slot===selection.slot):[];
 const stages=[['Ida',bees.filter(b=>b.phase==='Ida').length],['Búsqueda',bees.filter(b=>b.phase==='Búsqueda').length],['Forrajeo',bees.filter(b=>b.phase==='Forrajeo').length],['Regreso',bees.filter(b=>b.phase==='Regreso').length]] as const;
 const go=(time:number)=>{setPlaying(false);setMinute(Math.max(0,Math.min(time,dayMinutes)));};
 const follow=()=>{const t=[...today].filter(t=>t.one_way_distance_m>0&&t.returned).sort((a,b)=>b.one_way_distance_m-a.one_way_distance_m)[0]??today[0];if(t){setSelection({kind:'trip',key:tripKey(t)});go(t.departure_min);}};
 const next=today.filter(t=>t.departure_min>minute).sort((a,b)=>a.departure_min-b.departure_min)[0];
 const eventTime=(kind:string)=>{const e=run.events.find(e=>e.date===date&&e.hive_slot===selectedTrip?.hive_slot&&e.trip_slot===selectedTrip?.trip_slot&&e.event===kind);return e?`${fmt(e.time_min,2)} min`:'Sin evento registrado';};
 return <div className="movement-view">
  <section className="movement-intro"><div><span className="movement-kicker">UN DÍA EN EL PAISAJE COMPARTIDO</span><h2>{run.sites.length===5?'Cinco':run.sites.length} colmenas. Cada viaje cuenta.</h2><p>Identifica un color, sigue su ruta y observa el recurso que utiliza.</p></div><div className="movement-methods" aria-label="Demostración archivada">{(['RANDOM','GREEDY','NSGA2'] as const).map(m=><button key={m} className={run.method===m?'active':''} disabled={running} onClick={()=>{setPlaying(false);onLoadDemo(m);}}>{m==='NSGA2'?'NSGA-II':m}</button>)}</div></section>
  {installationPreview&&<p role="status" className="movement-preview-notice">Vista previa de {installationPreview.label} · {run.sites.length} ubicaciones. Aún no hay viajes ni recursos simulados para esta selección. Pulsa «Simular solución seleccionada» para ejecutarla.</p>}
  {!installationPreview&&<section className="movement-player" aria-label="Reproducción de viajes">
   <div className="movement-player-top"><div className="movement-transport"><button className="movement-play" aria-label={playing?'Pausar':'Reproducir'} disabled={running||minute>=dayMinutes} onClick={()=>setPlaying(!playing)}>{playing?<Pause size={17}/>:<Play size={17}/>} {playing?'Pausar':'Reproducir'}</button><button className="movement-reset" title="Reiniciar reloj" aria-label="Reiniciar reloj" onClick={()=>go(0)}><RotateCcw size={17}/></button></div><label>Día de simulación<select aria-label="Día de simulación" value={day} onChange={e=>{setPlaying(false);setDay(Number(e.target.value));setMinute(0);setSelection({kind:'hive',slot:0});}}>{run.days.map((d,i)=><option key={d.date} value={i}>{d.date} · {i+1}/{run.days.length}</option>)}</select></label><label>Velocidad visual<select aria-label="Velocidad visual" value={speed} onChange={e=>setSpeed(Number(e.target.value))}>{[.5,1,4,12].map(v=><option key={v} value={v}>{v}×</option>)}</select></label><div className="movement-clock"><b>{fmt(minute,1)}</b><span>/ {dayMinutes} min</span></div></div>
   <input className="movement-timeline" aria-label="Minuto de la jornada" type="range" min="0" max={dayMinutes} step="0.05" value={minute} onChange={e=>go(Number(e.target.value))}/>
   <div className="movement-player-bottom"><span>Inicio del día</span><div>{stages.map(([phase,count])=><span key={phase} className={`movement-phase movement-phase-${phase}`}><i/>{phase} <b>{count}</b></span>)}</div><span>Regeneración al cierre</span></div>
  </section>}
  <div className="movement-colonies" role="group" aria-label="Colmenas de la corrida">{run.sites.map((_,slot)=><button key={slot} aria-pressed={selection?.kind==='hive'&&selection.slot===slot} onClick={()=>setSelection({kind:'hive',slot})} style={{'--colony-color':colonyColor(slot)} as React.CSSProperties}><span>C{slot+1}</span><b>Colmena {slot+1}</b><small>{bees.filter(b=>b.trip.hive_slot===slot).length} en viaje</small></button>)}</div>
  <div className="movement-workspace">
   <MovementMap landscape={landscape} run={run} date={date} minute={minute} bees={bees} stock={stock} activity={activity} selection={selection} onSelect={setSelection}/>
   <aside className="movement-side-column" aria-label="Información del elemento seleccionado">
    <details className="movement-side movement-map-dropdown" open={explorerOpen} onToggle={e=>setExplorerOpen(e.currentTarget.open)}>
    <summary className="movement-selection-heading"><MousePointer2 size={17}/><span>EXPLORA EL MAPA</span></summary>
    {installationPreview?<p>Vista previa · {hive?movementName(hive.display_name||hive.Navn||hive.site_id):installationPreview.label}. Sin resultados individuales todavía.</p>:<>
    <div className="movement-selection-card">
     {selection?.kind==='hive'&&<><span className="movement-card-icon" style={{color:colonyColor(selection.slot)}}><Hexagon size={26}/></span><h3>Colmena {selection.slot+1}</h3><p>{movementName(hive?.display_name||hive?.Navn)||'Ubicación sin nombre'}</p><dl><dt>Ubicación geográfica</dt><dd>{hive?`${fmt(hive.latitude,5)}, ${fmt(hive.longitude,5)}`:'No disponible'}</dd><dt>Viajes del día</dt><dd>{hiveTrips.length}</dd><dt>Activos ahora</dt><dd>{bees.filter(b=>b.trip.hive_slot===selection.slot).length}</dd><dt>Entrega final del día</dt><dd>{fmt(hiveTrips.reduce((s,t)=>s+t.resource_delivered,0),3)} RU</dd></dl><details><summary>Identificador de ubicación</summary><p className="movement-id">{hive?.site_id}</p></details><p className="movement-card-note">El total entregado resume todo el día archivado; no es una predicción en el minuto actual.</p></>}
     {selection?.kind==='trip'&&selectedTrip&&<><span className="movement-card-icon" style={{color:colonyColor(selectedTrip.hive_slot)}}><Route size={26}/></span><h3>C{selectedTrip.hive_slot+1} → parque</h3><span className="movement-state">{currentTripState(selectedTrip,minute)}</span><p>{parkName}</p><dl><dt>Distancia de ida</dt><dd>{fmt(selectedTrip.one_way_distance_m,1)} m</dd><dt>Salida</dt><dd>{eventTime('departure')}</dd><dt>Llegada</dt><dd>{eventTime('arrival')}</dd><dt>Regreso</dt><dd>{eventTime('return')}</dd></dl><div className="movement-jump"><button onClick={()=>go(selectedTrip.departure_min)}>Ver salida</button><button disabled={selectedTrip.foraging_start_min==null} onClick={()=>go(selectedTrip.foraging_start_min!)}>Ver visita</button><button disabled={!selectedTrip.returned||selectedTrip.foraging_end_min==null||selectedTrip.return_min==null} onClick={()=>go((selectedTrip.foraging_end_min!+selectedTrip.return_min!)/2)}>Ver regreso</button></div><details><summary>Resultado final del viaje</summary><dl><dt>Consumido</dt><dd>{fmt(selectedTrip.resource_consumed,3)} RU</dd><dt>Entregado</dt><dd>{fmt(selectedTrip.resource_delivered,3)} RU</dd><dt>Retorno dentro del día</dt><dd>{selectedTrip.returned?'Registrado':'No registrado'}</dd></dl><p className="movement-card-note">Resultado final del log; puede ocurrir después del minuto que estás reproduciendo.</p></details></>}
     {(selection?.kind==='park'||selectedTrip)&&patchId&&<div className={selectedTrip?'movement-patch-mini':''}>{!selectedTrip&&<><span className="movement-card-icon"><Layers size={26}/></span><h3>{parkName}</h3></>}<dl><dt>Recurso disponible ahora</dt><dd>{fmt(stock[patchId],3)} RU</dd><dt>Colonias recolectando</dt><dd>{activity.get(patchId)?.colonies.map(c=>`C${c+1}`).join(' + ')||'Ninguna ahora'}</dd><dt>Veces compartido hoy</dt><dd>{episodeCounts.get(patchId)??0}</dd></dl><details><summary>ID del parche</summary><p className="movement-id">{patchId}</p></details><details><summary>Superficie, asignación y distancias</summary><p>Superficie original: {fmt(park?.area_m2,1)} m². Recurso inicial: {fmt(resource&&totalArea>0?resource.exclusive_area_m2/totalArea*Number(run.parameters.initial_resource_total):null,3)} RU, repartido por cuota de superficie exclusiva.</p><DataTable rows={accessDistances(resource,run.sites,landscape.candidates).map((r,i)=>({...r,hive:'C'+(i+1)}))} columns={[{key:'hive',label:'Colmena'},{key:'distance_m',label:'Distancia (m)'}]}/><p>Distancias entre puntos representativos en EPSG:25833, no al borde del parque.</p></details></div>}
     {selection?.kind==='trip'&&!selectedTrip&&<p>No hay un viaje seleccionado en este día.</p>}
    </div>
    <div className={`movement-competition ${sharedNow.length?'has-sharing':''}`}><h3><span className="movement-sharing-dot"/>Actividad compartida del día</h3><strong aria-label="Episodios compartidos acumulados">{patchId?(episodeCounts.get(patchId)??0):totalEpisodes}<small> {patchId?'episodios en este parque':'episodios acumulados'}</small></strong><p>Hasta el minuto {fmt(minute,1)} de {date}. {patchId?'Conteo del parque seleccionado.':'Suma de episodios de todos los parques.'}</p><p>Total del día hasta este minuto: {totalEpisodes} episodios en {episodeCounts.size} parques.</p><p>{sharedNow.length?`Ahora: ${sharedNow.length} parches con forrajeo simultáneo. El halo señala la actividad actual.`:'Sin forrajeo simultáneo de colonias distintas en este instante.'}</p>{shared.length>0&&<button onClick={()=>{const w=shared.find(w=>w.end>minute)??shared[0];setSelection({kind:'park',id:w.patch});go((w.start+w.end)/2);}}>Ver intervalo registrado</button>}<details><summary>Qué significa este indicador</summary><p>Cuenta un episodio cuando un parque empieza a ser utilizado simultáneamente por dos o más colonias distintas con consumo positivo en [inicio de forrajeo, final de forrajeo). Un uso compartido continuo cuenta una sola vez, aunque se incorporen más viajes o colonias. Si termina y después vuelve a ocurrir, suma otro episodio. El conteo incluye el episodio en curso y permanece al volver al parque; se reconstruye hasta el minuto reproducido, disminuye al retroceder y cambia al seleccionar otro día. No cuenta rutas cruzadas ni viajes de una misma colonia. El halo sigue mostrando solo la actividad instantánea; este historial no es la presión registrada al iniciar cada intento.</p>{!shared.length&&<p>No hay intervalos compartidos en los logs de este día. No se añaden ejemplos artificiales.</p>}</details></div>
    <div className="movement-shortcuts"><button disabled={!today.length} onClick={follow}>Seguir un viaje <ArrowRight size={15}/></button><button disabled={!next} onClick={()=>next&&go(next.departure_min)}>Siguiente salida</button></div>
    </>}
    </details>
    {scenarioControls&&<div className="movement-scenario">{scenarioControls}</div>}
   </aside>
  </div>
  {!installationPreview&&<>{run.kind==='quick_nsga_individual_run'&&<div className="movement-individual-metrics"><b>Métricas de esta simulación individual</b><p>{fmt(run.metrics.total_resource_obtained,3)} RU entregadas · distancia media de ida {fmt(run.metrics.mean_distance_m,1)} m · {run.sites.length} colmenas · réplica {run.provenance.individual_replication_id}. No son promedios de búsqueda.</p><details><summary>Ver las nueve métricas de la corrida</summary><DataTable rows={Object.entries(run.metrics).map(([metric,value])=>({metric:metricLabels[metric]?.name??metric,value,unit:metricLabels[metric]?.unit??''}))} columns={[{key:'metric',label:'Métrica'},{key:'value',label:'Resultado individual'},{key:'unit',label:'Unidad'}]}/></details></div>}<p className="movement-disclaimer">{run.kind==='quick_nsga_individual_run'?`Simulación individual de ${run.provenance.quick_solution_id} · réplica ${run.provenance.individual_replication_id}; métricas distintas del promedio de búsqueda`:run.kind==='new_exploratory_run'?'Corrida exploratoria':'Demo archivada'} · {run.method} · seed {run.provenance.seed} · {run.provenance.engine_version}. Movimiento interpolado desde los logs: no son abejas reales rastreadas ni trayectorias GPS.</p>
  <p className="movement-weather">{observedWeather?.temperature_mean_C!=null?`Contexto observado: temperatura media de sesiones ${fmt(observedWeather.temperature_mean_C)} °C. No impulsa el motor.`:'Sin temperatura registrada para este día; no se imputa clima.'}</p>
  <details className="movement-more"><summary>Inspector completo y descarga de viajes</summary><TripInspector run={run} date={date} landscape={landscape} selected={selection?.kind==='trip'?selection.key:''} onSelect={key=>setSelection({kind:'trip',key})}/></details>
  <details className="movement-more"><summary>Recursos durante los 18 días y entregas por colmena</summary><ResourceEvolution run={run} date={date}/></details></>}
 </div>;
}
