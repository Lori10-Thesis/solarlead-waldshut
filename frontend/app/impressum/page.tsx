import Link from "next/link";
import { publicConfigComplete, site } from "@/lib/site";

export default function Page(){
  const name=[site.operatorName,site.operatorLegalForm].filter(Boolean).join(" ");
  return <div className="container legal-page">
    <nav className="nav"><div className="brand">{site.consumerBrand}</div><Link href="/">Zurück</Link></nav>
    <section className="card detail-card" style={{marginTop:40}}>
      <h1 style={{fontSize:48}}>Impressum</h1>
      {!publicConfigComplete() && <div className="error">Betreiberangaben sind noch nicht vollständig konfiguriert. Diese Preview darf so nicht öffentlich beworben werden.</div>}
      <h2>Angaben gemäß § 5 DDG</h2>
      <p><b>{name || "[Betreibername fehlt]"}</b><br/>
      {site.addressLine1 || "[Straße/Hausnummer fehlt]"}<br/>
      {site.addressLine2 && <>{site.addressLine2}<br/></>}
      {site.postalCity || "[PLZ/Ort fehlt]"}<br/>{site.country}</p>
      <h2>Kontakt</h2>
      <p>E-Mail: {site.email ? <a href={`mailto:${site.email}`}>{site.email}</a> : "[fehlt]"}<br/>
      {site.phone && <>Telefon: <a href={`tel:${site.phone}`}>{site.phone}</a></>}</p>
      {(site.registerCourt || site.registerNumber) && <><h2>Register</h2><p>{site.registerCourt}<br/>{site.registerNumber}</p></>}
      {site.vatId && <><h2>Umsatzsteuer</h2><p>Umsatzsteuer-Identifikationsnummer: {site.vatId}</p></>}
      <p className="small">Die konkrete Pflichtangabenlage hängt von Rechtsform und Tätigkeit des Betreibers ab. Vor dem öffentlichen Start sollte diese Seite rechtlich geprüft werden.</p>
    </section>
  </div>;
}
