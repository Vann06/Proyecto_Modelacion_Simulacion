import {useMemo,useState} from 'react';
import {MapContainer,TileLayer,GeoJSON,Circle,CircleMarker,Marker,Polyline,Popup,Tooltip} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type {Landscape,Run,Row} from '../types';
import {activeTrips,stocks} from '../visualization';
import {fmt} from '../api';
import {MapControls,initialLayers} from './MapControls';

const beeIcon=L.divIcon({className:'bee-marker',iconSize:[30,30],iconAnchor:[15,15],html:'<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><ellipse cx="23" cy="20" rx="12" ry="8" fill="#d0e9ea"/><ellipse cx="42" cy="20" rx="12" ry="8" fill="#d0e9ea"/><ellipse cx="32" cy="36" rx="23" ry="15" fill="#efbd4f" stroke="#173e34" stroke-width="3"/><path d="M24 22v27M37 22v27" stroke="#173e34" stroke-width="6"/><circle cx="49" cy="32" r="3" fill="#173e34"/></svg>'});
export function OsloMap({landscape,run=null,date='',minute=0,sites,onSelect,onTripSelect}:{landscape:Landscape;run?:Run|null;date?:string;minute?:number;sites?:string[];onSelect?:(p:Row)=>void;onTripSelect?:(id:string)=>void}){
 const [layers,setLayers]=useState(initialLayers);
 const bees=useMemo(()=>activeTrips(run,date,minute,landscape.candidates,landscape.resources),[run,date,minute,landscape]);
 const stock=useMemo(()=>stocks(run,date,minute),[run,date,minute]);
 const ids=sites??run?.sites??[];const hives=ids.flatMap(id=>{const s=landscape.candidates.find(s=>s.site_id===id);return s?[s]:[]});
 const totalArea=landscape.resources.reduce((sum,r)=>sum+r.exclusive_area_m2,0);
 const initial=new Map(landscape.resources.map(r=>[r.patch_id,r.exclusive_area_m2/totalArea*Number(run?.parameters.initial_resource_total??1000)]));
 return <><MapControls layers={layers} onChange={(key,value)=>setLayers(old=>({...old,[key]:value}))}/>
 <MapContainer center={[59.92,10.76]} zoom={11} scrollWheelZoom={false} className="oslo-map" preferCanvas>
  {layers.base&&<TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"/>}
  {layers.parks&&<GeoJSON data={landscape.parks} style={{color:'#7f9685',weight:.7,fillColor:'#c6d2c1',fillOpacity:.3}} onEachFeature={(f,layer)=>{layer.on('click',()=>onSelect?.(f.properties??{}))}}/>}
  {layers.resources&&<GeoJSON key={run?.provenance.config_hash??'initial'} data={landscape.resource_geometry} style={f=>{const id=f?.properties?.patch_id;const ratio=run?(stock[id]??0)/Math.max(initial.get(id)??1,1e-12):1;return {color:'#548b6a',weight:.5,fillColor:ratio>.5?'#45916c':ratio>.1?'#b4be7b':'#ccac87',fillOpacity:.5}}} onEachFeature={(f,layer)=>layer.on('click',()=>onSelect?.({...landscape.parks.features.find(p=>p.properties?.patch_id===f.properties?.patch_id)?.properties,available:stock[f.properties?.patch_id]}))}/>}
  {layers.zones&&<GeoJSON interactive={false} data={landscape.zones} style={{color:'#b36f65',weight:1.1,fillColor:'#c6887c',fillOpacity:.16}}/>}
  {layers.candidates&&landscape.candidates.map(s=><CircleMarker key={s.site_id} center={[s.latitude,s.longitude]} radius={3} pathOptions={{color:'#6b7e81',fillOpacity:.7,weight:0}}><Popup>{s.display_name||s.Navn||s.site_id}<br/>{s.site_id}</Popup></CircleMarker>)}
  {layers.hives&&hives.map((s,i)=><CircleMarker key={s.site_id} center={[s.latitude,s.longitude]} radius={11} pathOptions={{color:'#fff',fillColor:'#d8a541',fillOpacity:1,weight:2}}><Tooltip permanent direction="center" className="hive-number">{i+1}</Tooltip><Popup><b>Colmena {i+1}</b><br/>{s.display_name||s.Navn}<br/>{s.site_id}</Popup></CircleMarker>)}
  {layers.access&&hives.map(s=><Circle key={s.site_id} center={[s.latitude,s.longitude]} radius={Number(run?.parameters.max_foraging_distance_m??3000)} interactive={false} pathOptions={{color:"#7381b5",weight:1,fillOpacity:.025}}/>)}
  {bees.slice(0,400).map(b=><Marker key={b.key} position={b.position} icon={beeIcon} eventHandlers={{click:()=>onTripSelect?.(b.key)}}><Popup>Viaje modelado · colmena {b.trip.hive_slot+1}<br/>{b.phase}<br/>Consumo del viaje: {fmt(b.trip.resource_consumed)} RU<br/>Otras colonias al iniciar: {b.trip.other_colonies_active_at_foraging_start??'Aún no inicia'}</Popup></Marker>)}
  {layers.routes&&bees.slice(0,400).map(b=><Polyline key={b.key} positions={[b.home,b.target]} pathOptions={{color:'#527e70',weight:1.2,dashArray:'4 5',opacity:.7}}/>)}
 </MapContainer><div className="map-legend"><span><i className="dot green"/>Recurso sintético</span><span><i className="dot rose"/>Zona restringida</span><span><i className="dot gold"/>Colmena</span><span><i className="dot blue"/>Candidato permitido</span><span>Radio de acceso: supuesto del escenario</span><span>🐝 Viaje activo</span></div><p className="chart-note">Geometría real · interpolación visual de viajes, no GPS · máximo 400 íconos de {bees.length} viajes activos. Polígonos simplificados solo para dibujar.</p></>;
}
