export type LayerName='parks'|'resources'|'zones'|'candidates'|'hives'|'routes'|'access'|'base';
export const initialLayers:Record<LayerName,boolean>={parks:true,resources:true,zones:true,candidates:false,hives:true,routes:true,access:false,base:true};
const names:Record<LayerName,string>={parks:'Parques',resources:'Recursos',zones:'Restricciones',candidates:'Candidatos',hives:'Colmenas',routes:'Recorridos',access:'Radio de acceso',base:'Mapa base'};
export function MapControls({layers,onChange}:{layers:Record<LayerName,boolean>;onChange:(key:LayerName,value:boolean)=>void}){
 return <fieldset className="map-filters"><legend>Capas del mapa</legend>{(Object.keys(names) as LayerName[]).map(key=><label key={key}><input type="checkbox" checked={layers[key]} onChange={e=>onChange(key,e.target.checked)}/>{names[key]}</label>)}</fieldset>;
}
