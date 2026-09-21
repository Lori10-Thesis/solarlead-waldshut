"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ApiError, api } from "@/lib/api";

type Lead = {
  id:number; created_at:string; first_name:string; last_name:string; email:string; phone:string;
  postal_code:string; city:string; street:string|null; house_number:string|null;
  latitude:number|null; longitude:number|null; orientation:string; shading:string; owner_status:string;
  installation_location:string; annual_consumption_kwh:number; electricity_price_eur_kwh:number;
  purchase_timeframe:string; wants_installation:boolean; pv_yield_kwh:number|null;
  annual_savings_eur:number|null; lead_score:number; status:string;
  utm_source:string|null; utm_medium:string|null; utm_campaign:string|null; utm_content:string|null;
  consent_marketing:boolean; consent_partner_sharing:boolean; consent_text_version:string;
  consent_timestamp:string; qualification_notes:string|null; source_type:string; source_id:string|null; cost_eur:number; revenue_eur:number; duplicate_of_id:number|null; assigned_partner:string|null;
};

type Qualification = {
  reached:boolean; interest_confirmed:boolean; project_fit_confirmed:boolean;
  appointment_requested:boolean; budget_or_purchase_ready:boolean; notes:string; status:string;
};

const initial: Qualification = {
  reached:false, interest_confirmed:false, project_fit_confirmed:false,
  appointment_requested:false, budget_or_purchase_ready:false, notes:"", status:"contacted"
};

const labels: Record<string,string> = {
  south:"Süd", south_west:"Süd-West", south_east:"Süd-Ost", west:"West", east:"Ost", north:"Nord",
  low:"Kaum Schatten", medium:"Teilweise Schatten", high:"Stark verschattet", unknown:"Unbekannt",
  owner:"Eigentümer", tenant:"Mieter", immediately:"Sofort", "30_days":"≤ 30 Tage", "3_months":"≤ 3 Monate", information:"Information"
};

export default function LeadDetail() {
  const params = useParams<{id:string}>();
  const id = params.id;
  const [lead,setLead] = useState<Lead|null>(null);
  const [q,setQ] = useState<Qualification>(initial);
  const [saved,setSaved] = useState("");
  const [error,setError] = useState("");

  useEffect(()=>{
    api<Lead>(`/api/admin/leads/${id}`).then(l=>{
      setLead(l);
      if(l.qualification_notes){
        try { setQ({...initial,...JSON.parse(l.qualification_notes)}); } catch {}
      } else {
        setQ(v=>({...v,status:l.status || "contacted"}));
      }
    }).catch((e)=>{ if(e instanceof ApiError && e.status===401){ window.location.href="/admin/login"; return; } setError("Lead konnte nicht geladen werden."); });
  },[id]);

  const completeness = useMemo(()=>{
    const checks = [q.reached,q.interest_confirmed,q.project_fit_confirmed,q.appointment_requested,q.budget_or_purchase_ready];
    return Math.round(checks.filter(Boolean).length / checks.length * 100);
  },[q]);

  const save = async () => {
    setSaved(""); setError("");
    try {
      const updated = await api<Lead>(`/api/admin/leads/${id}/qualification`, {method:"PATCH",body:JSON.stringify(q)});
      setLead(updated); setSaved("Qualifizierung gespeichert.");
    } catch { setError("Speichern fehlgeschlagen."); }
  };

  if(error && !lead) return <div className="container dashboard"><div className="error">{error}</div></div>;
  if(!lead) return <div className="container dashboard"><p>Lead wird geladen…</p></div>;

  return <div className="container dashboard">
    <div className="topbar">
      <div>
        <Link className="small" href="/admin">← Zur Leadliste</Link>
        <div className="brand" style={{marginTop:10}}>{lead.first_name} {lead.last_name}</div>
        <p>Lead #{lead.id} · {new Date(lead.created_at).toLocaleString("de-DE")}</p>
      </div>
      <div className="lead-score-big">{lead.lead_score}<span>/100</span></div>
    </div>

    <div className="detail-grid">
      <section className="card detail-card">
        <div className="section-title">Kontakt</div>
        <div className="info-list">
          <div><span>Telefon</span><a href={`tel:${lead.phone}`}>{lead.phone}</a></div>
          <div><span>E-Mail</span><a href={`mailto:${lead.email}`}>{lead.email}</a></div>
          <div><span>Adresse</span><b>{[lead.street,lead.house_number,lead.postal_code,lead.city].filter(Boolean).join(" ")}</b></div>
          <div><span>Quelle</span><b>{lead.source_id || lead.utm_source || lead.source_type || "Direkt"} {lead.utm_campaign ? `· ${lead.utm_campaign}`:""}</b></div>
        </div>
      </section>

      <section className="card detail-card">
        <div className="section-title">PV-Potenzial</div>
        <div className="two-metrics">
          <div className="metric"><span className="small">Ertrag</span><strong>{lead.pv_yield_kwh || "–"} kWh</strong><span className="small">pro Jahr</span></div>
          <div className="metric"><span className="small">Ersparnis</span><strong>{lead.annual_savings_eur || "–"} €</strong><span className="small">pro Jahr</span></div>
        </div>
        <div className="info-list compact">
          <div><span>Ausrichtung</span><b>{labels[lead.orientation] || lead.orientation}</b></div>
          <div><span>Verschattung</span><b>{labels[lead.shading] || lead.shading}</b></div>
          <div><span>Verbrauch</span><b>{lead.annual_consumption_kwh.toLocaleString("de-DE")} kWh/Jahr</b></div>
          <div><span>Wohnsituation</span><b>{labels[lead.owner_status] || lead.owner_status}</b></div>
          <div><span>Kaufzeitpunkt</span><b>{labels[lead.purchase_timeframe] || lead.purchase_timeframe}</b></div>
          <div><span>Montage</span><b>{lead.wants_installation ? "Gewünscht" : "Nicht angegeben"}</b></div>
        </div>
      </section>
    </div>

    <section className="card detail-card qualification-card">
      <div className="qualification-head">
        <div><div className="section-title">Vertriebsqualifizierung</div><p className="small">Telefonisch prüfen und den Lead anschließend als qualifiziert oder Termin markieren.</p></div>
        <div className="qual-progress"><b>{completeness}%</b><span>geprüft</span></div>
      </div>

      <div className="qual-grid">
        {[
          ["reached","Person telefonisch erreicht"],
          ["interest_confirmed","Kaufinteresse bestätigt"],
          ["project_fit_confirmed","Balkon / Projekt passt grundsätzlich"],
          ["budget_or_purchase_ready","Kaufbereitschaft / Budget bestätigt"],
          ["appointment_requested","Beratungstermin gewünscht"],
        ].map(([key,label])=><label className="qual-check" key={key}>
          <input type="checkbox" checked={(q as any)[key]} onChange={e=>setQ(v=>({...v,[key]:e.target.checked}))}/>
          <span>{label}</span>
        </label>)}
      </div>

      <div className="grid2">
        <div className="field"><label>Status nach Prüfung</label>
          <select value={q.status} onChange={e=>setQ(v=>({...v,status:e.target.value}))}>
            <option value="contacted">Kontaktiert</option><option value="qualified">Qualifiziert</option>
            <option value="appointment">Termin</option><option value="sold">An Partner verkauft</option>
            <option value="won">Gewonnen</option><option value="lost">Verloren</option>
          </select>
        </div>
        <div className="field"><label>Dateneinwilligung</label><div className="consent-box">Partnerweitergabe: {lead.consent_partner_sharing?"✓":"–"}<br/>Kontakt: {lead.consent_marketing?"✓":"–"}<br/><span className="small">Version {lead.consent_text_version}</span></div></div>
      </div>

      <div className="field"><label>Vertriebsnotizen</label><textarea value={q.notes} onChange={e=>setQ(v=>({...v,notes:e.target.value}))} placeholder="z. B. Rückruf Mittwoch 18 Uhr, Mieter fragt Vermieter an…"/></div>
      <button className="btn" onClick={save}>Qualifizierung speichern</button>
      {saved && <div className="success-msg">{saved}</div>}
      {error && <div className="error">{error}</div>}
    </section>
  </div>;
}
