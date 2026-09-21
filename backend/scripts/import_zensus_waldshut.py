"""Convert official Destatis Zensus 2022 100m-grid data to SolarLead cells.

Input dataset:
  Gebäude mit Wohnraum nach Anzahl der Wohnungen im Gebäude

Output:
  backend/data/processed/zensus_cells.csv

The importer is deliberately tolerant of small column-name changes. It supports
both a long format (one category per row) and a wide format (categories as
columns), provided the official INSPIRE grid id is present.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from pyproj import Transformer

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "zensus" / "gebaeude_wohnungen"
OUTPUT = BASE / "data" / "processed" / "zensus_cells.csv"

# Pilotgebiet: Waldshut-Tiengen + direkte Nachbarorte. Can be overridden by CLI.
DEFAULT_BBOX = (8.10, 47.56, 8.38, 47.69)  # min_lon, min_lat, max_lon, max_lat

GRID_RE = re.compile(r"(?:CRS3035RES)?100mN(?P<n>\d+)E(?P<e>\d+)", re.I)
TO_WGS84 = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)

NULL_TOKENS = {"", "-", ".", "..", "...", "/", "x", "X", "NA", "N/A"}


def norm(s: str | None) -> str:
    s = (s or "").strip().lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def number(v: str | None) -> float:
    if v is None:
        return 0.0
    raw = str(v).strip()
    if raw in NULL_TOKENS:
        return 0.0
    raw = raw.replace(".", "").replace(",", ".") if "," in raw else raw
    try:
        return float(raw)
    except ValueError:
        return 0.0


def sniff(path: Path) -> tuple[str, str]:
    sample = path.read_bytes()[:65536]
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            txt = sample.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        txt = sample.decode("latin1")
        enc = "latin1"
    try:
        dialect = csv.Sniffer().sniff(txt, delimiters=";,\t|")
        delim = dialect.delimiter
    except csv.Error:
        delim = ";"
    return enc, delim


def choose_100m_csv(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.exists():
            raise SystemExit(f"CSV nicht gefunden: {p}")
        return p
    candidates = list(RAW.rglob("*.csv"))
    ranked = sorted(candidates, key=lambda p: ("100m" not in p.name.lower(), len(p.name)))
    for p in ranked:
        enc, delim = sniff(p)
        with p.open(encoding=enc, newline="", errors="replace") as f:
            reader = csv.reader(f, delimiter=delim)
            header = next(reader, [])
        if any("gitter_id_100m" in norm(h) or ("gitter" in norm(h) and "100m" in norm(h)) for h in header):
            return p
    raise SystemExit(
        "Keine 100m-Zensus-CSV gefunden. Zuerst `python scripts/download_zensus.py` ausführen."
    )


def grid_center(grid_id: str) -> tuple[float, float] | None:
    """Return WGS84 center for an INSPIRE 100 m grid id.

    Destatis/INSPIRE files encountered in the wild use two equivalent numeric
    encodings after N/E:

    - compact cell indices, e.g. ``100mN27249E41869``
      -> multiply by 100 to obtain the lower-left EPSG:3035 coordinate
    - metre coordinates, e.g. ``100mN2724900E4186900``
      -> values are already EPSG:3035 metres

    Supporting both makes the importer robust across Zensus grid exports.
    """
    raw = str(grid_id).strip()
    m = GRID_RE.search(raw.replace("_", "")) or GRID_RE.search(raw)
    if not m:
        return None

    n_raw = int(m.group("n"))
    e_raw = int(m.group("e"))

    # Compact 100-m cell indices are typically 5 digits in Germany; full
    # EPSG:3035 metre coordinates are around 2-5 million (7 digits).
    if n_raw < 100_000 and e_raw < 100_000:
        northing = n_raw * 100
        easting = e_raw * 100
    else:
        northing = n_raw
        easting = e_raw

    # Grid id denotes the lower-left corner; add 50 m to get cell center.
    lon, lat = TO_WGS84.transform(easting + 50, northing + 50)

    # Reject impossible transforms instead of silently producing nonsense.
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return None
    return lat, lon


def in_bbox(lat: float, lon: float, bbox: tuple[float,float,float,float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def category_bucket(text: str) -> tuple[str | None, float]:
    """Return (bucket, estimated apartments per building).

    Bucket `mfh` means >=3 apartments and is the main balcony-PV structural signal.
    The weighted apartment value is only an estimate for ranking density, not an
    official count of dwellings.
    """
    t = norm(text)
    # Explicit categories first.
    if any(x in t for x in ("13_und_mehr", "13_mehr", "13plus", "13_plus")):
        return "mfh", 15.0
    if any(x in t for x in ("7_12", "7_bis_12", "7bis12")):
        return "mfh", 9.0
    if any(x in t for x in ("3_6", "3_bis_6", "3bis6", "3_9", "3_bis_9")):
        return "mfh", 4.5
    if re.search(r"(^|_)2(_|$)", t) and "wohnung" in t:
        return "two", 2.0
    if re.search(r"(^|_)1(_|$)", t) and "wohnung" in t:
        return "one", 1.0
    # Short-code fallbacks sometimes used in machine-readable tables.
    if t in {"1", "1w", "1we", "eine", "eine_wohnung"}:
        return "one", 1.0
    if t in {"2", "2w", "2we", "zwei", "zwei_wohnungen"}:
        return "two", 2.0
    if t in {"3_6", "7_12", "13_u_m", "13_und_mehr", "3_und_mehr"}:
        return "mfh", 6.0
    return None, 0.0


def header_key(fieldnames: list[str], candidates: Iterable[str]) -> str | None:
    lookup = {norm(f): f for f in fieldnames}
    for c in candidates:
        nc = norm(c)
        if nc in lookup:
            return lookup[nc]
    for nf, original in lookup.items():
        if any(norm(c) in nf for c in candidates):
            return original
    return None


def parse(path: Path, bbox: tuple[float,float,float,float]):
    enc, delim = sniff(path)
    aggregates: dict[str, dict] = defaultdict(lambda: {
        "one": 0.0, "two": 0.0, "mfh": 0.0, "weighted_units": 0.0,
        "total_buildings": 0.0, "lat": 0.0, "lon": 0.0,
    })

    with path.open(encoding=enc, newline="", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delim)
        fields = reader.fieldnames or []
        grid_col = header_key(fields, ["Gitter_ID_100m", "GitterID_100m", "grid_id_100m"])
        if not grid_col:
            raise SystemExit(f"Gitter_ID_100m nicht gefunden. Spalten: {fields}")

        count_col = header_key(fields, ["Anzahl_Gebaeude", "Anzahl Gebäude", "Anzahl"])
        cat_col = header_key(fields, [
            "Anzahl_Wohnungen_im_Gebaeude", "Anzahl Wohnungen im Gebäude",
            "Ausprägung", "Auspraegung", "Merkmalsauspraegung", "Kategorie"
        ])

        # Wide-format category columns.
        wide_cols: list[tuple[str,str,float]] = []
        for col in fields:
            bucket, weight = category_bucket(col)
            if bucket:
                wide_cols.append((col,bucket,weight))

        seen_geo: dict[str, tuple[float,float] | None] = {}
        matched_rows = 0
        for row in reader:
            gid = str(row.get(grid_col, "")).strip()
            if not gid:
                continue
            if gid not in seen_geo:
                seen_geo[gid] = grid_center(gid)
            coords = seen_geo[gid]
            if not coords:
                continue
            lat, lon = coords
            if not in_bbox(lat, lon, bbox):
                continue
            a = aggregates[gid]
            a["lat"], a["lon"] = lat, lon

            if wide_cols:
                for col, bucket, weight in wide_cols:
                    cnt = number(row.get(col))
                    if cnt <= 0:
                        continue
                    a[bucket] += cnt
                    a["weighted_units"] += cnt * weight
                    a["total_buildings"] += cnt
                matched_rows += 1
                continue

            if cat_col and count_col:
                label = row.get(cat_col, "")
                bucket, weight = category_bucket(label)
                cnt = number(row.get(count_col))
                if bucket and cnt > 0:
                    a[bucket] += cnt
                    a["weighted_units"] += cnt * weight
                    a["total_buildings"] += cnt
                    matched_rows += 1
            elif count_col:
                # Some files may expose only totals; still retain density, but MFH share is unknown.
                cnt = number(row.get(count_col))
                if cnt > 0:
                    a["total_buildings"] = max(a["total_buildings"], cnt)
                    a["weighted_units"] = max(a["weighted_units"], cnt)
                    matched_rows += 1

    if not aggregates:
        # Helpful diagnostics: show how the first parseable grid ids transform.
        print("\nDiagnose: erste interpretierbare Gitter-IDs:")
        shown = 0
        with path.open(encoding=enc, newline="", errors="replace") as df:
            dr = csv.DictReader(df, delimiter=delim)
            for drow in dr:
                gid = str(drow.get(grid_col, "")).strip()
                coords = grid_center(gid) if gid else None
                if coords:
                    print(f" - {gid} -> lat={coords[0]:.6f}, lon={coords[1]:.6f}")
                    shown += 1
                if shown >= 5:
                    break
        raise SystemExit("Im gewählten Waldshut-Bounding-Box wurden keine Zellen gefunden.")
    return aggregates, matched_rows, fields


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="Pfad direkt zur offiziellen 100m CSV")
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("MIN_LON","MIN_LAT","MAX_LON","MAX_LAT"), default=DEFAULT_BBOX)
    args = ap.parse_args()

    path = choose_100m_csv(args.csv)
    bbox = tuple(args.bbox)
    print(f"Verarbeite: {path}")
    print(f"Pilot-BBOX: {bbox}")
    aggs, matched, fields = parse(path, bbox)

    rows = []
    for gid, a in aggs.items():
        total = a["total_buildings"]
        if total <= 0:
            continue
        mfh_share = min(1.0, max(0.0, a["mfh"] / total)) if a["mfh"] else 0.0
        housing_units = max(total, a["weighted_units"])
        rows.append({
            "cell_id": gid,
            "latitude": f'{a["lat"]:.7f}',
            "longitude": f'{a["lon"]:.7f}',
            "housing_units": f'{housing_units:.2f}',
            "mfh_share": f'{mfh_share:.4f}',
            "building_count_zensus": f'{total:.0f}',
            "mfh_buildings_zensus": f'{a["mfh"]:.0f}',
            "source": "Zensus 2022 / Destatis",
        })

    rows.sort(key=lambda r: float(r["housing_units"]), reverse=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Fertig: {len(rows)} Waldshut-Zellen -> {OUTPUT}")
    print(f"Verwertete Kategoriezeilen: {matched}")
    if rows:
        top = rows[:5]
        print("Top 5 nach geschätzter Wohnungsdichte:")
        for r in top:
            print(f'  {r["cell_id"]}: units≈{r["housing_units"]}, MFH={float(r["mfh_share"])*100:.0f}%')
    if rows and all(float(r["mfh_share"]) == 0 for r in rows):
        print("WARNUNG: Keine MFH-Kategorien erkannt. Bitte `python scripts/inspect_zensus_csv.py` ausführen und Ausgabe prüfen.")


if __name__ == "__main__":
    main()
