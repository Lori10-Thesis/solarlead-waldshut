"""V0.4 migration: multi-market / vertical / routing platform core."""
import secrets
from sqlalchemy import inspect, text
from app.db import Base, SessionLocal, engine
from app.models import GeoCell, Lead
from app.platform_seed import seed_platform
from app.routing import resolve_market

LEAD_COLS = {
    'market_code': "VARCHAR(80) DEFAULT 'unassigned'",
    'geo_fit_score': 'INTEGER',
    'public_token': 'VARCHAR(160)',
    'product_preference': 'VARCHAR(60)',
    'contact_time': 'VARCHAR(40)',
    'assigned_partner_id': 'INTEGER',
    'assigned_sales_rep_id': 'INTEGER',
}
GEO_COLS = {
    'market_code': "VARCHAR(80) DEFAULT 'waldshut'",
    'vertical_code': "VARCHAR(80) DEFAULT 'balcony_pv'",
}


def ensure_columns(table: str, wanted: dict[str,str]):
    inspector=inspect(engine)
    if not inspector.has_table(table):
        return
    current={c['name'] for c in inspector.get_columns(table)}
    with engine.begin() as conn:
        for name, sql_type in wanted.items():
            if name not in current:
                print(f'ADD {table}.{name}')
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {sql_type}'))


def main():
    # On a fresh install create the current schema; on upgrades add missing columns first.
    Base.metadata.create_all(bind=engine)
    ensure_columns('leads', LEAD_COLS)
    ensure_columns('geo_cells', GEO_COLS)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("UPDATE geo_cells SET market_code='waldshut' WHERE market_code IS NULL OR market_code=''"))
        conn.execute(text("UPDATE geo_cells SET vertical_code='balcony_pv' WHERE vertical_code IS NULL OR vertical_code=''"))
        try:
            conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_leads_public_token_unique ON leads(public_token)'))
        except Exception:
            pass

    db=SessionLocal()
    try:
        seed_platform(db)
        leads=db.query(Lead).all()
        changed=0
        for lead in leads:
            market=resolve_market(db, lead.postal_code or '')
            lead.market_code=market.code if market else 'unassigned'
            if not lead.public_token:
                lead.public_token=secrets.token_urlsafe(24)
            changed+=1
        db.commit()
        print(f'{changed} bestehende Leads auf Market/Public-Token aktualisiert.')
        print(f'{db.query(GeoCell).count()} Geo-Zellen vorhanden; bestehende Zellen = Waldshut/balcony_pv.')
    finally:
        db.close()
    print('V0.4 Migration abgeschlossen.')

if __name__ == '__main__': main()
