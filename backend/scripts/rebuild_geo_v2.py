"""Rebuild all markets that already have source files with cross-market scoring v2."""
from __future__ import annotations
import os,subprocess,sys
from pathlib import Path
from app.db import SessionLocal
from app.models import Market
BASE=Path(__file__).resolve().parents[1];ENV={**os.environ,'PYTHONPATH':str(BASE)}

def main():
    db=SessionLocal()
    try:markets=[m.code for m in db.query(Market).filter(Market.active==True).all()]  # noqa: E712
    finally:db.close()
    for market in markets:
        if not (BASE/'data'/'processed'/market/'zensus_cells.csv').exists() and not (market=='waldshut' and (BASE/'data'/'processed'/'zensus_cells.csv').exists()):
            print(f'{market}: keine Quelldaten, übersprungen');continue
        # Waldshut legacy files stay in root; generic builder needs a regional view.
        if market=='waldshut':
            reg=BASE/'data'/'processed'/'waldshut';reg.mkdir(parents=True,exist_ok=True)
            for name in ('zensus_cells.csv','lgl_cells.csv','solar_cells.csv','mastr_cells.csv','campaign_cells.csv'):
                src=BASE/'data'/'processed'/name;dst=reg/name
                if src.exists() and not dst.exists():dst.write_bytes(src.read_bytes())
        subprocess.run([sys.executable,str(BASE/'scripts'/'build_geo_cells_market.py'),'--market',market],cwd=BASE,env=ENV,check=True)
        subprocess.run([sys.executable,str(BASE/'scripts'/'load_geo_cells.py'),'--market',market,'--vertical','balcony_pv'],cwd=BASE,env=ENV,check=True)
    print('Cross-market Geo-Scoring v2 abgeschlossen.')

if __name__=='__main__':main()
