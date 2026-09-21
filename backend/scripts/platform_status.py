from app.db import SessionLocal
from app.models import GeoCell, Lead, Market, Partner, SalesRep, Territory, Vertical

db=SessionLocal()
try:
    print('Verticals:', [(x.code,x.name) for x in db.query(Vertical).all()])
    for m in db.query(Market).order_by(Market.name).all():
        cells=db.query(GeoCell).filter(GeoCell.market_code==m.code).count()
        leads=db.query(Lead).filter(Lead.market_code==m.code).count()
        print(f'Market {m.code}: {m.name} | provider={m.building_provider} | geo_cells={cells} | leads={leads}')
    print('Partners:', [(p.id,p.name) for p in db.query(Partner).all()])
    print('Sales reps:', [(r.id,r.name) for r in db.query(SalesRep).all()])
    print('Territories:', [(t.name,t.market_code,t.vertical_code,t.sales_rep_id) for t in db.query(Territory).all()])
finally:
    db.close()
