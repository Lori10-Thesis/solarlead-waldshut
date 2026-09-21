from sqlalchemy import inspect, text
from app.db import engine, Base, SessionLocal
from app.models import AcquisitionCampaign

VERSION = 'V0.5 Organic Acquisition + Setter Ops'

COLUMNS = {
    'leads': {
        'lead_origin': "VARCHAR(40) DEFAULT 'owned'",
        'client_account_id': 'INTEGER',
        'setter_status': "VARCHAR(40) DEFAULT 'queued'",
        'setter_attempts': 'INTEGER DEFAULT 0',
        'setter_name': 'VARCHAR(160)',
        'setter_outcome': 'VARCHAR(120)',
    }
}


def add_columns():
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in COLUMNS.items():
            existing = {c['name'] for c in insp.get_columns(table)}
            for name, ddl in cols.items():
                if name not in existing:
                    print(f'ADD {table}.{name}')
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {ddl}'))


def create_indexes():
    statements = [
        'CREATE INDEX IF NOT EXISTS ix_leads_lead_origin ON leads (lead_origin)',
        'CREATE INDEX IF NOT EXISTS ix_leads_client_account_id ON leads (client_account_id)',
        'CREATE INDEX IF NOT EXISTS ix_leads_setter_status ON leads (setter_status)',
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def seed_campaigns():
    db = SessionLocal()
    try:
        rows = [
            dict(code='whatsapp_waldshut', name='WhatsApp Waldshut', channel='whatsapp', market_code='waldshut', source_id='whatsapp_waldshut', utm_source='whatsapp', utm_medium='group', utm_campaign='organic_waldshut'),
            dict(code='facebook_koeln', name='Facebook Gruppen Köln', channel='facebook_group', market_code='koeln', source_id='facebook_koeln', utm_source='facebook', utm_medium='group', utm_campaign='organic_koeln'),
            dict(code='local_qr', name='Lokale QR/Flyer', channel='local_qr', market_code=None, source_id='local_qr', utm_source='offline', utm_medium='qr', utm_campaign='local_organic'),
            dict(code='referral', name='Empfehlungen / Referral', channel='referral', market_code=None, source_id='referral', utm_source='referral', utm_medium='referral', utm_campaign='referral_program'),
        ]
        for row in rows:
            if not db.query(AcquisitionCampaign).filter(AcquisitionCampaign.code == row['code']).first():
                db.add(AcquisitionCampaign(vertical_code='balcony_pv', active=True, **row))
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    print(VERSION)
    Base.metadata.create_all(bind=engine)
    add_columns()
    create_indexes()
    seed_campaigns()
    print('V0.5 Migration abgeschlossen.')
