import {useEffect,useState} from 'react';
import {api} from './api';
import type {QuickJob,RunOptions} from './types';

/** Explicit starts only; changing sliders never posts a job. State lives with App. */
export function useQuickNsga(){
 const [job,setJob]=useState<QuickJob|null>(null),[selected,setSelected]=useState('');
 const [starting,setStarting]=useState(false),[error,setError]=useState('');
 const active=starting||job?.status==='starting'||job?.status==='running';
 useEffect(()=>{
  if(!job||!['starting','running'].includes(job.status))return;
  let disposed=false;let timer:ReturnType<typeof setTimeout>;
  const poll=async()=>{try{const next=await api<QuickJob>('quick-nsga2/'+job.job_id);if(disposed)return;setJob(next);setError('');if(['starting','running'].includes(next.status))timer=setTimeout(poll,1000);}catch(e){if(!disposed){setError('No se pudo consultar el progreso. La búsqueda puede continuar: '+String(e));timer=setTimeout(poll,2500);}}};
  timer=setTimeout(poll,500);return()=>{disposed=true;clearTimeout(timer);};
 },[job?.job_id,job?.status]);
 async function start(options:RunOptions){if(active)return;setStarting(true);setError('');setSelected('');try{setJob(await api<QuickJob>('quick-nsga2',{...options,method:'NSGA2',optimizer_seed:2026}));}catch(e){setError(String(e));}finally{setStarting(false);}}
 return {job,selected,setSelected,active,error,start};
}
