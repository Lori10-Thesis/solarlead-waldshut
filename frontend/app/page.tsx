"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { operatorDisplay, site } from "@/lib/site";

type Form = {
  postal_code:string; city:string; street:string; house_number:string;
  owner_status:string; installation_location:string; orientation:string; shading:string;
  annual_consumption_kwh:number; electricity_price_eur_kwh:number;
  purchase_timeframe:string; product_preference:string; wants_installation:boolean;
  first_name:string; last_name:string; phone:string; email:string; contact_time:string;
  consent_marketing:boolean; consent_partner_sharing:boolean;
};

type Receipt={id:number;status:string;market_code:string;lead_score:number;geo_fit_score:number|null;assigned:boolean;public_token:string|null};

const initial:Form={
  postal_code:"",city:"",street:"",house_number:"",owner_status:"",installation_location:"balcony",
  orientation:"",shading:"",annual_consumption_kwh:2500,electricity_price_eur_kwh:0.34,
  purchase_timeframe:"",product_preference:"",wants_installation:true,
  first_name:"",last_name:"",phone:"",email:"",contact_time:"",
  consent_marketing:false,consent_partner_sharing:false
};

const orientationLabels:Record<string,string>={south:"Süd",south_west:"Süd-West",south_east:"Süd-Ost",west:"West",east:"Ost",north:"Nord",unknown:"Weiß ich nicht"};
const timeframeLabels:Record<string,string>={immediately:"So schnell wie möglich","30_days":"Innerhalb 30 Tagen","3_months":"Innerhalb 3 Monaten",information:"Ich informiere mich erst"};
const preferenceLabels:Record<string,string>={complete_with_installation:"Komplettlösung inkl. Montage",set_only:"Balkonkraftwerk / Set",consultation:"Erst beraten lassen"};

export default function Home(){
  const [step,setStep]=useState(0);
  const [form,setForm]=useState<Form>(initial);
  const [result,setResult]=useState<any>(null);
  const [receipt,setReceipt]=useState<Receipt|null>(null);
  const [utm,setUtm]=useState<Record<string,string>>({});
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [addressSaved,setAddressSaved]=useState(false);
  const [marketHint,setMarketHint]=useState("");
  const sessionRef=useRef("");

  const track=(event_type:string, tracking:Record<string,string>=utm)=>{
    if(!sessionRef.current) return;
    api("/api/funnel/events",{method:"POST",body:JSON.stringify({
      session_id:sessionRef.current,event_type,vertical_code:"balcony_pv",market_code:marketHint||tracking.market||null,
      source_id:tracking.source_id||null,utm_source:tracking.utm_source||null,utm_medium:tracking.utm_medium||null,
      utm_campaign:tracking.utm_campaign||null,utm_content:tracking.utm_content||null,
      landing_path:location.pathname,referrer:document.referrer||null
    })}).catch(()=>{});
  };

  useEffect(()=>{
    const p=new URLSearchParams(location.search);
    const tracking={source_id:p.get("src")||"",utm_source:p.get("utm_source")||"",utm_medium:p.get("utm_medium")||"",utm_campaign:p.get("utm_campaign")||"",utm_content:p.get("utm_content")||"",market:p.get("market")||""};
    setUtm(tracking); setMarketHint(tracking.market);
    const sid=(typeof crypto!=="undefined"&&"randomUUID" in crypto)?crypto.randomUUID():`${Date.now()}-${Math.random()}`;
    sessionRef.current=sid;
    api("/api/funnel/events",{method:"POST",body:JSON.stringify({session_id:sid,event_type:"landing_view",vertical_code:"balcony_pv",market_code:tracking.market||null,source_id:tracking.source_id||null,utm_source:tracking.utm_source||null,utm_medium:tracking.utm_medium||null,utm_campaign:tracking.utm_campaign||null,utm_content:tracking.utm_content||null,landing_path:location.pathname,referrer:document.referrer||null})}).catch(()=>{});
  },[]);
  const set=(k:keyof Form,v:any)=>setForm(x=>({...x,[k]:v}));
  const progress=Math.min(100,Math.round((step/11)*100));

  const calculate=async()=>{
    setBusy(true);setError("");
    try{
      const r=await api<any>("/api/pv/calculate",{method:"POST",body:JSON.stringify({
        postal_code:form.postal_code,city:"",street:null,house_number:null,orientation:form.orientation||"unknown",shading:form.shading||"unknown",
        annual_consumption_kwh:form.annual_consumption_kwh,electricity_price_eur_kwh:form.electricity_price_eur_kwh
      })}); setResult(r); setStep(8); track("pv_result_viewed");
    }catch{ setError("Die Potenzialberechnung ist gerade nicht verfügbar. Bitte versuche es erneut."); }
    finally{setBusy(false);}
  };

  const submit=async()=>{
    setBusy(true);setError("");
    try{
      const r=await api<Receipt>("/api/leads",{method:"POST",body:JSON.stringify({
        vertical:"balcony_pv", postal_code:form.postal_code,city:"",street:null,house_number:null,
        orientation:form.orientation||"unknown",shading:form.shading||"unknown",annual_consumption_kwh:form.annual_consumption_kwh,
        electricity_price_eur_kwh:form.electricity_price_eur_kwh,first_name:form.first_name,last_name:form.last_name,email:form.email||null,phone:form.phone,
        installation_location:form.installation_location,owner_status:form.owner_status,wants_installation:form.wants_installation,
        purchase_timeframe:form.purchase_timeframe,product_preference:form.product_preference,contact_time:form.contact_time,review_confirmed:true,
        consent_marketing:form.consent_marketing,consent_partner_sharing:form.consent_partner_sharing,consent_text_version:"v3_public_contact",
        funnel_session_id:sessionRef.current||null,landing_path:location.pathname,referrer:document.referrer||null,...utm
      })}); setReceipt(r); setStep(11);
    }catch(e:any){ setError(e?.message||"Die Anfrage konnte nicht gespeichert werden."); }
    finally{setBusy(false);}
  };

  const saveAddress=async()=>{
    if(!receipt?.public_token||!form.street||!form.house_number)return;
    setBusy(true);setError("");
    try{ await api(`/api/leads/${receipt.public_token}/address`,{method:"PATCH",body:JSON.stringify({street:form.street,house_number:form.house_number,city:form.city})}); setAddressSaved(true); }
    catch{setError("Die Adresse konnte nicht ergänzt werden.");} finally{setBusy(false);}
  };

  const summary=useMemo(()=>[
    ["Region",form.postal_code],["Wohnsituation",form.owner_status==="owner"?"Eigentümer":"Mieter"],
    ["Ausrichtung",orientationLabels[form.orientation]||"–"],["Kaufzeitpunkt",timeframeLabels[form.purchase_timeframe]||"–"],
    ["Wunsch",preferenceLabels[form.product_preference]||"–"]
  ],[form]);

  const next=(n:number)=>{
    setError("");
    if(step===0&&n===1) track("funnel_started");
    if(n===9) track("contact_step_viewed");
    if(n===10) track("review_viewed");
    setStep(n)
  };

  const marketLabel=marketHint==="koeln"?"Köln":marketHint==="waldshut"?"Waldshut / Hochrhein":"deiner Region";

  return <>
    <div className="container">
      <nav className="nav"><div className="brand">{site.consumerBrand}</div><div className="trustline">Kostenlos · unverbindlich · regionaler Balkon-PV Check</div></nav>

      <main className="funnel-shell">
        <section className="funnel-copy">
          <div className="kicker">Balkon-PV Check · {marketLabel}</div>
          <h1>{marketHint?`Lohnt sich ein Balkonkraftwerk in ${marketLabel}?`:"Lohnt sich ein Balkonkraftwerk bei dir?"}</h1>
          <p>Prüfe kostenlos dein Balkon-PV-Potenzial. Du bekommst zuerst eine Potenzialschätzung – Kontaktdaten fragen wir erst, wenn du passende regionale Angebote möchtest.</p>
          <div className="trust-grid"><span>✓ keine Adresse nötig</span><span>✓ Ergebnis vor Kontaktdaten</span><span>✓ regionale Zuordnung</span></div>
        </section>

        <section className="card funnel-card">
          <div className="progressbar"><i style={{width:`${progress}%`}}/></div>
          {step<8 && <div className="step-caption">Schritt {step+1} von 8</div>}

          {step===0&&<><h2>Wo soll das Projekt umgesetzt werden?</h2><p>Die PLZ reicht für die erste regionale Analyse.</p><div className="field"><label>Postleitzahl</label><input autoFocus inputMode="numeric" maxLength={5} placeholder="z. B. 79761 oder 50667" value={form.postal_code} onChange={e=>set("postal_code",e.target.value.replace(/\D/g,""))}/></div><button className="btn" disabled={form.postal_code.length!==5} onClick={()=>next(1)}>Weiter →</button></>}

          {step===1&&<><h2>Wie wohnst du?</h2><div className="choice-stack"><button className={"choice big "+(form.owner_status==="owner"?"active":"")} onClick={()=>{set("owner_status","owner");next(2)}}>Eigentümer</button><button className={"choice big "+(form.owner_status==="tenant"?"active":"")} onClick={()=>{set("owner_status","tenant");next(2)}}>Mieter</button></div><Back onClick={()=>next(0)}/></>}

          {step===2&&<><h2>Wo soll die Anlage hin?</h2><div className="choice-grid"><Choice label="Balkon" active={form.installation_location==="balcony"} onClick={()=>set("installation_location","balcony")}/><Choice label="Terrasse" active={form.installation_location==="terrace"} onClick={()=>set("installation_location","terrace")}/><Choice label="Garage" active={form.installation_location==="garage"} onClick={()=>set("installation_location","garage")}/><Choice label="Noch offen" active={form.installation_location==="unknown"} onClick={()=>set("installation_location","unknown")}/></div><Nav back={()=>next(1)} next={()=>next(3)}/></>}

          {step===3&&<><h2>Welche Ausrichtung hat die Fläche?</h2><div className="choice-grid">{Object.entries(orientationLabels).map(([k,v])=><Choice key={k} label={v} active={form.orientation===k} onClick={()=>set("orientation",k)}/>)}</div><Nav back={()=>next(2)} next={()=>next(4)} disabled={!form.orientation}/></>}

          {step===4&&<><h2>Wie stark ist die Fläche verschattet?</h2><div className="choice-stack"><Choice label="Kaum / fast immer frei" active={form.shading==="low"} onClick={()=>set("shading","low")}/><Choice label="Teilweise" active={form.shading==="medium"} onClick={()=>set("shading","medium")}/><Choice label="Stark" active={form.shading==="high"} onClick={()=>set("shading","high")}/><Choice label="Weiß ich nicht" active={form.shading==="unknown"} onClick={()=>set("shading","unknown")}/></div><Nav back={()=>next(3)} next={()=>next(5)} disabled={!form.shading}/></>}

          {step===5&&<><h2>Wie hoch ist dein Stromverbrauch?</h2><p>Wenn du ihn nicht kennst, reicht eine typische Haushaltsgröße.</p><div className="choice-grid"><Choice label="1 Person · ~1.500 kWh" active={form.annual_consumption_kwh===1500} onClick={()=>set("annual_consumption_kwh",1500)}/><Choice label="2 Personen · ~2.500 kWh" active={form.annual_consumption_kwh===2500} onClick={()=>set("annual_consumption_kwh",2500)}/><Choice label="3 Personen · ~3.500 kWh" active={form.annual_consumption_kwh===3500} onClick={()=>set("annual_consumption_kwh",3500)}/><Choice label="4+ Personen · ~4.500 kWh" active={form.annual_consumption_kwh===4500} onClick={()=>set("annual_consumption_kwh",4500)}/></div><Nav back={()=>next(4)} next={()=>next(6)}/></>}

          {step===6&&<><h2>Wann möchtest du starten?</h2><div className="choice-stack">{Object.entries(timeframeLabels).map(([k,v])=><Choice key={k} label={v} active={form.purchase_timeframe===k} onClick={()=>set("purchase_timeframe",k)}/>)}</div><Nav back={()=>next(5)} next={()=>next(7)} disabled={!form.purchase_timeframe}/></>}

          {step===7&&<><h2>Was ist für dich interessant?</h2><div className="choice-stack"><Choice label="Komplettlösung inklusive Montage" active={form.product_preference==="complete_with_installation"} onClick={()=>{set("product_preference","complete_with_installation");set("wants_installation",true)}}/><Choice label="Balkonkraftwerk / Set" active={form.product_preference==="set_only"} onClick={()=>{set("product_preference","set_only");set("wants_installation",false)}}/><Choice label="Erst beraten lassen" active={form.product_preference==="consultation"} onClick={()=>set("product_preference","consultation")}/></div><div className="actions"><button className="btn secondary" onClick={()=>next(6)}>Zurück</button><button className="btn" disabled={!form.product_preference||busy} onClick={calculate}>{busy?"Berechne …":"Potenzial anzeigen →"}</button></div>{error&&<div className="error">{error}</div>}</>}

          {step===8&&result&&<><div className="result-head"><span className="kicker">Deine Potenzialschätzung</span><div className="score">{result.potential_score}/100</div></div><div className="grid2"><div className="metric"><span>Ertrag</span><strong>{Math.round(result.pv_yield_kwh)} kWh</strong><small>pro Jahr</small></div><div className="metric"><span>Ersparnis*</span><strong>{Math.round(result.annual_savings_eur)} €</strong><small>pro Jahr</small></div></div><p className="small">* Orientierungswert auf PLZ-/Standortbasis. Noch keine individuelle Angebotsgarantie.</p><button className="btn" onClick={()=>next(9)}>Passende Angebote vergleichen →</button><button className="text-btn" onClick={()=>next(7)}>Angaben ändern</button></>}

          {step===9&&<><h2>Wie können wir dich erreichen?</h2><p>Für einen passenden regionalen Anbieter benötigen wir eine Telefonnummer. E-Mail ist optional.</p><div className="field"><label>Vorname</label><input value={form.first_name} onChange={e=>set("first_name",e.target.value)} placeholder="Vorname"/></div><div className="field"><label>Telefonnummer</label><input inputMode="tel" value={form.phone} onChange={e=>set("phone",e.target.value)} placeholder="z. B. 0176 …"/></div><div className="field"><label>E-Mail <span className="muted">optional</span></label><input type="email" value={form.email} onChange={e=>set("email",e.target.value)} placeholder="name@beispiel.de"/></div><div className="field"><label>Am besten erreichbar</label><select value={form.contact_time} onChange={e=>set("contact_time",e.target.value)}><option value="">Bitte wählen</option><option value="morning">Vormittags</option><option value="midday">Mittags</option><option value="afternoon">Nachmittags</option><option value="evening">Abends</option></select></div><Nav back={()=>next(8)} next={()=>next(10)} disabled={!form.first_name||form.phone.length<6||!form.contact_time}/></>}

          {step===10&&<><h2>Bitte kurz prüfen</h2><div className="review-card">{summary.map(([k,v])=><div key={k}><span>{k}</span><b>{v}</b></div>)}</div><div className="checkbox"><input type="checkbox" checked={form.consent_marketing} onChange={e=>set("consent_marketing",e.target.checked)}/><span className="small">Ich bitte {operatorDisplay()} ausdrücklich, mich zu meiner konkreten Balkon-PV-Anfrage telefonisch und – falls angegeben – per E-Mail zu kontaktieren. Die Einwilligung kann ich jederzeit für die Zukunft widerrufen.</span></div><div className="optional-box"><b>Keine automatische Partnerweitergabe</b><p className="small">Deine Kontaktdaten werden nicht bereits mit diesem Klick pauschal verkauft oder an beliebige Anbieter verteilt. Wenn nach der Vorqualifizierung ein konkreter Fachpartner passt, wird die Weitergabe an diesen Partner separat bestätigt und dokumentiert.</p></div><div className="actions"><button className="btn secondary" onClick={()=>next(9)}>Zurück</button><button className="btn" disabled={!form.consent_marketing||busy} onClick={submit}>{busy?"Sende …":"Anfrage bestätigen →"}</button></div>{error&&<div className="error">{error}</div>}</>}

          {step===11&&receipt&&<><div className="success-icon">✓</div><h2>Anfrage ist eingegangen.</h2><p>Dein Lead-Score liegt aktuell bei <b>{receipt.lead_score}/100</b>. {receipt.assigned?"Die Anfrage wurde bereits dem passenden regionalen Vertrieb zugeordnet.":"Die Anfrage liegt in unserer Qualifizierungswarteschlange."}</p><div className="optional-box"><b>Optional: Standortanalyse verfeinern</b><p className="small">Straße und Hausnummer sind nicht erforderlich. Wenn du sie freiwillig ergänzt, können wir den Standort genauer berechnen.</p>{!addressSaved?<><div className="grid2"><input placeholder="Straße" value={form.street} onChange={e=>set("street",e.target.value)}/><input placeholder="Hausnr." value={form.house_number} onChange={e=>set("house_number",e.target.value)}/></div><button className="btn secondary" disabled={!form.street||!form.house_number||busy} onClick={saveAddress}>Standort verfeinern</button></>:<div className="success-note">Standort wurde ergänzt ✓</div>}</div>{error&&<div className="error">{error}</div>}</>}
        </section>
      </main>

      <section className="section"><h2>Warum wir so fragen</h2><div className="three"><div className="card feature"><b>Erst Nutzen</b><p>Die Potenzialschätzung kommt vor den Kontaktdaten. Das reduziert unnötige Hürden.</p></div><div className="card feature"><b>Kaufabsicht zählt</b><p>Zeitpunkt und Produktwunsch fließen stärker in den Lead-Score ein als reine Technikdetails.</p></div><div className="card feature"><b>Regional geroutet</b><p>Die PLZ ordnet die Anfrage automatisch einem aktiven Vertriebsgebiet zu.</p></div></div></section>
      <footer className="footer"><div>{site.consumerBrand} · betrieben von {operatorDisplay()}</div><div className="legal-links"><Link href="/impressum">Impressum</Link><Link href="/datenschutz">Datenschutz</Link></div></footer>
    </div>
  </>;
}

function Choice({label,active,onClick}:{label:string;active:boolean;onClick:()=>void}){return <button type="button" className={"choice "+(active?"active":"")} onClick={onClick}>{label}</button>}
function Back({onClick}:{onClick:()=>void}){return <button className="text-btn" onClick={onClick}>← Zurück</button>}
function Nav({back,next,disabled=false}:{back:()=>void;next:()=>void;disabled?:boolean}){return <div className="actions"><button className="btn secondary" onClick={back}>Zurück</button><button className="btn" disabled={disabled} onClick={next}>Weiter →</button></div>}
