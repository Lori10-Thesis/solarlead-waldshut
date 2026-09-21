"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { API, ApiError, api } from "@/lib/api";

type Lead = {
  market_code:string; geo_fit_score:number|null; assigned_sales_rep_id:number|null;
  id:number; created_at:string; first_name:string; last_name:string; email:string; phone:string;
  postal_code:string; city:string; orientation:string; shading:string; owner_status:string;
  purchase_timeframe:string; wants_installation:boolean; pv_yield_kwh:number|null;
  annual_savings_eur:number|null; lead_score:number; status:string;
  utm_source:string|null; utm_campaign:string|null; source_type:string; source_id:string|null; cost_eur:number; revenue_eur:number;
};

const statusLabel: Record<string,string> = {
  new:"Neu", duplicate:"Duplikat", contacted:"Kontaktiert", qualified:"Qualifiziert", sales_ready:"Sales Ready", appointment:"Termin",
  sold:"Verkauft", won:"Gewonnen", lost:"Verloren"
};

export default function Admin() {
  const [leads,setLeads] = useState<Lead[]>([]);
  const [error,setError] = useState("");
  const [market,setMarket]=useState("");
  const [markets,setMarkets]=useState<any[]>([]);

  const load = () => api<Lead[]>(`/api/admin/leads${market?`?market=${market}`:""}`)
    .then(setLeads)
    .catch((e)=>{ if(e instanceof ApiError && e.status===401){ window.location.href="/admin/login"; return; } setError("Backend nicht erreichbar."); });

  useEffect(()=>{ api<any[]>("/api/platform/markets").then(setMarkets); },[]);
  useEffect(()=>{ load(); },[market]);

  const logout = async()=>{ try{ await api("/api/auth/logout",{method:"POST"}); } finally{ window.location.href="/admin/login"; } };

  const setStatus = async (id:number,status:string) => {
    await api(`/api/admin/leads/${id}/status`, {method:"PATCH",body:JSON.stringify({status})});
    load();
  };

  const stats = useMemo(()=>({
    total:leads.length,
    hot:leads.filter(l=>l.lead_score>=80).length,
    qualified:leads.filter(l=>["qualified","sales_ready","appointment","sold","won"].includes(l.status)).length,
    won:leads.filter(l=>l.status==="won").length
  }),[leads]);

  return <div className="container dashboard"><div className="admin-shortcuts"><Link className="mini-btn" href="/admin/acquisition">Organic Acquisition</Link><Link className="mini-btn" href="/admin/setter">Setter Ops</Link><Link className="mini-btn" href="/admin/buyers">Buyer Ops</Link><Link className="mini-btn" href="/admin/routing">Routing</Link><Link className="mini-btn" href="/admin/analytics">Analytics</Link></div>
    <div className="topbar">
      <div><div className="brand">Solar<span>Lead</span> / Admin</div><p>Lead Operations · V0.6</p></div>
      <div className="navlinks" style={{display:"flex"}}>
        <Link href="/">Funnel</Link><Link href="/geo">Geo-Radar</Link><Link href="/admin/routing">Routing</Link><Link href="/admin/analytics">Quellen</Link><a href={`${API}/api/admin/leads.csv`}>CSV Export</a><button className="link-btn" onClick={logout}>Logout</button>
      </div>
    </div>

    <div style={{marginBottom:16,maxWidth:320}}><label>Markt</label><select value={market} onChange={e=>setMarket(e.target.value)}><option value="">Alle Märkte</option>{markets.map((m:any)=><option key={m.code} value={m.code}>{m.name}</option>)}</select></div>

    <div className="statgrid">
      <div className="card stat"><span>Leads</span><strong>{stats.total}</strong></div>
      <div className="card stat"><span>Hot ≥80</span><strong className="hot">{stats.hot}</strong></div>
      <div className="card stat"><span>Qualifiziert+</span><strong>{stats.qualified}</strong></div>
      <div className="card stat"><span>Gewonnen</span><strong>{stats.won}</strong></div>
    </div>

    <div className="card table-wrap">
      <table>
        <thead><tr><th>Score</th><th>Lead</th><th>Ort</th><th>PV</th><th>Kauf</th><th>Quelle</th><th>Status</th><th>Aktion</th></tr></thead>
        <tbody>{leads.map(l=><tr key={l.id}>
          <td><span className="badge">{l.lead_score}</span></td>
          <td><Link href={`/admin/leads/${l.id}`}><b>{l.first_name} {l.last_name}</b></Link><br/><span className="small">{new Date(l.created_at).toLocaleString("de-DE")}</span></td>
          <td>{l.postal_code} {l.city}<br/><span className="small">{l.market_code} · Geo {l.geo_fit_score??"–"} · {l.orientation}</span></td>
          <td>{l.pv_yield_kwh ? `${l.pv_yield_kwh} kWh` : "–"}<br/><span className="small">{l.annual_savings_eur ? `${l.annual_savings_eur} €/Jahr` : ""}</span></td>
          <td>{l.purchase_timeframe}</td>
          <td>{l.source_id || l.utm_source || l.source_type || "direkt"}<br/><span className="small">{l.utm_campaign || ""}</span></td>
          <td>
            <select value={l.status} onChange={e=>setStatus(l.id,e.target.value)}>
              {Object.entries(statusLabel).map(([key,label])=><option key={key} value={key}>{label}</option>)}
            </select>
          </td>
          <td><Link className="mini-btn" href={`/admin/leads/${l.id}`}>Qualifizieren →</Link></td>
        </tr>)}</tbody>
      </table>
      {leads.length===0 && <div style={{padding:24}}><p>Noch keine Leads. Teste zuerst den Funnel auf der Startseite.</p></div>}
    </div>
    {error && <div className="error">{error}</div>}
  </div>;
}
