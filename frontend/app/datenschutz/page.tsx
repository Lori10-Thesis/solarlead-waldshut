import Link from "next/link";
import { publicConfigComplete, site } from "@/lib/site";

export default function Page(){
  const controller=[site.operatorName,site.operatorLegalForm].filter(Boolean).join(" ") || "[Verantwortlicher fehlt]";
  return <div className="container legal-page">
    <nav className="nav"><div className="brand">{site.consumerBrand}</div><Link href="/">Zurück</Link></nav>
    <section className="card detail-card" style={{marginTop:40}}>
      <h1 style={{fontSize:48}}>Datenschutzerklärung</h1>
      {!publicConfigComplete() && <div className="error">Die Betreiberangaben sind noch nicht vollständig konfiguriert. Diese Preview darf so nicht öffentlich beworben werden.</div>}

      <h2>1. Verantwortlicher</h2>
      <p><b>{controller}</b><br/>{site.addressLine1}<br/>{site.addressLine2 && <>{site.addressLine2}<br/></>}{site.postalCity}<br/>{site.country}<br/>
      E-Mail: {site.privacyEmail || site.email || "[fehlt]"}</p>

      <h2>2. Zweck des Balkon-PV-Checks</h2>
      <p>Wir verarbeiten die von dir eingegebenen Projekt- und Kontaktdaten, um deine konkrete Balkon-PV-Anfrage zu bearbeiten, eine unverbindliche Potenzialschätzung zu erstellen, die Anfrage regional zuzuordnen und – wenn du dies ausdrücklich möchtest – mit dir zur Vorqualifizierung Kontakt aufzunehmen.</p>

      <h2>3. Welche Daten verarbeitet werden</h2>
      <p>Je nach Nutzung verarbeiten wir insbesondere PLZ, Wohn-/Projektsituation, Ausrichtung, Verschattung, geschätzten Stromverbrauch, Kaufzeitpunkt, Produktwunsch, Vorname, Telefonnummer, optionale E-Mail-Adresse sowie technische Nachweis- und Sicherheitsdaten wie Zeitstempel, User-Agent und IP-Adresse. Straße und Hausnummer sind im öffentlichen Funnel optional.</p>

      <h2>4. Potenzialberechnung und Geodienste</h2>
      <p>Für die Standort- und Ertragsabschätzung können Geocoding- und Solardaten-Dienste genutzt werden. Aktuell kann die Anwendung insbesondere Nominatim/OpenStreetMap zur Geocodierung und PVGIS der Europäischen Kommission zur Solarertragsberechnung anfragen. Bei der ersten Berechnung verwenden wir grundsätzlich nur die für den Check erforderlichen Standortangaben; eine genaue Anschrift ist nicht erforderlich.</p>

      <h2>5. Kontaktaufnahme</h2>
      <p>Eine Kontaktaufnahme erfolgt nur, wenn du sie im Funnel ausdrücklich für deine konkrete Anfrage anforderst. Die Einwilligung kann mit Wirkung für die Zukunft widerrufen werden. Soweit die Kontaktaufnahme rechtlich als Telefonwerbung einzuordnen ist, dokumentieren wir den Einwilligungsnachweis und dessen Verwendung entsprechend den gesetzlichen Vorgaben.</p>

      <h2>6. Weitergabe an Fachpartner</h2>
      <p>Der Website-Lead wird nicht automatisch pauschal an beliebige Fachpartner weitergegeben. Eine Weitergabe an einen konkreten Anbieter soll erst erfolgen, nachdem du dieser Weitergabe für den benannten Partner separat zugestimmt hast. Die Zustimmung wird mit Partner, Zeitpunkt und Bearbeiter dokumentiert.</p>

      <h2>7. Empfänger und Auftragsverarbeiter</h2>
      <p>Daten können an technisch erforderliche Dienstleister für Hosting, Infrastruktur und Betrieb übermittelt werden. {site.hostingProvider ? <>Als Hosting-/Infrastrukturanbieter ist aktuell <b>{site.hostingProvider}</b>{site.hostingCountry ? ` (${site.hostingCountry})` : ""} konfiguriert. </> : <>Der konkrete Produktions-Hostinganbieter wird vor Livegang hier ergänzt. </>}Ein ausgewählter Fachpartner erhält Kontaktdaten nur nach der oben beschriebenen separaten Zustimmung.</p>
      {site.cloudflareEnabled && <p>Für die öffentliche Bereitstellung kann Cloudflare als Netzwerk-/Tunnel-/Proxy-Dienst eingesetzt werden. Dabei können technisch notwendige Verbindungsdaten verarbeitet werden.</p>}

      <h2>8. Rechtsgrundlagen</h2>
      <p>Je nach Verarbeitung kommen insbesondere Art. 6 Abs. 1 lit. a DSGVO (Einwilligung), Art. 6 Abs. 1 lit. b DSGVO (vorvertragliche Maßnahmen auf Anfrage) und Art. 6 Abs. 1 lit. f DSGVO (berechtigte Interessen, etwa IT-Sicherheit und Missbrauchsschutz) in Betracht. Welche Grundlage konkret greift, richtet sich nach dem jeweiligen Verarbeitungsvorgang.</p>

      <h2>9. Speicherdauer</h2>
      <p>Leaddaten werden nur so lange gespeichert, wie dies für Anfragebearbeitung, Nachweis-, Rechtsverteidigungs- und gesetzliche Aufbewahrungszwecke erforderlich ist. Einwilligungsnachweise für Telefonwerbung müssen nach § 7a UWG grundsätzlich ab Erteilung sowie nach jeder Verwendung fünf Jahre aufbewahrt werden. Für andere Daten können kürzere oder längere gesetzliche Fristen gelten.</p>

      <h2>10. Funnel-Messung</h2>
      <p>Die Anwendung misst intern technische Funnel-Ereignisse wie Landingpage-Aufruf, Funnel-Start und Ergebnisansicht, um die eigene Lead-Strecke zu verbessern. Vor Absenden des Formulars werden diese Ereignisse über eine zufällige, nur im Arbeitsspeicher der geöffneten Seite gehaltene Kennung geführt und enthalten keine freiwillig eingegebenen Kontaktdaten. Der öffentliche Funnel speichert dafür keinen persistenten Analyse-Identifier im Browser. Wir setzen in dieser Version keine externen Werbe- oder Analyse-Cookies ein.</p>

      <h2>11. Deine Rechte</h2>
      <p>Du hast nach Maßgabe der DSGVO insbesondere Rechte auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Einwilligungen können für die Zukunft widerrufen werden. Außerdem besteht ein Beschwerderecht bei einer zuständigen Datenschutzaufsichtsbehörde.</p>

      <h2>12. Kontakt Datenschutz</h2>
      <p>{site.privacyEmail ? <a href={`mailto:${site.privacyEmail}`}>{site.privacyEmail}</a> : "[Datenschutz-Kontakt noch nicht konfiguriert]"}</p>

      <p className="small">Stand: August 2026. Diese Vorlage bildet den aktuellen technischen Stand der Anwendung ab und ersetzt keine individuelle rechtliche Prüfung.</p>
    </section>
  </div>;
}
