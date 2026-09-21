"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {api,ApiError} from "@/lib/api";

type Campaign={id:number;code:string;name:string;channel:string;market_code:string|null;query:string};
type Performance={code:string;name:string;channel:string;market_code:string|null;source_id:string;views:number;starts:number;results:number;contact_views:number;leads:number;qualified:number;appointments:number;sold:number;revenue_eur:number;start_rate:number|null;lead_rate:number|null;qualified_rate:number|null};

const region=(m:string|null)=>m==="koeln"?"Köln":m==="waldshut"?"Waldshut/Hochrhein":"deiner Region";

export default function Acquisition(){
 const [rows,setRows]=useState<Campaign[]>([]); const [perf,setPerf]=useState<Performance[]>([]); const [copied,setCopied]=useState("");
 const load=()=>Promise.all([api<Campaign[]>("/api/admin/acquisition/campaigns"),api<Performance[]>("/api/admin/acquisition/performance")]).then(([a,b])=>{setRows(a);setPerf(b)}).catch((e)=>{if(e instanceof ApiError&&e.status===401)location.href="/admin/login"});
 useEffect(()=>{load()},[]);
 const base=typeof window!=="undefined"?window.location.origin:"http://localhost:3000";
 const url=(c:Campaign)=>`${base}/?${c.query}`;
 const shareText=(c:Campaign)=>`☀️ Kostenloser Balkon-PV-Check für ${region(c.market_code)}\n\nIn wenigen Minuten prüfen, welches Solar-Potenzial der eigene Balkon hat und ob sich ein Balkonkraftwerk lohnen könnte. Kostenlos und unverbindlich:\n\n${url(c)}`;
 const copy=async(c:Campaign,kind:"link"|"post")=>{await navigator.clipboard.writeText(kind==="link"?url(c):shareText(c));setCopied(`${c.code}-${kind}`);setTimeout(()=>setCopied(""),1200)};
 const byCode=Object.fromEntries(perf.map(x=>[x.code,x]));
 const totals=perf.reduce((a,x)=>({views:a.views+x.views,leads:a.leads+x.leads,qualified:a.qualified+x.qualified,appointments:a.appointments+x.appointments}),{views:0,leads:0,qualified:0,appointments:0});
 return <div className="container dashboard"><div className="topbar"><div><Link className="small" href="/admin">← Dashboard</Link><div className="brand" style={{marginTop:10}}>Organic Acquisition</div><p>Jeder Link hat eine eigene Source. V0.5.1 misst jetzt den gesamten Funnel bis zum qualifizierten Lead.</p></div><button className="mini-btn" onClick={load}>Aktualisieren</button></div>
 <div className="statgrid"><div className="card stat"><span>Landing-Aufrufe</span><strong>{totals.views}</strong></div><div className="card stat"><span>Eigene Leads</span><strong>{totals.leads}</strong></div><div className="card stat"><span>Qualifiziert</span><strong>{totals.qualified}</strong></div><div className="card stat"><span>Termine</span><strong>{totals.appointments}</strong></div></div>
 <section className="card detail-card"><div className="section-title">Organische Kampagnen</div><div className="campaign-stack">{rows.map(c=>{const p=byCode[c.code];return <div className="campaign-card" key={c.id}><div className="campaign-main"><div><b>{c.name}</b><div className="small">{c.channel} · {region(c.market_code)}</div><code>{url(c)}</code></div><div className="campaign-actions"><button className="mini-btn" onClick={()=>copy(c,"link")}>{copied===`${c.code}-link`?"Kopiert ✓":"Link kopieren"}</button><button className="mini-btn" onClick={()=>copy(c,"post")}>{copied===`${c.code}-post`?"Kopiert ✓":"Post kopieren"}</button></div></div><div className="funnel-metrics"><span><b>{p?.views||0}</b> Aufrufe</span><span><b>{p?.starts||0}</b> Starts</span><span><b>{p?.results||0}</b> Ergebnisse</span><span><b>{p?.contact_views||0}</b> Kontakt</span><span><b>{p?.leads||0}</b> Leads</span><span><b>{p?.qualified||0}</b> Qualified</span><span><b>{p?.appointments||0}</b> Termine</span><span><b>{p?.lead_rate??"–"}{p?.lead_rate!=null?"%":""}</b> View→Lead</span></div></div>})}</div></section>
 <section className="card detail-card" style={{marginTop:16}}><div className="section-title">So starten wir organisch</div><div className="organic-grid"><div><b>WhatsApp lokal</b><p className="small">Nur in passenden Gruppen/Status posten. Waldshut und Köln haben getrennte Links, damit wir Conversion vergleichen können.</p></div><div><b>Facebook-Gruppen</b><p className="small">Mehrwert statt Spam: kostenloser regionaler Check. Gruppenregeln beachten und pro Region den richtigen Link verwenden.</p></div><div><b>QR / Offline</b><p className="small">Später kann genau derselbe Link als QR auf Partnerkarten, Aushängen oder Flyern verwendet werden.</p></div><div><b>Lernen</b><p className="small">Nicht Klicks optimieren, sondern Qualified Rate und Termine. Das ist unsere echte wirtschaftliche Kennzahl.</p></div></div></section>
 </div>
}
