# Zensus 2022 Rohdaten

SolarLead V0.2 nutzt zunächst den amtlichen Datensatz:

**Gebäude mit Wohnraum nach Anzahl der Wohnungen im Gebäude**

Direkter offizieller Destatis-Download:
`https://www.destatis.de/static/DE/zensus/gitterdaten/Gebaeude_nach_Anzahl_der_Wohnungen_im_Gebaeude.zip`

Automatisch laden:

```bash
python scripts/download_zensus.py
```

Danach:

```bash
python scripts/run_zensus_pipeline.py
```

Die Originaldaten bleiben unverändert in diesem Ordner. Das erzeugte
`data/processed/zensus_cells.csv` enthält nur die auf das Pilotgebiet gefilterten
100-m-Zellen und daraus abgeleitete Ranking-Merkmale.

Quellenhinweis für spätere öffentliche Darstellungen:
`© Statistische Ämter des Bundes und der Länder 2025, bearbeitet durch SolarLead`

Vor einem öffentlichen Release bitte den jeweils im ZIP enthaltenen Lizenz- und
Quellenhinweis noch einmal gegen die aktuelle Destatis-Dokumentation prüfen.
