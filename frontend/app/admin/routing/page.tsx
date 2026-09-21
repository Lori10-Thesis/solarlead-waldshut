"use client";
import { useEffect,useState } from "react";
import Link from "next/link";
import { ApiError,api } from "@/lib/api";

export default function Routing(){
  const [d,setD]=useState<any>(null);
  useEffect(()=>{api<any>("/api/admin/routing").then(setD).catch(e=>{if(e instanceof ApiError&&e.status===401)location.href="/admin/login"})},[]);
  if(!d)return <div className="container dashboard"><p>Lade Routing …</p></div>;
  return <div className="container dashboard"><div className="topbar"><div><div className="brand">Solar<span>Lead</span> / Routing</div><p>Markets → Territories → Vertriebsteams</p></div><div className="navlinks" style={{display:"flex"}}><Link href="/admin">Leads</Link><Link href="/geo">Geo-Radar</Link></div></div>
  <div className="routing-grid">
    <div className="card feature"><h2>Märkte</h2><div className="routing-list">{d.markets.map((m:any)=><div className="routing-row" key={m.code}><div><b>{m.name}</b><br/><span>{m.code} · {m.state_code}</span></div><span>{m.building_provider}</span></div>)}</div></div>
    <div className="card feature"><h2>Verticals</h2><div className="routing-list">{d.verticals.map((v:any)=><div className="routing-row" key={v.code}><div><b>{v.name}</b><br/><span>{v.code}</span></div><span>{v.active?"aktiv":"inaktiv"}</span></div>)}</div></div>
    <div className="card feature"><h2>Vertrieb</h2><div className="routing-list">{d.sales_reps.map((r:any)=><div className="routing-row" key={r.id}><div><b>{r.name}</b><br/><span>{r.partner||"intern"}</span></div><span>{r.active?"aktiv":"inaktiv"}</span></div>)}</div></div>
    <div className="card feature"><h2>Territories</h2><div className="routing-list">{d.territories.map((t:any)=><div className="routing-row" key={t.id}><div><b>{t.name}</b><br/><span>{t.market_code} · {t.vertical_code}</span></div><span>{t.sales_rep}<br/>max. {t.max_leads_per_day}/Tag</span></div>)}</div></div>
  </div></div>
}
