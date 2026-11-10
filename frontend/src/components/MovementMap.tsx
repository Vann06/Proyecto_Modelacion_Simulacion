import {useEffect,useMemo,useState} from 'react';
import {MapContainer,TileLayer,GeoJSON,Marker,Polyline,Circle,CircleMarker,Tooltip,useMap} from 'react-leaflet';
import L from 'leaflet';
import type {Landscape,Run} from '../types';
import type {VisualTrip} from '../visualization';
import {colonyColor,flightAngle,currentTripState,movementName} from '../movementModel';
import {fmt} from '../api';

export type MovementSelection={kind:'hive';slot:number}|{kind:'trip';key:string}|{kind:'park';id:string}|null;

// Original inline SVGs; colors and numbers are derived from colony slots, never source HTML.
export function hiveSvg(slot:number):string{
 const color=colonyColor(slot);
 return `<svg viewBox="0 0 54 60" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Colmena ${slot+1}"><circle cx="27" cy="26" r="24" fill="#fffdf5" stroke="${color}" stroke-width="2"/><path d="M11 19 27 10l16 9" fill="${color}" stroke="${color}" stroke-width="3" stroke-linejoin="round"/><rect x="14" y="20" width="26" height="8" rx="2" fill="#edc56e" stroke="${color}" stroke-width="1.7"/><rect x="14" y="29" width="26" height="8" rx="2" fill="#f8dfa3" stroke="${color}" stroke-width="1.7"/><path d="M12 39h30" stroke="${color}" stroke-width="3" stroke-linecap="round"/><circle cx="27" cy="34" r="2" fill="${color}"/><rect x="14" y="44" width="26" height="15" rx="7" fill="${color}"/><text x="27" y="55" text-anchor="middle" fill="white" font-size="10" font-family="system-ui" font-weight="700">C${slot+1}</text></svg>`;
}
export function beeSvg(slot:number,angle:number,visiting:boolean):string{
 return `<svg viewBox="0 0 64 48" xmlns="http://www.w3.org/2000/svg" style="transform:rotate(${angle}deg)" role="img" aria-label="Viaje de colmena ${slot+1}">${visiting?`<circle cx="30" cy="25" r="20" fill="${colonyColor(slot)}" opacity=".13"/>`:''}<ellipse cx="27" cy="14" rx="12" ry="8" fill="#fffdf1" stroke="${colonyColor(slot)}" stroke-width="1.5"/><ellipse cx="27" cy="34" rx="12" ry="8" fill="#fffdf1" stroke="${colonyColor(slot)}" stroke-width="1.5"/><ellipse cx="31" cy="24" rx="20" ry="12" fill="#efc35e" stroke="#433522" stroke-width="2"/><path d="M22 14v20m10-21v22" stroke="#614629" stroke-width="5"/><circle cx="48" cy="23" r="7" fill="${colonyColor(slot)}"/><circle cx="51" cy="20" r="1.7" fill="white"/><path d="m12 24-6-3v6Z" fill="#433522"/></svg>`;
}

function Frame({points,resetKey,focus}:{points:[number,number][];resetKey:string;focus:[number,number]|null}){
 const map=useMap();
 useEffect(()=>{if(points.length)map.fitBounds(L.latLngBounds(points),{padding:[45,45],maxZoom:13,animate:false});},[map,resetKey]);
 useEffect(()=>{const observer=new ResizeObserver(()=>{map.invalidateSize();if(points.length)map.fitBounds(L.latLngBounds(points),{padding:[45,45],maxZoom:13,animate:false});});observer.observe(map.getContainer());return()=>observer.disconnect();},[map,resetKey]);
 useEffect(()=>{if(focus)map.panInside(focus,{padding:[65,65],animate:false});},[map,focus?.[0],focus?.[1]]);
 return null;
}

function FlightMarker({flight,onSelect}:{flight:VisualTrip;onSelect:(s:MovementSelection)=>void}){
 const returning=flight.phase==='Regreso';
 const angle=flightAngle(flight.home,flight.target,returning);
 const visiting=flight.phase==='Forrajeo'||flight.phase==='Búsqueda';
 const icon=useMemo(()=>L.divIcon({className:'movement-bee-icon',html:beeSvg(flight.trip.hive_slot,angle,visiting),iconSize:[27,24],iconAnchor:[13,12]}),[flight.trip.hive_slot,angle,visiting]);
 return <Marker position={flight.position} title={`Viaje C${flight.trip.hive_slot+1} · ${flight.phase}`} zIndexOffset={900} icon={icon} eventHandlers={{click:()=>onSelect({kind:'trip',key:flight.key})}}/>;
}

export function MovementMap({landscape,run,date,minute,bees,stock,activity,selection,onSelect}:{landscape:Landscape;run:Run;date:string;minute:number;bees:VisualTrip[];stock:Record<string,number>;activity:Map<string,{colonies:number[];trips:number}>;selection:MovementSelection;onSelect:(s:MovementSelection)=>void}){
 const [base,setBase]=useState(true),[parks,setParks]=useState(true),[routes,setRoutes]=useState(true),[zones,setZones]=useState(false),[frame,setFrame]=useState(0);
 const [showResource,setShowResource]=useState(true),[showCandidates,setShowCandidates]=useState(false),[showHives,setShowHives]=useState(true),[showRadius,setShowRadius]=useState(false);
 const hives=run.sites.map(id=>landscape.candidates.find(c=>c.site_id===id));
 const hiveIcons=useMemo(()=>run.sites.map((_,i)=>L.divIcon({className:'movement-hive-icon',html:hiveSvg(i),iconSize:[48,54],iconAnchor:[24,27]})),[run.sites]);
 const resources=useMemo(()=>new Map(landscape.resources.map(r=>[r.patch_id,r])),[landscape]);
 const today=useMemo(()=>run.trips.filter(t=>t.date===date),[run,date]);
 const visited=new Set(today.map(t=>t.patch_id));
 const points:[number,number][]=hives.flatMap(h=>h?[[h.latitude,h.longitude] as [number,number]]:[]);
 for(const id of visited){const r=resources.get(id);if(r)points.push([r.latitude,r.longitude]);}
 const selectedTrip=selection?.kind==='trip'?today.find(t=>`${t.hive_slot}-${t.trip_slot}`===selection.key):null;
 const selectedPatch=selection?.kind==='park'?selection.id:selectedTrip?.patch_id;
 const target=selectedPatch?resources.get(selectedPatch):undefined;
 const home=selectedTrip?hives[selectedTrip.hive_slot]:undefined;
 const focus:[number,number]|null=selection?.kind==='hive'&&hives[selection.slot]?[hives[selection.slot]!.latitude,hives[selection.slot]!.longitude]:target?[target.latitude,target.longitude]:null;
 const initialArea=landscape.resources.reduce((sum,r)=>sum+r.exclusive_area_m2,0);
 const initialTotal=Number(run.parameters.initial_resource_total);
 const selectedRoute=home&&target?[[home.latitude,home.longitude],[target.latitude,target.longitude]] as [number,number][]:null;
 const visible=bees.slice(0,120);
 return <div className="movement-map-shell">
  <div className="movement-map-toolbar"><div><b>Oslo · paisaje real</b><span>{date} · minuto {fmt(minute,1)}</span></div><button type="button" onClick={()=>setFrame(f=>f+1)}>Encuadrar actividad</button></div>
  <MapContainer center={[59.92,10.76]} zoom={11} scrollWheelZoom={false} preferCanvas className="movement-map">
   <Frame points={points} resetKey={`${run.method}-${run.provenance.config_hash}-${run.sites.join(',')}-${date}-${frame}`} focus={focus}/>
   {base&&<TileLayer className="movement-basemap" url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'/>}
   {parks&&<GeoJSON data={landscape.parks} style={{color:'#829a89',weight:.7,fillColor:'#b7c8ae',fillOpacity:.15}} onEachFeature={(f,l)=>l.on('click',()=>onSelect({kind:'park',id:f.properties?.patch_id}))}/>}
   {showResource&&run.kind!=='quick_nsga_preview'&&<GeoJSON data={landscape.resource_geometry} style={f=>{const id=f?.properties?.patch_id;const r=resources.get(id);const initial=r&&initialArea>0?r.exclusive_area_m2/initialArea*initialTotal:0;const ratio=initial>0?(stock[id]??0)/initial:0;const busy=activity.get(id);return {color:busy?'#748951':'#8caa87',weight:busy?2:.6,fillColor:ratio>.5?'#a1ba8e':ratio>.1?'#d2c58a':'#c5bba8',fillOpacity:visited.has(id)?.52:.22};}} onEachFeature={(f,l)=>l.on('click',()=>onSelect({kind:'park',id:f.properties?.patch_id}))}/>}
   {zones&&<GeoJSON data={landscape.zones} interactive={false} style={{color:'#a86f6b',weight:1,dashArray:'3 4',fillOpacity:.08}}/>}
   {routes&&visible.map(b=><Polyline key={`route-${b.key}`} positions={[b.home,b.target]} interactive={false} pathOptions={{color:colonyColor(b.trip.hive_slot),weight:selection?.kind==='trip'&&selection.key===b.key?3:1.8,opacity:.65,dashArray:b.phase==='Regreso'?'3 6':undefined}}/>)}
   {selectedRoute&&routes&&<Polyline positions={selectedRoute} interactive={false} pathOptions={{color:colonyColor(selectedTrip!.hive_slot),weight:3,opacity:.85,dashArray:currentTripState(selectedTrip!,minute)==='Regreso a la colmena'?'3 6':undefined}}/>}
   {[...activity].map(([id,a])=>{const r=resources.get(id);if(!r)return null;return <CircleMarker key={`activity-${id}`} center={[r.latitude,r.longitude]} radius={a.colonies.length>1?21:8} eventHandlers={{click:()=>onSelect({kind:'park',id})}} pathOptions={{color:a.colonies.length>1?'#ba593b':colonyColor(a.colonies[0]),weight:a.colonies.length>1?3:1.5,fillColor:a.colonies.length>1?'#e8ad62':colonyColor(a.colonies[0]),fillOpacity:.17,className:a.colonies.length>1?'movement-shared-halo':''}}><Tooltip permanent={a.colonies.length>1} direction={a.colonies.length>1?'center':'top'} className={a.colonies.length>1?'movement-shared-count':''}>{a.colonies.length>1?a.colonies.length:`C${a.colonies[0]+1} recolectando`}</Tooltip></CircleMarker>})}
   {target&&<CircleMarker center={[target.latitude,target.longitude]} radius={12} interactive={false} pathOptions={{color:'#3b564a',weight:2,dashArray:'3 3',fillOpacity:0}}/>}
   {showHives&&hives.map((h,i)=>h&&<Marker key={`${h.site_id}-${i}`} position={[h.latitude,h.longitude]} title={`Colmena ${i+1}`} zIndexOffset={500+i} icon={hiveIcons[i]} eventHandlers={{click:()=>onSelect({kind:'hive',slot:i})}}/>)}
   {showCandidates&&landscape.candidates.map(c=><CircleMarker key={c.site_id} center={[c.latitude,c.longitude]} radius={3} eventHandlers={{click:()=>onSelect({kind:'park',id:c.patch_id})}} pathOptions={{color:'#6a7d76',weight:1,fillOpacity:.35}}><Tooltip>{movementName(c.display_name||c.Navn||c.site_id)}</Tooltip></CircleMarker>)}
   {showRadius&&hives.map((h,i)=>h&&<Circle key={h.site_id+'-'+i} center={[h.latitude,h.longitude]} radius={Number(run.parameters.max_foraging_distance_m)} interactive={false} pathOptions={{color:colonyColor(i),weight:1,dashArray:'3 5',fillOpacity:.015}}/>)}
   {visible.map(b=><FlightMarker key={b.key} flight={b} onSelect={onSelect}/>)}
  </MapContainer>
  <div className="movement-map-options" role="group" aria-label="Capas de movimiento">{[['Mapa base',base,setBase],['Parques',parks,setParks],['Rutas',routes,setRoutes],['Restricciones',zones,setZones]].map(([label,value,setter])=><label key={String(label)}><input type="checkbox" checked={Boolean(value)} onChange={e=>(setter as (v:boolean)=>void)(e.target.checked)}/>{String(label)}</label>)}</div>
  <details className="movement-extra-layers"><summary>Capas adicionales</summary><div>{[['Recursos',showResource,setShowResource],['Candidatos',showCandidates,setShowCandidates],['Colmenas',showHives,setShowHives],['Radio de acceso',showRadius,setShowRadius]].map(([label,value,setter])=><label key={String(label)}><input type="checkbox" checked={Boolean(value)} onChange={e=>(setter as (v:boolean)=>void)(e.target.checked)}/>{String(label)}</label>)}</div></details>
  <div className="movement-map-key"><span><i className="movement-key-park"/>Parque / recurso</span><span><i className="movement-key-out"/>Ida</span><span><i className="movement-key-back"/>Regreso</span><span><i className="movement-key-shared"/>≥2 colonias en forrajeo</span></div>
  <p className="movement-map-footnote">{visible.length}/{bees.length} viajes activos dibujados · rutas rectas interpoladas, no GPS. El color del recurso representa stock sintético, no calidad ecológica.</p>
 </div>;
}

