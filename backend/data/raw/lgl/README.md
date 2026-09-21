# LGL Gebäude / Hausumringe

V0.2.2 nutzt amtliche Gebäudegeometrien des LGL Baden-Württemberg.

Automatischer Versuch:

```bash
python scripts/download_lgl_buildings.py
```

Danach:

```bash
python scripts/run_lgl_pipeline.py
```

Der Download nutzt standardmäßig den freien INSPIRE-WFS für ALKIS-Gebäude.
Falls sich der LGL-Endpunkt oder FeatureType ändert:

```bash
python scripts/inspect_lgl_wfs.py
```

und bei Bedarf:

```bash
export LGL_WFS_URL="<neue WFS URL>"
export LGL_BUILDING_TYPENAME="<FeatureType>"
```

Alternativ kann eine selbst aus dem LGL-Open-GeoData-Portal heruntergeladene
Gebäudedatei als `buildings.geojson`, `buildings.json`, `buildings.gml` oder
`buildings.xml` in diesen Ordner gelegt werden.
