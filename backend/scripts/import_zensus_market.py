"""Import the official Zensus 2022 100 m building/ dwelling dataset for one market.

This reuses the tolerant INSPIRE-grid parser from the Waldshut importer but gets
its bounding box from the V0.4 ``markets`` table and writes market-scoped files:

    data/processed/<market>/zensus_cells.csv

Usage:
    PYTHONPATH=. python scripts/import_zensus_market.py --market koeln
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from app.db import SessionLocal
from app.models import Market
from import_zensus_waldshut import choose_100m_csv, parse

BASE = Path(__file__).resolve().parents[1]


def get_market(code: str) -> Market:
    db = SessionLocal()
    try:
        m = db.query(Market).filter(Market.code == code, Market.active == True).first()  # noqa: E712
        if not m:
            raise SystemExit(f"Market '{code}' nicht gefunden. Zuerst V0.4-Migration ausführen.")
        # detach the scalar values we need before closing the session
        values = {k: getattr(m, k) for k in (
            'code','name','bbox_west','bbox_south','bbox_east','bbox_north'
        )}
    finally:
        db.close()
    return type('MarketInfo', (), values)()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--market', required=True)
    ap.add_argument('--csv', default=None, help='Optionaler Pfad zur offiziellen 100m-Zensus-CSV')
    args = ap.parse_args()

    market = get_market(args.market)
    bbox = (market.bbox_west, market.bbox_south, market.bbox_east, market.bbox_north)
    source = choose_100m_csv(args.csv)
    output = BASE / 'data' / 'processed' / market.code / 'zensus_cells.csv'

    print(f"Verarbeite Zensus für: {market.name} ({market.code})")
    print(f"Quelle: {source}")
    print(f"Market-BBOX: {bbox}")
    aggs, matched, _fields = parse(source, bbox)

    rows = []
    for gid, a in aggs.items():
        total = a['total_buildings']
        if total <= 0:
            continue
        mfh_share = min(1.0, max(0.0, a['mfh'] / total)) if a['mfh'] else 0.0
        housing_units = max(total, a['weighted_units'])
        rows.append({
            'cell_id': gid,
            'latitude': f"{a['lat']:.7f}",
            'longitude': f"{a['lon']:.7f}",
            'housing_units': f"{housing_units:.2f}",
            'mfh_share': f"{mfh_share:.4f}",
            'building_count_zensus': f"{total:.0f}",
            'mfh_buildings_zensus': f"{a['mfh']:.0f}",
            'source': 'Zensus 2022 / Destatis',
        })

    if not rows:
        raise SystemExit(f"Keine Zensus-Zellen für Market {market.code} erzeugt.")

    rows.sort(key=lambda r: float(r['housing_units']), reverse=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    print(f"Fertig: {len(rows)} Zensus-Zellen -> {output}")
    print(f"Verwertete Kategoriezeilen: {matched}")
    print('Top 5 Wohndichte:')
    for r in rows[:5]:
        print(f"  {r['cell_id']}: units≈{r['housing_units']}, MFH={float(r['mfh_share'])*100:.0f}%")


if __name__ == '__main__':
    main()
