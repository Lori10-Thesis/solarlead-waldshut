# SolarLead Waldshut

Kompletter MVP einer Lead-Generation-WebApp für Balkonkraftwerke in der Pilotregion Waldshut.

## Was enthalten ist

- **Kunden-Funnel:** Adresse/PLZ, Balkon, Ausrichtung, Verschattung, Verbrauch
- **PV-Berechnung:** PVGIS-Anbindung mit lokaler Fallback-Berechnung
- **Ersparnis:** Jahres- und 10-Jahres-Schätzung
- **Lead Capture:** Kontaktdaten + dokumentierte Einwilligungsfelder
- **Lead Score:** 0–100 nach Kaufnähe und Eignung
- **Admin:** Leads, Kontakt, Status, CSV-Export
- **UTM-Tracking:** Quelle/Kampagne wird am Lead gespeichert
- **Geo-Radar:** interaktive Waldshut-Karte mit Potenzialzellen
- **Geo-Importer-Struktur:** vorbereitet für Zensus, LGL und MaStR

> Das Geo-Radar identifiziert **Gebietspotenziale, keine Privatpersonen**. Ein personenbezogener Lead entsteht erst durch die freiwillige Anfrage im Funnel.

## Projektstruktur

```text
solarlead-waldshut/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── scoring.py
│   │   ├── pv.py
│   │   ├── geo.py
│   │   ├── seed.py
│   │   └── importers/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── admin/page.tsx
│   │   ├── geo/page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── lib/api.ts
│   └── package.json
├── docker-compose.yml
└── README.md
```

# Start in VS Code

## Voraussetzungen

- Python 3.11+
- Node.js 20+
- VS Code

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Frontend

Zweites Terminal:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Danach:

```text
Kunden-Funnel: http://localhost:3000
Admin:         http://localhost:3000/admin
Geo-Radar:     http://localhost:3000/geo
```

# Funnel testen

1. `http://localhost:3000` öffnen.
2. Waldshut-Adresse bzw. PLZ eingeben.
3. Balkonparameter angeben.
4. PV-Potenzial berechnen.
5. Test-Kontaktdaten + beide Einwilligungen setzen.
6. Anfrage absenden.
7. `http://localhost:3000/admin` öffnen.
8. Der Lead erscheint inkl. Score und PV-Schätzung.

Mit UTM-Test:

```text
http://localhost:3000/?utm_source=instagram&utm_medium=paid_social&utm_campaign=waldshut_august&utm_content=video_1
```

# Geo-Radar

Der MVP enthält bewusst nur Demo-Scores, damit die Oberfläche sofort läuft. Produktiv wird `geo_cells` aus echten Geodaten berechnet.

Vorgesehene Inputs:

1. **Zensus 2022** – Wohnungs- und Gebäudestruktur auf Rasterebene
2. **LGL Baden-Württemberg** – Gebäude/Hausumringe/Koordinaten
3. **MaStR** – zulässige öffentliche/aggregierte PV-Marktdaten
4. **PVGIS** – solares Potenzial
5. **eigene Kampagnendaten** – CPL/Conversion nach Region

Beispielgewichtung:

```text
30 % Wohnungs-/Mehrfamilienhausdichte
25 % Gebäudeeignung
20 % solares Potenzial
15 % Marktlücke / geringe PV-Durchdringung
10 % eigene Kampagnenperformance
```

# Vor Produktion ergänzen

- PostgreSQL + PostGIS
- echtes Admin-Login / Rollen
- Partner-Accounts und Lead-Zuweisung
- Bezahl-/Abrechnungslogik
- Telefon-Qualifizierungsmaske
- Double-Opt-In / Einwilligungsnachweise passend zum finalen Prozess
- Datenschutz-/AGB-Prüfung
- produktionsgeeignetes Geocoding (der Nominatim-Aufruf im MVP ist nur Dev-Fallback)
- Rate Limiting, Logging, Monitoring, Backups
- echte Geo-Importer

# Zielarchitektur

```text
Traffic / Ads
    ↓
SolarLead Funnel
    ↓
PV-/Geo-Berechnung
    ↓
Opt-in + Lead
    ↓
Auto-Scoring
    ↓
Qualifizierung
    ↓
Partner-Marktplatz
    ↓
Lead-Verkauf / Termin
```

---

# V0.2 – Geo Intelligence + Vertriebsqualifizierung

V0.2 ergänzt den MVP um zwei Kernbereiche.

## 1. Lead-Detailansicht

Neue Route:

```text
/admin/leads/{id}
```

Dort kann der Vertrieb:

- Kontakt- und Kampagnendaten sehen
- PV-Ertrag und Ersparnis prüfen
- Kaufzeitpunkt / Wohnsituation / Montagewunsch sehen
- telefonisch erreicht markieren
- Interesse bestätigen
- Projektfit bestätigen
- Kaufbereitschaft bestätigen
- Terminwunsch markieren
- Vertriebsnotizen speichern
- den Status auf Kontaktiert / Qualifiziert / Termin / Verkauft / Gewonnen / Verloren setzen

Die Qualifizierung wird im bestehenden Feld `qualification_notes` als JSON gespeichert. Dadurch ist **keine Migration deiner vorhandenen SQLite-Datenbank nötig**.

## 2. Geo-Datenpipeline

Neue Dateien:

```text
backend/scripts/build_geo_cells.py
backend/scripts/load_geo_cells.py
backend/app/importers/README.md
backend/data/processed/EXAMPLE_*.csv
```

Der Geo-Score nutzt aktuell:

```text
30 % Wohnungs-/MFH-Dichte
25 % Gebäudeeignung
20 % solares Potenzial
15 % Marktlücke
10 % Kampagnenperformance
```

`/geo` zeigt automatisch `DEMO`, solange die Seed-Daten verwendet werden. Sobald du die erzeugten Geo-Zellen importierst, wechselt der Modus auf `IMPORTIERT`.

## V0.1 → V0.2 aktualisieren

Wenn dein V0.1 bereits lokal läuft:

1. Frontend und Backend mit `Ctrl+C` stoppen.
2. Sicherung anlegen:

```bash
cp backend/solarlead.db backend/solarlead-backup.db 2>/dev/null || true
```

3. V0.2-Quelldateien über deine bestehenden Quelldateien kopieren.
4. Deine vorhandene `.env` und `frontend/.env.local` behalten.
5. Frontend:

```bash
cd frontend
npm install
npm run dev
```

6. Backend in zweitem Terminal:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

7. Testen:

- `http://localhost:3000/admin`
- einen Lead anklicken
- Qualifizierung speichern
- `http://localhost:3000/geo`

## Geo-Pipeline mit Beispieldaten testen

Vom Projektordner:

```bash
cd backend
cp data/processed/EXAMPLE_zensus_cells.csv data/processed/zensus_cells.csv
cp data/processed/EXAMPLE_lgl_cells.csv data/processed/lgl_cells.csv
cp data/processed/EXAMPLE_mastr_cells.csv data/processed/mastr_cells.csv
cp data/processed/EXAMPLE_campaign_cells.csv data/processed/campaign_cells.csv
python scripts/build_geo_cells.py
PYTHONPATH=. python scripts/load_geo_cells.py
```

Danach `/geo` neu laden. Der Datenmodus sollte `IMPORTIERT` anzeigen.

**Die Beispieldaten sind nur zum technischen Test gedacht und keine realen Marktwerte.**

## V0.2 – echte Zensus-2022-Daten für Waldshut

Das Geo-Radar kann nun aus dem offiziellen 100-m-Zensusdatensatz **„Gebäude mit
Wohnraum nach Anzahl der Wohnungen im Gebäude“** gespeist werden.

### Einmalig zusätzliche Python-Abhängigkeit installieren

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Offizielle Daten laden

```bash
python scripts/download_zensus.py
```

Das Skript lädt direkt vom veröffentlichten Destatis-Endpunkt und entpackt die
10-km-, 1-km- und 100-m-Dateien. Der Importer wählt anschließend automatisch die
100-m-CSV aus.

### Waldshut importieren und Geo-Radar aktualisieren

```bash
python scripts/run_zensus_pipeline.py
```

Danach `http://localhost:3000/geo` neu laden.

Der Standard-Ausschnitt umfasst Waldshut-Tiengen und die unmittelbare Umgebung.
Für einen anderen Ausschnitt kann der Importer z. B. so aufgerufen werden:

```bash
python scripts/import_zensus_waldshut.py --bbox 8.10 47.56 8.38 47.69
python scripts/build_geo_cells.py
PYTHONPATH=. python scripts/load_geo_cells.py
```

### Was aus dem Zensus berechnet wird

Für jede 100-m-Zelle:

- amtliche INSPIRE-Gitter-ID
- Mittelpunkt als WGS84 Latitude/Longitude
- Anzahl Gebäude im Datensatz
- Anteil von Gebäuden mit 3+ Wohnungen (`mfh_share`)
- geschätztes Wohnungsdichte-Gewicht für das **Ranking**

Die geschätzte Zahl `housing_units` ist **kein amtlicher Wohnungsbestand**, sondern
eine aus den Größenklassen abgeleitete Ranking-Größe. Die originalen Zensuswerte
bleiben separat erhalten.

### Datenschutz

Die Zensus-Gitterdaten sind aggregierte Statistikdaten. Das Geo-Radar identifiziert
keine Bewohner, Eigentümer oder konkrete kaufwillige Personen. Personenbezogene
Leads entstehen weiterhin ausschließlich über den freiwilligen SolarLead-Funnel.

## V0.2.2 – LGL Gebäudefit

Nach erfolgreichem Zensus-Import:

```bash
cd backend
source .venv/bin/activate
python scripts/run_lgl_pipeline.py
```

Die Pipeline:

1. entdeckt den freien LGL-WFS-FeatureType für ALKIS-Gebäude,
2. lädt Gebäude im Waldshut-Pilotgebiet als GeoJSON oder GML,
3. ordnet jeden Gebäudegrundriss über seinen Schwerpunkt einer Zensus-100-m-Zelle zu,
4. berechnet Gebäudezahl, gesamte/Ø Grundfläche und Bebauungsgrad,
5. berechnet daraus `building_fit` 0–1,
6. baut den Geo-Gesamtscore neu und lädt ihn in SQLite.

Der Gebäudefit ist **kein personenbezogener Score**. Er bewertet ausschließlich die
bauliche Struktur einer Rasterzelle.

Falls der LGL-WFS geändert wird:

```bash
python scripts/inspect_lgl_wfs.py
```

---

# V0.2.3 – PVGIS Solar Layer

Neue Pipeline:

```bash
cd backend
source .venv/bin/activate
python scripts/run_solar_pipeline.py
```

Sie erzeugt `data/processed/solar_cells.csv`, berechnet den Geo-Score neu und lädt ihn in SQLite.

**Referenz des Geo-Solar-Scores:** 1 kWp kristallines PV, Süd, 90° vertikal, 14 % Verluste. Das ist absichtlich ein standardisierter Gebietsindikator. Der individuelle Funnel nutzt weiterhin die konkrete Balkonausrichtung und Verschattung.

Standardmäßig werden 100-m-Zellen in ca. 1-km-Solar-Samples gruppiert (`SOLAR_SAMPLE_GRID_M=1000`). Das vermeidet Scheingenauigkeit und unnötige PVGIS-API-Last. Ergebnisse werden unter `backend/data/cache/pvgis_solar_cache.json` gecacht und können nach Abbruch fortgesetzt werden.

Optional feiner:

```bash
SOLAR_SAMPLE_GRID_M=500 python scripts/run_solar_pipeline.py
```

Für den Pilot würde ich zunächst 1000 m verwenden.
