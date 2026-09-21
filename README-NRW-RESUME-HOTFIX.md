# SolarLead V0.4.1 – NRW WFS Resume Hotfix

Dieser Hotfix behebt Abbrüche wie:

`httpx.RemoteProtocolError: Server disconnected without sending a response`

beim großen Köln-Download über den Geobasis-NRW-WFS.

## Wichtig

Die bereits geladenen Daten werden **nicht gelöscht**.

- fertige Tiles (`.done`) werden übersprungen
- bereits vorhandene `page_000.gml`, `page_001.gml`, ... eines noch nicht fertigen Tiles werden wiederverwendet
- Netzwerkabbrüche werden automatisch bis zu 7-mal erneut versucht
- exponentielles Backoff verhindert sofortiges Hämmern auf den WFS
- neue Seiten werden atomar gespeichert

## Installation

```bash
cd ~/Downloads/solarlead-waldshut

unzip -o ~/Downloads/solarlead-v0.4.1-nrw-resume-hotfix.zip \
  -d ~/Downloads/solarlead-waldshut
```

Dann:

```bash
cd backend
source .venv/bin/activate
```

## Nur den Download fortsetzen

```bash
PYTHONPATH=. python scripts/download_nrw_buildings.py --market koeln
```

Danach die komplette Köln-Pipeline wieder starten:

```bash
PYTHONPATH=. python scripts/run_koeln_geo_pipeline.py
```

Der Downloader erkennt die fertigen Dateien und lädt nicht alles erneut.

Alternativ können nach einem erfolgreichen Download direkt die Folgeprozesse gestartet werden, falls diese Skripte in deiner V0.4.1-Version vorhanden sind:

```bash
PYTHONPATH=. python scripts/process_nrw_buildings.py --market koeln
```

und anschließend die übrigen Geo-/Solar-Schritte über `run_koeln_geo_pipeline.py`.
