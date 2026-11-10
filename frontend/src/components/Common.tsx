import type {ReactNode} from 'react';
import {Download,Info} from 'lucide-react';
import {fmt} from '../api';
export function Panel({title,eyebrow,children,className=''}:{title?:string;eyebrow?:string;children:ReactNode;className?:string}){return <section className={'panel '+className}>{eyebrow&&<p className="eyebrow">{eyebrow}</p>}{title&&<h2>{title}</h2>}{children}</section>}
export function Notice({children}:{children:ReactNode}){return <div className="notice"><Info size={19}/><div>{children}</div></div>}
export function DownloadCSV({name,label='Descargar CSV'}:{name:string;label?:string}){return <a className="button secondary" href={'/api/download/'+name} download><Download size={16}/>{label}</a>}
export function DownloadRows({rows,name,label}:{rows:Record<string,unknown>[];name:string;label:string}){
 const save=()=>{if(!rows.length)return;const keys=Object.keys(rows[0]);const quote=(x:unknown)=>'"'+String(x??'').replaceAll('"','""')+'"';
  const text=[keys.map(quote).join(','),...rows.map(r=>keys.map(k=>quote(r[k])).join(','))].join('\r\n');
  const url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 return <button className="button secondary" disabled={!rows.length} onClick={save}><Download size={16}/>{label}</button>;
}
export function Stat({label,value,unit,foot}:{label:string;value:string;unit?:string;foot?:string}){return <div className="stat"><span>{label}</span><strong>{value}<small>{value==='No definido'?'':unit}</small></strong>{foot&&<p>{foot}</p>}</div>}
export function DataTable({rows,columns}:{rows:Record<string,any>[];columns:{key:string;label:string;digits?:number}[]}){return <div className="table-wrap"><table><thead><tr>{columns.map(c=><th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{columns.map(c=><td key={c.key}>{typeof r[c.key]==='number'?fmt(r[c.key],c.digits??3):String(r[c.key]??'No disponible')}</td>)}</tr>)}</tbody></table></div>}
