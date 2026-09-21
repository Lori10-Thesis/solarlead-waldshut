"""Build SolarLead geo cells from normalized source CSV files.

Expected optional input files in backend/data/processed:
- zensus_cells.csv:  cell_id,latitude,longitude,housing_units,mfh_share
- lgl_cells.csv:     cell_id,building_count,building_fit,...
- solar_cells.csv:   cell_id,solar_score,specific_yield_kwh_kwp,...
- mastr_cells.csv:   cell_id,pv_units,pv_penetration
- campaign_cells.csv: cell_id,conversion_rate

Output: geo_cells.csv
"""
from __future__ import annotations
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed"
OUTPUT = DATA / "geo_cells.csv"


def read_csv(name: str) -> dict[str, dict]:
    path = DATA / name
    if not path.exists(): return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {row["cell_id"]: row for row in csv.DictReader(f)}


def fnum(row: dict | None, key: str, default: float = 0.0) -> float:
    if not row: return default
    try: return float(str(row.get(key, "")).replace(",", "."))
    except (TypeError, ValueError): return default


def clamp(v: float) -> int:
    return max(0, min(100, round(v)))


def main():
    zensus = read_csv("zensus_cells.csv")
    lgl = read_csv("lgl_cells.csv")
    solar = read_csv("solar_cells.csv")
    mastr = read_csv("mastr_cells.csv")
    campaign = read_csv("campaign_cells.csv")

    ids = set(zensus) | set(lgl) | set(solar) | set(mastr) | set(campaign)
    if not ids:
        raise SystemExit("Keine normalisierten Quelldateien gefunden.")

    max_housing = max([fnum(zensus.get(i), "housing_units") for i in ids] + [1])
    max_buildings = max([fnum(lgl.get(i), "building_count") for i in ids] + [1])
    max_conversion = max([fnum(campaign.get(i), "conversion_rate") for i in ids] + [0.01])
    rows = []

    for cell_id in ids:
        z, g, s, m, c = zensus.get(cell_id), lgl.get(cell_id), solar.get(cell_id), mastr.get(cell_id), campaign.get(cell_id)
        lat = fnum(z, "latitude", fnum(g, "latitude", fnum(s, "latitude", 0)))
        lon = fnum(z, "longitude", fnum(g, "longitude", fnum(s, "longitude", 0)))
        if not lat or not lon: continue

        housing_score = clamp(65 * (fnum(z, "housing_units") / max_housing) + 35 * fnum(z, "mfh_share"))
        building_fit_score = clamp(45 * (fnum(g, "building_count") / max_buildings) + 55 * fnum(g, "building_fit", 0.5)) if g else 50
        solar_score = clamp(fnum(s, "solar_score", 50)) if s else 50

        if m:
            pv_penetration = min(1.0, max(0.0, fnum(m, "pv_penetration", 0.2)))
            market_gap_score = clamp((1 - pv_penetration) * 100)
        else:
            market_gap_score = 50

        campaign_score = clamp(100 * fnum(c, "conversion_rate") / max_conversion if c else 50)
        total = clamp(0.30*housing_score + 0.25*building_fit_score + 0.20*solar_score + 0.15*market_gap_score + 0.10*campaign_score)

        rows.append({
            "cell_id":cell_id, "name":f"Raster {cell_id}", "latitude":lat, "longitude":lon,
            "potential_score":total, "housing_density_score":housing_score,
            "building_fit_score":building_fit_score, "solar_score":solar_score,
            "market_gap_score":market_gap_score, "campaign_score":campaign_score,
        })

    rows.sort(key=lambda r:r["potential_score"], reverse=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} Geo-Zellen geschrieben: {OUTPUT}")

if __name__ == "__main__": main()
