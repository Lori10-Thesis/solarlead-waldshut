"use client";
import { useEffect,useState } from 'react';
import Link from 'next/link';
import { ApiError,api } from '@/lib/api';

type Row={source:string;leads:number;hot:number;qualified:number;won:number;cost_eur:number;revenue_eur:number;cpl:number|null;qualified_cpl:number|null};
export default function Analytics(){const [rows,setRows]=useState<Row[]>([]);const [error,setError]=useState('');
 useEffect(()=>{api<Row[]>('/api/admin/analytics/sources').then(setRows).catch((e)=>{if(e instanceof ApiError&&e.status===401) location.href='/admin/login'; else setError('Analytics konnten nicht geladen werden.');});},[]);
 return <div className="container dashboard"><div className="topbar"><div><div className="brand">Solar<span>Lead</span> / Sources</div><p>Akquise- und Monetarisierungsperformance.</p></div><div className="navlinks" style={{display:'flex'}}><Link href="/admin">Leads</Link><Link href="/geo">Geo</Link></div></div>
 <div className="card table-wrap"><table><thead><tr><th>Quelle</th><th>Leads</th><th>Hot</th><th>Qualified</th><th>Won</th><th>Kosten</th><th>CPL</th><th>Q-CPL</th><th>Umsatz</th></tr></thead><tbody>{rows.map(r=><tr key={r.source}><td><b>{r.source}</b></td><td>{r.leads}</td><td>{r.hot}</td><td>{r.qualified}</td><td>{r.won}</td><td>{r.cost_eur.toFixed(2)} €</td><td>{r.cpl===null?'–':`${r.cpl.toFixed(2)} €`}</td><td>{r.qualified_cpl===null?'–':`${r.qualified_cpl.toFixed(2)} €`}</td><td>{r.revenue_eur.toFixed(2)} €</td></tr>)}</tbody></table></div>{error&&<div className="error">{error}</div>}</div>}
