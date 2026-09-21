"""Robust/resumable download of simplified ALKIS building footprints from Geobasis NRW WFS.

Improvements over V0.4.1:
- retries transient WFS/network failures with exponential backoff
- disables HTTP keep-alive for this large WFS transfer (more robust against stale server connections)
- resumes finished tiles via `.done`
- resumes *within* an unfinished tile by reusing already downloaded `page_XXX.gml`
- writes new pages atomically (`.part` -> `.gml`)
- prints retry/resume progress

Usage:
    PYTHONPATH=. python scripts/download_nrw_buildings.py --market koeln

After completion continue with:
    PYTHONPATH=. python scripts/process_nrw_buildings.py --market koeln
    PYTHONPATH=. python scripts/run_solar_market.py --market koeln
    PYTHONPATH=. python scripts/build_geo_market.py --market koeln
    PYTHONPATH=. python scripts/load_geo_market.py --market koeln
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
from pyproj import Transformer

from app.db import SessionLocal
from app.models import Market
from app.geo_providers.registry import get_building_provider

BASE = Path(__file__).resolve().parents[1]
TO_25832 = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
FEATURE_TYPE = "ave:GebaeudeBauwerk"
PAGE_SIZE = 10000

RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504, 529}


def get_market(code: str):
    db = SessionLocal()
    try:
        m = (
            db.query(Market)
            .filter(Market.code == code, Market.active == True)  # noqa: E712
            .first()
        )
        if not m:
            raise SystemExit(f"Market '{code}' nicht gefunden.")
        return {
            "code": m.code,
            "name": m.name,
            "provider": m.building_provider,
            "bbox": (m.bbox_west, m.bbox_south, m.bbox_east, m.bbox_north),
        }
    finally:
        db.close()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def response_counts(content: bytes) -> tuple[int | None, int | None]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise RuntimeError(f"Ungültige/unvollständige GML-Antwort: {exc}") from exc

    if local_name(root.tag) == "ExceptionReport":
        text = " ".join((e.text or "") for e in root.iter()).strip()
        raise RuntimeError(f"WFS ExceptionReport: {text[:500]}")

    def n(name):
        v = root.attrib.get(name)
        if v is None or str(v).lower() == "unknown":
            return None
        try:
            return int(v)
        except ValueError:
            return None

    return n("numberMatched"), n("numberReturned")


def tile_boxes(bbox_wgs: tuple[float, float, float, float], tile_m: int):
    west, south, east, north = bbox_wgs
    x1, y1 = TO_25832.transform(west, south)
    x2, y2 = TO_25832.transform(east, north)
    minx, maxx = sorted((x1, x2))
    miny, maxy = sorted((y1, y2))
    ix1 = math.floor(minx / tile_m)
    ix2 = math.ceil(maxx / tile_m)
    iy1 = math.floor(miny / tile_m)
    iy2 = math.ceil(maxy / tile_m)

    for iy in range(iy1, iy2):
        for ix in range(ix1, ix2):
            yield (
                ix,
                iy,
                (
                    ix * tile_m,
                    iy * tile_m,
                    (ix + 1) * tile_m,
                    (iy + 1) * tile_m,
                ),
            )


def is_retryable_http(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRY_STATUS
    return isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
            httpx.TransportError,
        ),
    )


def fetch_page(
    client: httpx.Client,
    endpoint: str,
    params: dict,
    *,
    max_retries: int,
    label: str,
) -> bytes:
    """Fetch one WFS page with retry/backoff."""
    last_exc = None

    for attempt in range(max_retries + 1):
        try:
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            content = response.content

            # Validate before persisting. This catches truncated XML as well.
            if (
                b"ExceptionReport" in content[:5000]
                or b"ExceptionText" in content[:5000]
            ):
                response_counts(content)
            else:
                response_counts(content)

            return content

        except Exception as exc:
            last_exc = exc
            if not is_retryable_http(exc) and not isinstance(exc, RuntimeError):
                raise

            if attempt >= max_retries:
                break

            delay = min(60.0, (2 ** attempt) * 2.0 + random.uniform(0.3, 1.5))
            print(
                f"      ⚠ {label}: {type(exc).__name__}: {str(exc)[:140]}"
            )
            print(
                f"        Retry {attempt + 1}/{max_retries} in {delay:.1f}s …",
                flush=True,
            )
            time.sleep(delay)

    raise RuntimeError(
        f"{label}: nach {max_retries} Retries weiterhin fehlgeschlagen: {last_exc}"
    ) from last_exc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="koeln")
    ap.add_argument("--tile-m", type=int, default=4000)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--max-retries", type=int, default=7)
    ap.add_argument("--pause", type=float, default=0.15)
    args = ap.parse_args()

    market = get_market(args.market)
    provider = get_building_provider(market["provider"])
    if not provider or market["provider"] != "GEOBASIS_NRW":
        raise SystemExit(
            f"Market {market['code']} nutzt nicht GEOBASIS_NRW: {market['provider']}"
        )

    endpoint = provider["endpoint"]
    out = BASE / "data" / "raw" / market["code"] / "nrw_buildings"
    out.mkdir(parents=True, exist_ok=True)

    tiles = list(tile_boxes(market["bbox"], max(1000, args.tile_m)))

    print(f"Geobasis NRW WFS: {endpoint}")
    print(f"Market: {market['name']} · {len(tiles)} Tiles à ca. {args.tile_m} m")
    print(f"FeatureType: {FEATURE_TYPE}")
    print(
        "Resume: fertige Tiles und bereits gespeicherte Seiten werden wiederverwendet.",
        flush=True,
    )

    completed = 0
    downloaded_pages = 0
    reused_pages = 0
    total_mb = 0.0

    headers = {
        "User-Agent": "SolarLead/0.4.1-hotfix (+regional-building-intelligence)",
        # The NRW WFS sent a disconnect during the long Köln transfer.
        # Avoiding long-lived keep-alive sockets makes retries more robust.
        "Connection": "close",
    }

    timeout = httpx.Timeout(connect=30.0, read=180.0, write=30.0, pool=30.0)
    limits = httpx.Limits(max_keepalive_connections=0, max_connections=2)

    with httpx.Client(
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
        limits=limits,
    ) as client:
        for idx, (ix, iy, bbox) in enumerate(tiles, 1):
            tile_dir = out / f"tile_{ix}_{iy}"
            done = tile_dir / ".done"

            if done.exists() and not args.force:
                completed += 1
                if idx == 1 or idx % 5 == 0 or idx == len(tiles):
                    print(
                        f"  [{idx}/{len(tiles)}] Tile {ix}/{iy}: ✓ bereits fertig",
                        flush=True,
                    )
                continue

            tile_dir.mkdir(parents=True, exist_ok=True)

            if args.force:
                for p in tile_dir.glob("page_*.gml"):
                    p.unlink()
                for p in tile_dir.glob("page_*.part"):
                    p.unlink()
                done.unlink(missing_ok=True)

            start = 0
            page = 0

            while True:
                minx, miny, maxx, maxy = bbox
                params = {
                    "SERVICE": "WFS",
                    "REQUEST": "GetFeature",
                    "VERSION": "2.0.0",
                    "TYPENAMES": FEATURE_TYPE,
                    "SRSNAME": "urn:ogc:def:crs:EPSG::25832",
                    "BBOX": (
                        f"{minx},{miny},{maxx},{maxy},"
                        "urn:ogc:def:crs:EPSG::25832"
                    ),
                    "COUNT": PAGE_SIZE,
                    "STARTINDEX": start,
                }

                page_file = tile_dir / f"page_{page:03d}.gml"

                if page_file.exists() and not args.force:
                    content = page_file.read_bytes()
                    try:
                        matched, returned = response_counts(content)
                    except Exception:
                        print(
                            f"      vorhandene Seite {page_file.name} ist ungültig → neu laden",
                            flush=True,
                        )
                        page_file.unlink(missing_ok=True)
                        continue

                    reused_pages += 1
                    print(
                        f"      ↳ Resume {ix}/{iy} page {page}: "
                        f"{len(content)/1024/1024:.1f} MB aus Cache",
                        flush=True,
                    )
                else:
                    content = fetch_page(
                        client,
                        endpoint,
                        params,
                        max_retries=max(0, args.max_retries),
                        label=f"Tile {ix}/{iy} page {page}",
                    )
                    matched, returned = response_counts(content)

                    tmp_file = tile_dir / f"page_{page:03d}.part"
                    tmp_file.write_bytes(content)
                    tmp_file.replace(page_file)

                    downloaded_pages += 1
                    total_mb += len(content) / 1024 / 1024

                if returned is None:
                    # Conservative fallback: tiny response => no/final results.
                    returned = 0 if len(content) < 1500 else PAGE_SIZE

                if returned < PAGE_SIZE:
                    break

                start += returned
                page += 1

                if matched is not None and start >= matched:
                    break

                if page > 50:
                    raise RuntimeError(
                        f"Unplausibel viele WFS-Seiten für Tile {ix}/{iy}."
                    )

                time.sleep(max(0.0, args.pause))

            done.write_text(
                json.dumps(
                    {
                        "tile": [ix, iy],
                        "pages": page + 1,
                        "bbox25832": bbox,
                        "completed_at_unix": time.time(),
                    }
                ),
                encoding="utf-8",
            )

            completed += 1
            print(
                f"  [{idx}/{len(tiles)}] Tile {ix}/{iy}: "
                f"✓ {page + 1} Seite(n) · neu insgesamt {total_mb:.1f} MB",
                flush=True,
            )
            time.sleep(max(0.0, args.pause))

    print()
    print(
        f"Fertig: {completed}/{len(tiles)} Tiles; "
        f"neu={downloaded_pages} Seiten; "
        f"wiederverwendet={reused_pages} Seiten; "
        f"neuer Download≈{total_mb:.1f} MB"
    )
    print(f"Ablage: {out}")


if __name__ == "__main__":
    main()
