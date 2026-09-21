"""Download ALKIS/INSPIRE building features for the Waldshut pilot area.

Primary source: LGL Baden-Württemberg Open Data WFS.
The service URL can be overridden with LGL_WFS_URL.

The script discovers the building FeatureType from GetCapabilities and prefers
GeoJSON output. If the WFS does not advertise JSON, it stores GML instead; the
matching importer understands both formats.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from pyproj import Transformer

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "lgl"
RAW.mkdir(parents=True, exist_ok=True)

WFS_URL = os.getenv(
    "LGL_WFS_URL",
    "https://owsproxy.lgl-bw.de/owsproxy/wfs/WFS_INSP_BW_Gebaeude_ALKIS",
)
BBOX = (8.10, 47.56, 8.38, 47.69)  # min_lon,min_lat,max_lon,max_lat
USER_AGENT = os.getenv("USER_AGENT", "SolarLead-Waldshut-Dev/0.2.2 contact@example.com")
TO_25832 = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)


def fetch(params: dict[str, str | int], timeout: int = 120) -> tuple[bytes, str]:
    url = WFS_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def local(el) -> str:
    return el.tag.rsplit("}", 1)[-1]


def capabilities() -> tuple[list[str], list[str]]:
    body, _ = fetch({"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"})
    root = ET.fromstring(body)
    names: list[str] = []
    formats: list[str] = []

    for ft in root.iter():
        if local(ft) == "FeatureType":
            for child in ft:
                if local(child) == "Name" and child.text:
                    names.append(child.text.strip())
                    break
    for el in root.iter():
        if local(el) in {"Value", "DefaultValue"} and el.text:
            t = el.text.strip()
            if "json" in t.lower() or "gml" in t.lower() or "xml" in t.lower():
                formats.append(t)
    return list(dict.fromkeys(names)), list(dict.fromkeys(formats))


def choose_type(names: list[str]) -> str:
    explicit = os.getenv("LGL_BUILDING_TYPENAME")
    if explicit:
        return explicit
    for name in names:
        n = name.lower()
        if "building" in n or "gebaeude" in n or "gebäude" in n:
            return name
    raise SystemExit(
        "Kein Gebäude-FeatureType automatisch erkannt.\n"
        "Verfügbare Typen:\n - " + "\n - ".join(names[:100]) +
        "\nSetze bei Bedarf LGL_BUILDING_TYPENAME=<Name>."
    )


def looks_like_json(body: bytes, content_type: str) -> bool:
    s = body.lstrip()[:1]
    return s in {b"{", b"["} or "json" in content_type.lower()


def bbox_strategies():
    min_lon,min_lat,max_lon,max_lat=BBOX
    min_e,min_n=TO_25832.transform(min_lon,min_lat)
    max_e,max_n=TO_25832.transform(max_lon,max_lat)
    return [
        ("CRS84", f"{min_lon},{min_lat},{max_lon},{max_lat},urn:ogc:def:crs:OGC:1.3:CRS84"),
        ("EPSG25832", f"{min_e:.2f},{min_n:.2f},{max_e:.2f},{max_n:.2f},urn:ogc:def:crs:EPSG::25832"),
        ("EPSG4326-axis", f"{min_lat},{min_lon},{max_lat},{max_lon},urn:ogc:def:crs:EPSG::4326"),
    ]


def download_json(type_name: str) -> bool:
    out = RAW / "buildings.geojson"
    page_size = 5000

    for bbox_label,bbox_value in bbox_strategies():
      for output_format in ("application/json", "json"):
        all_features: list[dict] = []
        start = 0
        try:
            while True:
                params = {
                    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
                    "typeNames": type_name,
                    "srsName": "urn:ogc:def:crs:OGC:1.3:CRS84",
                    "bbox": bbox_value,
                    "count": page_size, "startIndex": start,
                    "outputFormat": output_format,
                }
                body, ct = fetch(params)
                if not looks_like_json(body, ct):
                    break
                payload = json.loads(body)
                features = payload.get("features", []) if isinstance(payload, dict) else []
                all_features.extend(features)
                print(f"  {bbox_label} / Seite ab {start}: {len(features)} Gebäude")
                if len(features) < page_size:
                    if not all_features:
                        break
                    out.write_text(json.dumps({"type": "FeatureCollection", "features": all_features}), encoding="utf-8")
                    print(f"LGL Gebäude gespeichert: {out} ({len(all_features)} Features)")
                    return True
                start += len(features)
                if start > 200_000:
                    raise RuntimeError("Sicherheitslimit überschritten")
        except Exception as e:
            print(f"  JSON {bbox_label}/{output_format!r} nicht nutzbar: {e}")
    return False

def download_gml(type_name: str) -> Path:
    out = RAW / "buildings.gml"
    last_error = ""
    for bbox_label,bbox_value in bbox_strategies():
        params = {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeNames": type_name,
            "srsName": "urn:ogc:def:crs:OGC:1.3:CRS84",
            "bbox": bbox_value,
            "count": 50000,
        }
        try:
            body, _ = fetch(params, timeout=240)
            text = body[:1500].decode("utf-8", errors="ignore")
            if "Exception" in text or "ServiceException" in text:
                last_error=text
                continue
            # A valid but empty response is not useful; try next bbox convention.
            if b"posList" not in body and b"<gml:pos" not in body:
                last_error=f"{bbox_label}: keine Geometrien im GML"
                continue
            out.write_bytes(body)
            print(f"LGL GML gespeichert: {out} ({len(body)/1024/1024:.1f} MB; {bbox_label})")
            return out
        except Exception as e:
            last_error=f"{bbox_label}: {e}"
    raise SystemExit("WFS-GML-Download fehlgeschlagen. Letzte Diagnose:\n" + last_error)

def main():
    print("Prüfe LGL WFS …")
    print("Endpoint:", WFS_URL)
    names, formats = capabilities()
    type_name = choose_type(names)
    print("Gebäude-FeatureType:", type_name)
    if formats:
        print("Gemeldete Formate:", ", ".join(formats[:12]))

    if download_json(type_name):
        return
    print("GeoJSON nicht verfügbar – falle auf GML zurück.")
    download_gml(type_name)


if __name__ == "__main__":
    main()
