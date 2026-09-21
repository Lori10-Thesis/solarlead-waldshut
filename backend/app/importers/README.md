# V0.2 Geo-Datenpipeline

Das Geo-Radar soll **Gebiete** bewerten, nicht Privatpersonen identifizieren.

## Offizielle Quellen

1. **Zensus 2022** – 100-m-Raster als Open Data. Daraus nutzen wir z. B. Wohnungsdichte und Gebäudestruktur.
2. **LGL Baden-Württemberg OpenGeoData** – amtliche Hausumringe / Gebäudekoordinaten. Die Hausumringe enthalten keine Bewohner- oder Eigentümerdaten.
3. **Marktstammdatenregister (MaStR)** – öffentliche PV-Daten zur aggregierten Marktdurchdringung.
4. **PVGIS** – standortbezogene Solar-/PV-Ertragsschätzung.

## Warum Adapter statt hart codierter Download-Links?

Die amtlichen Dateinamen, Exportstände und Schemas ändern sich. SolarLead trennt daher:

```text
amtliche Rohdaten
      ↓
Source Adapter
      ↓
normalisierte CSVs
      ↓
build_geo_cells.py
      ↓
geo_cells.csv
      ↓
load_geo_cells.py
      ↓
WebApp Geo-Radar
```

## Normalisierte Dateien

Lege sie unter `backend/data/processed/` ab.

### zensus_cells.csv

```csv
cell_id,latitude,longitude,housing_units,mfh_share,solar_score
WT_001,47.6237,8.2172,180,0.72,0.89
```

- `mfh_share`: 0–1
- `solar_score`: 0–1; kann zunächst über PVGIS/Regionalscore erzeugt werden

### lgl_cells.csv

```csv
cell_id,latitude,longitude,building_count,building_fit
WT_001,47.6237,8.2172,34,0.82
```

### mastr_cells.csv

```csv
cell_id,pv_units,pv_penetration
WT_001,18,0.22
```

`pv_penetration` ist ein **aggregierter** Marktindikator 0–1. Keine Zuordnung zu einzelnen Haushalten.

### campaign_cells.csv

Optional; aus deinem eigenen Marketing:

```csv
cell_id,conversion_rate
WT_001,0.071
```

## Score V0.2

```text
30 % Wohnungs-/MFH-Dichte
25 % Gebäudeeignung
20 % solares Potenzial
15 % Marktlücke (niedrige PV-Durchdringung)
10 % eigene Kampagnenperformance
```

## Build & Import

Vom `backend`-Ordner:

```bash
python scripts/build_geo_cells.py
PYTHONPATH=. python scripts/load_geo_cells.py
```

Danach Backend neu laden und `/geo` öffnen.

## Nächster Adapter-Schritt

Wir bauen die konkreten Source-Adapter jeweils anhand des tatsächlich von dir heruntergeladenen Zensus-/LGL-/MaStR-Exports. Das verhindert, dass wir Spaltennamen raten und später falsche Scores berechnen.

## LGL V0.2.2

Automatischer Download + Import:

```bash
python scripts/run_lgl_pipeline.py
```

Normalisiertes Ergebnis `data/processed/lgl_cells.csv`:

```text
cell_id,latitude,longitude,building_count,total_footprint_m2,avg_footprint_m2,coverage_ratio,building_fit,source
```

MVP-Zuordnung: Gebäude-Schwerpunkt -> 100-m-Zensuszelle. Eine spätere PostGIS-
Version kann exakte Polygonüberschneidungen verwenden.
