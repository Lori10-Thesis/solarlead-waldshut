# SolarLead V0.4.1 — Köln Geo Engine

V0.4.1 macht Köln zum zweiten echten Geo-Markt der Plattform.

## Neu

- generischer Zensus-Importer pro Market
- Geobasis-NRW-WFS-Downloader mit Kacheln, Pagination, Resume und Fortschritt
- NRW-Gebäudeaggregation auf 100-m-Zensuszellen
- marktbezogener PVGIS-Layer mit Cache
- marktbezogener Geo-Builder
- vergleichbareres `geo_v2_cross_market`-Scoring
- One-Command Köln Pipeline
- Rebuild-Skript, um Waldshut mit demselben Score neu zu rechnen

## Köln Pipeline

Im `backend`-Ordner:

```bash
source .venv/bin/activate
PYTHONPATH=. python scripts/run_koeln_geo_pipeline.py
```

Der bereits heruntergeladene bundesweite Zensus-Datensatz wird wiederverwendet.
Die NRW-Gebäude werden aus dem vereinfachten ALKIS-WFS (`ave:GebaeudeBauwerk`)
gekachelt für den in `markets` konfigurierten Köln-Bounding-Box geladen.

Die Pipeline schreibt ausschließlich Köln-Dateien unter:

```text
data/processed/koeln/
  zensus_cells.csv
  buildings_cells.csv
  solar_cells.csv
  geo_cells.csv
```

Waldshut-Daten werden nicht überschrieben.

## Marktübergreifendes Scoring

Nach dem Köln-Import sollte einmal ausgeführt werden:

```bash
PYTHONPATH=. python scripts/rebuild_geo_v2.py
```

Dadurch werden alle Märkte mit vorhandenen Roh-/Processed-Quellen nach derselben
absoluten Score-Logik berechnet. Für Waldshut werden bestehende Legacy-Dateien
nur in einen regionalen Ordner kopiert; sie werden nicht neu heruntergeladen.

## Datenreife

Nach V0.4.1:

- Waldshut: Zensus + LGL + optional PVGIS
- Köln: Zensus + Geobasis NRW + PVGIS
- MaStR: noch neutral / nächste Datenebene
- Campaign Score: neutral bis reale First-Party-Conversions vorhanden sind

Hinweis: Die Market-BBOX ist aktuell der technische Pilot-Ausschnitt. Ein späterer
Schritt ersetzt den BBOX-Clip durch amtliche Gemeinde-/Marktpolygone.
