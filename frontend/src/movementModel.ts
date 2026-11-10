/** Display-only queries of archived trip intervals. No random draws or model rules. */
import type {Run,Trip} from './types';

export const colonyColors=['#a96213','#27766b','#7463a0','#be5960','#386fa4'];
export const colonyColor=(slot:number)=>colonyColors[slot%colonyColors.length];
export const tripKey=(t:Trip)=>`${t.hive_slot}-${t.trip_slot}`;

/** Reversible decoding for labels in this view only; original source strings remain intact. */
export function movementName(label:unknown):string{
 if(typeof label!=='string')return '';
 if(!/[ÃÂ]/.test(label))return label;
 const extra=[0x20ac,0x81,0x201a,0x192,0x201e,0x2026,0x2020,0x2021,0x2c6,0x2030,0x160,0x2039,0x152,0x8d,0x17d,0x8f,0x90,0x2018,0x2019,0x201c,0x201d,0x2022,0x2013,0x2014,0x2dc,0x2122,0x161,0x203a,0x153,0x9d,0x17e,0x178];
 try{
  const bytes=[...label].map(c=>{const code=c.codePointAt(0)!;if(code<=255)return code;const i=extra.indexOf(code);if(i<0)throw new Error('Not a reversible CP1252 label');return 0x80+i;});
  return new TextDecoder('utf-8',{fatal:true}).decode(new Uint8Array(bytes));
 }catch{return label;}
}

export function foragingActivity(trips:Trip[],date:string,minute:number):Map<string,{colonies:number[];trips:number}>{
 const patches=new Map<string,{colonies:Set<number>;trips:number}>();
 for(const t of trips){
  // Motor occupancy is [foraging_start, foraging_end), only for positive consumption.
  if(t.date!==date||t.resource_consumed<=0||t.foraging_start_min==null||t.foraging_end_min==null||minute<t.foraging_start_min||minute>=t.foraging_end_min)continue;
  const state=patches.get(t.patch_id)??{colonies:new Set<number>(),trips:0};
  state.colonies.add(t.hive_slot);state.trips++;patches.set(t.patch_id,state);
 }
 return new Map([...patches].map(([id,a])=>[id,{colonies:[...a.colonies].sort((a,b)=>a-b),trips:a.trips}]));
}

export function sharedForagingWindows(trips:Trip[],date:string):{patch:string;start:number;end:number;colonies:number[]}[]{
 const boundaries=[...new Set(trips.filter(t=>t.date===date&&t.resource_consumed>0)
  .flatMap(t=>[t.foraging_start_min,t.foraging_end_min]).filter((t):t is number=>t!=null))].sort((a,b)=>a-b);
 const windows=[];
 for(let i=0;i<boundaries.length-1;i++){
  const start=boundaries[i],end=boundaries[i+1];
  if(end<=start)continue;
  for(const [patch,a] of foragingActivity(trips,date,start))if(a.colonies.length>1)windows.push({patch,start,end,colonies:a.colonies});
 }
 return windows;
}

/** One episode per continuous shared interval, even if a third colony joins. */
export function sharedForagingEpisodes(windows:ReturnType<typeof sharedForagingWindows>):ReturnType<typeof sharedForagingWindows>{
 const episodes:ReturnType<typeof sharedForagingWindows>=[];
 const lastByPatch=new Map<string,ReturnType<typeof sharedForagingWindows>[number]>();
 for(const window of [...windows].sort((a,b)=>a.start-b.start)){
  const last=lastByPatch.get(window.patch);
  if(last&&window.start<=last.end){
   last.end=Math.max(last.end,window.end);
   last.colonies=[...new Set([...last.colonies,...window.colonies])].sort((a,b)=>a-b);
  }else{
   const episode={...window,colonies:[...window.colonies]};
   episodes.push(episode);lastByPatch.set(window.patch,episode);
  }
 }
 return episodes;
}

export function sharedEpisodeCounts(episodes:ReturnType<typeof sharedForagingEpisodes>,minute:number):Map<string,number>{
 const counts=new Map<string,number>();
 for(const episode of episodes)if(episode.start<=minute)counts.set(episode.patch,(counts.get(episode.patch)??0)+1);
 return counts;
}

export function currentTripState(t:Trip,minute:number):string{
 if(minute<t.departure_min)return 'Pendiente de salida';
 if(t.returned&&t.return_min!=null&&minute>=t.return_min)return 'Regreso registrado';
 if(minute<t.arrival_min)return 'Ida al parque';
 if(t.foraging_end_min!=null&&minute>=t.foraging_end_min){
  if(t.return_min!=null&&minute<t.return_min)return 'Regreso a la colmena';
  return t.returned?'Regreso registrado':'Sin regreso registrado';
 }
 if(t.foraging_start_min!=null&&minute>=t.foraging_start_min)return 'Recolección en el parque';
 return 'Búsqueda en el parque';
}

export function flightAngle(home:[number,number],target:[number,number],returning:boolean):number{
 const scale=Math.cos((home[0]+target[0])/2*Math.PI/180);
 const east=(target[1]-home[1])*scale,north=target[0]-home[0];
 return Math.atan2(-north,east)*180/Math.PI+(returning?180:0);
}
