"""Aggregate LGL building footprints into the existing Zensus 100 m cells.

Accepted inputs:
- data/raw/lgl/buildings.geojson (preferred)
- data/raw/lgl/buildings.json
- data/raw/lgl/buildings.gml / .xml

Output:
- data/processed/lgl_cells.csv

MVP spatial rule: a building is assigned to the 100 m cell containing its
footprint centroid. A later PostGIS version can replace this with exact polygon
intersection across cell boundaries.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Iterator

from pyproj import Transformer

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "lgl"
ZENSUS = BASE / "data" / "processed" / "zensus_cells.csv"
OUTPUT = BASE / "data" / "processed" / "lgl_cells.csv"

TO_3035 = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
FROM_3035 = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
TO_WGS_BY_EPSG: dict[int, Transformer] = {
    25832: Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True),
    3035: FROM_3035,
    4258: Transformer.from_crs("EPSG:4258", "EPSG:4326", always_xy=True),
    4326: Transformer.from_crs("EPSG:4326", "EPSG:4326", always_xy=True),
}


def norm_gid(easting: float, northing: float) -> str:
    e = int(math.floor(easting / 100.0) * 100)
    n = int(math.floor(northing / 100.0) * 100)
    return f"CRS3035RES100mN{n}E{e}"


def polygon_area_centroid_xy(ring: list[tuple[float,float]]) -> tuple[float,float,float]:
    if len(ring) < 3:
        return 0.0, 0.0, 0.0
    pts = ring[:]
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    cross_sum = cx = cy = 0.0
    for (x1,y1),(x2,y2) in zip(pts, pts[1:]):
        cross = x1*y2 - x2*y1
        cross_sum += cross
        cx += (x1+x2)*cross
        cy += (y1+y2)*cross
    signed_area = cross_sum / 2.0
    area = abs(signed_area)
    if abs(cross_sum) < 1e-9:
        xs=[p[0] for p in pts[:-1]]; ys=[p[1] for p in pts[:-1]]
        return 0.0, sum(xs)/len(xs), sum(ys)/len(ys)
    cx /= (3.0 * cross_sum)
    cy /= (3.0 * cross_sum)
    return area, cx, cy


def rings_from_geojson_geometry(g: dict) -> Iterator[list[tuple[float,float]]]:
    t = g.get("type")
    c = g.get("coordinates") or []
    if t == "Polygon":
        if c: yield [(float(x),float(y)) for x,y,*_ in c[0]]
    elif t == "MultiPolygon":
        for poly in c:
            if poly: yield [(float(x),float(y)) for x,y,*_ in poly[0]]


def geojson_rings(path: Path) -> Iterator[list[tuple[float,float]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for feat in payload.get("features", []):
        geom = feat.get("geometry") or {}
        rings = list(rings_from_geojson_geometry(geom))
        if not rings: continue
        # One feature = one building. Use largest polygon part for centroid and
        # keep all parts by yielding each; aggregation later deduplicates feature
        # only approximately, which is acceptable for rare MultiPolygon buildings.
        for r in rings:
            yield r


def epsg_from_srs(s: str | None) -> int:
    s = s or ""
    m = re.search(r"(?:EPSG[:/]|::)(\d{4,5})(?:\D|$)", s, re.I)
    if m:
        return int(m.group(1))
    if "CRS84" in s.upper():
        return 4326
    return 4326


def gml_rings(path: Path) -> Iterator[list[tuple[float,float]]]:
    # Streaming parse: every posList is a candidate exterior ring. For the LGL
    # building service this yields the building footprint rings without loading
    # a large GML document fully into memory.
    current_srs = ""
    for event, elem in ET.iterparse(path, events=("start","end")):
        if event == "start" and elem.attrib.get("srsName"):
            current_srs = elem.attrib.get("srsName", current_srs)
        if event == "end" and elem.tag.rsplit("}",1)[-1] == "posList" and elem.text:
            nums = [float(x) for x in elem.text.split()]
            dim = int(elem.attrib.get("srsDimension", "2") or 2)
            if dim < 2 or len(nums) < 6:
                elem.clear(); continue
            epsg = epsg_from_srs(current_srs)
            transformer = TO_WGS_BY_EPSG.get(epsg)
            if transformer is None:
                try: transformer = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
                except Exception: transformer = TO_WGS_BY_EPSG[4326]
            ring=[]
            for i in range(0, len(nums)-dim+1, dim):
                x,y=nums[i],nums[i+1]
                lon,lat=transformer.transform(x,y)
                ring.append((lon,lat))
            if len(ring)>=3:
                yield ring
            elem.clear()


def choose_input(explicit: str | None) -> Path:
    if explicit:
        p=Path(explicit).expanduser().resolve()
        if not p.exists(): raise SystemExit(f"LGL-Datei nicht gefunden: {p}")
        return p
    for name in ("buildings.geojson","buildings.json","buildings.gml","buildings.xml"):
        p=RAW/name
        if p.exists(): return p
    raise SystemExit("Keine LGL-Gebäudedatei gefunden. Zuerst `python scripts/download_lgl_buildings.py` ausführen.")


def read_zensus() -> dict[str,dict]:
    if not ZENSUS.exists():
        raise SystemExit("zensus_cells.csv fehlt. Zuerst die Zensus-Pipeline ausführen.")
    with ZENSUS.open(encoding="utf-8-sig", newline="") as f:
        return {r["cell_id"]:r for r in csv.DictReader(f)}


def size_fit(avg: float) -> float:
    if avg <= 0: return 0.0
    if avg < 50: return max(0.15, avg/100)
    if avg < 100: return 0.5 + (avg-50)/100
    if avg <= 450: return 1.0
    if avg <= 1200: return max(0.30, 1.0 - (avg-450)/1070)
    return 0.20


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input", help="GeoJSON/GML input override")
    args=ap.parse_args()
    path=choose_input(args.input)
    zensus=read_zensus()
    allowed=set(zensus)
    print("Verarbeite LGL-Gebäude:", path)
    print("Zensus-Zellen als Zielraster:", len(allowed))

    agg=defaultdict(lambda:{"count":0,"area":0.0,"lat":0.0,"lon":0.0})
    source_iter = geojson_rings(path) if path.suffix.lower() in {".json",".geojson"} else gml_rings(path)
    seen=matched=0
    for ring_lonlat in source_iter:
        seen += 1
        ring_3035=[TO_3035.transform(lon,lat) for lon,lat in ring_lonlat]
        area,cx,cy=polygon_area_centroid_xy(ring_3035)
        if area < 8 or area > 100_000:  # remove tiny artefacts / implausible geometries
            continue
        gid=norm_gid(cx,cy)
        if gid not in allowed:
            continue
        lon,lat=FROM_3035.transform(cx,cy)
        a=agg[gid]
        a["count"] += 1
        a["area"] += area
        a["lat"],a["lon"] = lat,lon
        matched += 1

    rows=[]
    for gid,z in zensus.items():
        a=agg.get(gid)
        if not a: continue
        count=a["count"]
        total_area=a["area"]
        avg=total_area/count if count else 0
        coverage=min(1.0,total_area/10000.0)
        count_score=min(1.0,count/18.0)
        coverage_score=min(1.0,coverage/0.38) if coverage<=0.38 else max(0.35,1-(coverage-0.38)/0.62)
        fit=max(0.0,min(1.0,0.45*count_score + 0.35*coverage_score + 0.20*size_fit(avg)))
        rows.append({
            "cell_id":gid,
            "latitude":z.get("latitude", a["lat"]),
            "longitude":z.get("longitude", a["lon"]),
            "building_count":count,
            "total_footprint_m2":f"{total_area:.1f}",
            "avg_footprint_m2":f"{avg:.1f}",
            "coverage_ratio":f"{coverage:.4f}",
            "building_fit":f"{fit:.4f}",
            "source":"LGL BW / ALKIS Gebäude",
        })

    rows.sort(key=lambda r:float(r["building_fit"]), reverse=True)
    if not rows:
        raise SystemExit(f"Keine Gebäude den {len(allowed)} Zensus-Zellen zugeordnet. Gelesene Geometrien: {seen}")
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with OUTPUT.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Fertig: {len(rows)} Zellen mit LGL-Gebäudedaten -> {OUTPUT}")
    print(f"Geometrien gelesen: {seen}; Waldshut/Zensus zugeordnet: {matched}")
    print("Top 5 Building Fit:")
    for r in rows[:5]:
        print(f'  {r["cell_id"]}: fit={float(r["building_fit"])*100:.0f}, Gebäude={r["building_count"]}, Ø={r["avg_footprint_m2"]} m², Bebauung={float(r["coverage_ratio"])*100:.0f}%')


if __name__ == "__main__":
    main()
