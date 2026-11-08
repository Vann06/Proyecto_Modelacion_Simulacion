import type {Candidate,Resource,Run,Trip} from './types';
export interface VisualTrip {key:string;trip:Trip;position:[number,number];home:[number,number];target:[number,number];phase:string}
// This interpolates display positions from logged intervals; it never decides a trip.
export function tripPosition(trip:Trip,minute:number,home:[number,number],target:[number,number]):{position:[number,number];phase:string}|null {
 if(minute<trip.departure_min||(trip.return_min!=null&&minute>=trip.return_min))return null;
 let fraction=1,from=home,to=target,phase='Ida';
 if(minute<trip.arrival_min)fraction=(minute-trip.departure_min)/Math.max(trip.arrival_min-trip.departure_min,1e-12);
 else if(trip.foraging_end_min!=null&&minute>=trip.foraging_end_min&&trip.return_min!=null){phase='Regreso';from=target;to=home;fraction=(minute-trip.foraging_end_min)/Math.max(trip.return_min-trip.foraging_end_min,1e-12)}
 else{phase=trip.foraging_start_min!=null&&minute>=trip.foraging_start_min?'Forrajeo':'Búsqueda';from=target;to=target}
 fraction=Math.max(0,Math.min(1,fraction));
 return {position:[from[0]+fraction*(to[0]-from[0]),from[1]+fraction*(to[1]-from[1])],phase};
}
export function activeTrips(run:Run|null,date:string,minute:number,candidates:Candidate[],resources:Resource[]):VisualTrip[]{
 if(!run)return [];
 const homes=new Map(candidates.map(s=>[s.site_id,s])),patches=new Map(resources.map(s=>[s.patch_id,s]));
 return run.trips.filter(t=>t.date===date).flatMap(t=>{
  const a=homes.get(t.site_id),b=patches.get(t.patch_id);if(!a||!b)return [];
  const home:[number,number]=[a.latitude,a.longitude],target:[number,number]=[b.latitude,b.longitude];
  const p=tripPosition(t,minute,home,target);return p?[{key:`${t.hive_slot}-${t.trip_slot}`,trip:t,...p,home,target}]:[];
 });
}
export function stocks(run:Run|null,date:string,minute:number):Record<string,number>{
 if(!run)return {};const day=run.days.find(d=>d.date===date);if(!day)return {};
 const stock=Object.fromEntries(day.patch_ids.map((id,i)=>[id,(minute>=Number(run.parameters.day_minutes)?day.final:day.initial)[i]]));
 if(minute<Number(run.parameters.day_minutes))for(const t of run.trips)if(t.date===date&&t.foraging_start_min!=null&&t.foraging_start_min<=minute)stock[t.patch_id]-=t.resource_consumed;
 return stock;
}
