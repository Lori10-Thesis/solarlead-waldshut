"""Fetch regional PVGIS reference yield for SolarLead geo cells.

The 100 m Zensus cells are *not* queried one-by-one by default. SolarLead groups
cells into configurable ~1 km LAEA buckets because the underlying solar signal
does not justify 100 m marketing precision and this substantially reduces API
load. Every 100 m cell receives the PVGIS result of its regional sample bucket.

Reference system for the geo score:
- 1.0 kWp crystalline silicon
- fixed, south-facing facade (aspect=0)
- vertical module plane (angle=90°)
- 14 % system losses
- PVGIS horizon enabled (default)

This is a regional solar-resource indicator, not the customer's final yield.
The customer funnel calculates a separate result using the user's orientation,
shading and consumption.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import time
from pathlib import Path

import httpx

BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"
CACHE_DIR = BASE / "data" / "cache"
ZENSUS = PROCESSED / "zensus_cells.csv"
OUTPUT = PROCESSED / "solar_cells.csv"
CACHE_FILE = CACHE_DIR / "pvgis_solar_cache.json"

PVGIS_URL = os.getenv("PVGIS_URL", "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc")
SAMPLE_GRID_M = max(200, int(os.getenv("SOLAR_SAMPLE_GRID_M", "1000")))
REFERENCE_PRICE = float(os.getenv("SOLAR_REFERENCE_PRICE_EUR_KWH", "0.34"))
REFERENCE_SELF_USE = float(os.getenv("SOLAR_REFERENCE_SELF_USE", "0.70"))
REFERENCE_PEAK_KWP = 0.8

CELL_RE = re.compile(r"N(?P<n>\d+)E(?P<e>\d+)$")


def fnum(value, default=0.0):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def cell_xy(cell_id: str):
    m = CELL_RE.search(cell_id)
    if not m:
        return None
    return int(m.group("e")), int(m.group("n"))


def bucket_key(row: dict) -> str:
    xy = cell_xy(row["cell_id"])
    if xy:
        e, n = xy
        return f"E{(e // SAMPLE_GRID_M) * SAMPLE_GRID_M}N{(n // SAMPLE_GRID_M) * SAMPLE_GRID_M}"
    # Fallback if the cell-id schema ever changes.
    lat = fnum(row.get("latitude"))
    lon = fnum(row.get("longitude"))
    return f"LAT{round(lat, 2):.2f}LON{round(lon, 2):.2f}"


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CACHE_FILE)


def query_pvgis(client: httpx.Client, lat: float, lon: float, retries: int = 6) -> float:
    params = {
        "lat": lat,
        "lon": lon,
        "peakpower": 1.0,
        "pvtechchoice": "crystSi",
        "loss": 14,
        "fixed": 1,
        "angle": 90,
        "aspect": 0,
        "outputformat": "json",
    }
    last_error = None
    for attempt in range(retries):
        try:
            r = client.get(PVGIS_URL, params=params)
            if r.status_code == 529 or r.status_code >= 500:
                raise RuntimeError(f"PVGIS HTTP {r.status_code}")
            r.raise_for_status()
            data = r.json()
            return float(data["outputs"]["totals"]["fixed"]["E_y"])
        except Exception as exc:
            last_error = exc
            if attempt == retries - 1:
                break
            delay = min(8.0, 0.8 * (2 ** attempt))
            time.sleep(delay)
    raise RuntimeError(f"PVGIS-Abfrage fehlgeschlagen: {last_error}")


def percentile_ranks(values: list[float]) -> dict[float, float]:
    ordered = sorted(values)
    n = len(ordered)
    if n <= 1:
        return {v: 50.0 for v in ordered}
    ranks = {}
    for i, v in enumerate(ordered):
        ranks[v] = 100.0 * i / (n - 1)
    return ranks


def solar_score(yield_kwh_kwp: float, percentile: float) -> int:
    # Absolute score for a south-facing *vertical* facade reference in Germany.
    # The wide 500-900 kWh/kWp corridor intentionally avoids overstating tiny
    # local differences. 30% regional percentile adds useful topographic signal.
    absolute = max(0.0, min(100.0, (yield_kwh_kwp - 500.0) / 400.0 * 100.0))
    return max(0, min(100, round(0.70 * absolute + 0.30 * percentile)))


def main():
    if not ZENSUS.exists():
        raise SystemExit(f"Fehlt: {ZENSUS}. Zuerst Zensus-Pipeline ausführen.")

    with ZENSUS.open(encoding="utf-8-sig", newline="") as f:
        cells = list(csv.DictReader(f))
    if not cells:
        raise SystemExit("zensus_cells.csv ist leer.")

    buckets: dict[str, list[dict]] = {}
    for row in cells:
        buckets.setdefault(bucket_key(row), []).append(row)

    # Representative coordinate = average cell midpoint within each bucket.
    samples = {}
    for key, rows in buckets.items():
        samples[key] = {
            "latitude": sum(fnum(r.get("latitude")) for r in rows) / len(rows),
            "longitude": sum(fnum(r.get("longitude")) for r in rows) / len(rows),
            "cells": len(rows),
        }

    cache = load_cache()
    print(f"Zensus-Zellen: {len(cells)}")
    print(f"PVGIS-Sampling: {len(samples)} regionale Samples (~{SAMPLE_GRID_M} m Raster)")
    print("Referenz: 1 kWp, Süd, 90° vertikal, 14 % Verluste")

    missing = [k for k in samples if k not in cache or not cache[k].get("specific_yield_kwh_kwp")]
    print(f"Cache-Treffer: {len(samples)-len(missing)}; neu abzufragen: {len(missing)}")

    with httpx.Client(timeout=25.0, headers={"User-Agent":"SolarLead-Waldshut/0.2.3"}) as client:
        for idx, key in enumerate(missing, 1):
            s = samples[key]
            try:
                y = query_pvgis(client, s["latitude"], s["longitude"])
                cache[key] = {
                    "latitude": round(s["latitude"], 6),
                    "longitude": round(s["longitude"], 6),
                    "specific_yield_kwh_kwp": round(y, 2),
                    "version": "PVGIS 5.3",
                    "reference": "south_vertical_1kwp_loss14",
                }
                if idx % 10 == 0 or idx == len(missing):
                    save_cache(cache)
                if idx == 1 or idx % 20 == 0 or idx == len(missing):
                    print(f"  [{idx}/{len(missing)}] {key}: {y:.1f} kWh/kWp")
                # Gentle pacing. PVGIS can return 529 when overloaded.
                time.sleep(0.12)
            except Exception as exc:
                print(f"  WARN {key}: {exc}")

    save_cache(cache)
    valid_yields = [float(cache[k]["specific_yield_kwh_kwp"]) for k in samples if k in cache and cache[k].get("specific_yield_kwh_kwp")]
    if not valid_yields:
        raise SystemExit("Keine PVGIS-Ergebnisse verfügbar. Pipeline nicht fortgesetzt.")

    ranks = percentile_ranks(valid_yields)
    rows_out = []
    misses = 0
    for cell in cells:
        key = bucket_key(cell)
        item = cache.get(key)
        if not item or not item.get("specific_yield_kwh_kwp"):
            misses += 1
            continue
        y = float(item["specific_yield_kwh_kwp"])
        score = solar_score(y, ranks.get(y, 50.0))
        yield_800 = y * REFERENCE_PEAK_KWP
        # Indicative energy-value proxy, not a guaranteed household saving.
        value = yield_800 * REFERENCE_SELF_USE * REFERENCE_PRICE
        rows_out.append({
            "cell_id": cell["cell_id"],
            "latitude": cell.get("latitude", ""),
            "longitude": cell.get("longitude", ""),
            "solar_score": score,
            "specific_yield_kwh_kwp": round(y, 1),
            "reference_yield_800w_kwh": round(yield_800, 1),
            "reference_energy_value_eur": round(value, 2),
            "sample_bucket": key,
            "sample_grid_m": SAMPLE_GRID_M,
            "pvgis_version": item.get("version", "PVGIS 5.3"),
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows_out[0].keys())
        writer.writeheader()
        writer.writerows(rows_out)

    ys = [r["specific_yield_kwh_kwp"] for r in rows_out]
    print(f"Fertig: {len(rows_out)} Solar-Zellen -> {OUTPUT}")
    print(f"Nicht zugeordnet: {misses}")
    print(f"PVGIS Referenzertrag: min={min(ys):.1f}, mittel={sum(ys)/len(ys):.1f}, max={max(ys):.1f} kWh/kWp")
    top = sorted(rows_out, key=lambda r: r["solar_score"], reverse=True)[:5]
    print("Top 5 Solar Score:")
    for r in top:
        print(f"  {r['cell_id']}: score={r['solar_score']}, 800W≈{r['reference_yield_800w_kwh']} kWh/Jahr")


if __name__ == "__main__":
    main()
