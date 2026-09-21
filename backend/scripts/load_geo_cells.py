"""Load geo_cells.csv for one market/vertical without deleting other markets."""
import argparse
import csv
from pathlib import Path
from app.db import Base, SessionLocal, engine
from app.models import GeoCell

BASE=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--market', default='waldshut')
    ap.add_argument('--vertical', default='balcony_pv')
    ap.add_argument('--file', default=None)
    args=ap.parse_args()
    default_regional=BASE/'data'/'processed'/args.market/'geo_cells.csv'
    legacy=BASE/'data'/'processed'/'geo_cells.csv'
    source=Path(args.file) if args.file else (default_regional if default_regional.exists() else legacy if args.market=='waldshut' else default_regional)
    if not source.exists(): raise SystemExit(f'Fehlt: {source}')
    Base.metadata.create_all(bind=engine); db=SessionLocal()
    try:
        db.query(GeoCell).filter(GeoCell.market_code==args.market,GeoCell.vertical_code==args.vertical).delete(synchronize_session=False)
        with source.open(encoding='utf-8',newline='') as f:
            for row in csv.DictReader(f):
                db.add(GeoCell(name=row['name'],market_code=args.market,vertical_code=args.vertical,
                    latitude=float(row['latitude']),longitude=float(row['longitude']),potential_score=int(row['potential_score']),
                    housing_density_score=int(row['housing_density_score']),building_fit_score=int(row['building_fit_score']),
                    solar_score=int(row['solar_score']),market_gap_score=int(row['market_gap_score']),campaign_score=int(row['campaign_score'])))
        db.commit(); print(f'Geo-Radar {args.market}/{args.vertical} aktualisiert aus {source}')
    finally: db.close()

if __name__=='__main__': main()
