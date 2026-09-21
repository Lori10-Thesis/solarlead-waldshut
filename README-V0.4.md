# SolarLead V0.4 – Platform Core

V0.4 macht aus dem Waldshut-Pilot eine Multi-Market-/Multi-Vertical-Plattformbasis.

## Neu

- `Vertical`-Modell (erste Vertical: `balcony_pv`)
- `Market`-Modell: Waldshut + Köln
- `Partner`, `SalesRep`, `Territory`
- automatische PLZ→Market→Territory→SalesRep-Zuordnung
- getrennte `lead_score` und `geo_fit_score`
- Geo-Zellen gehören jetzt zu Market + Vertical
- Geo-Radar mit Marktumschalter
- NRW Building Provider (`GEOBASIS_NRW`) vorbereitet
- Progressive Funnel: keine Straße/Hausnummer am Anfang
- Ergebnis vor Kontaktdaten
- Telefonnummer Pflicht, E-Mail optional
- Kaufzeitpunkt und Produktwunsch stärker gewichtet
- Review-Step vor Lead-Abgabe
- freiwillige Adressverfeinerung nach Lead-Erstellung
- Routing-Dashboard `/admin/routing`
- Admin-Marktfilter

## Märkte

### Waldshut / Hochrhein
- State: BW
- Building provider: LGL BW
- bestehende echte Geo-Zellen werden migriert und beibehalten

### Köln
- State: NRW
- Building provider: Geobasis NRW
- Routing ist sofort aktiv
- Geo-Radar bleibt leer, bis echte Köln-Daten importiert wurden

## Datenprinzip

Keine Demo-Werte für einen neuen Markt. Datenreife wird separat vom Markt-/Routingstatus geführt.

## Nächster Data-Step

Köln:
1. Zensus 2022 100-m-Raster ausschneiden
2. Geobasis-NRW-Hausumringe aggregieren
3. PVGIS-Solar-Sampling
4. später MaStR
