from sqlalchemy import inspect, text
from app.db import Base, SessionLocal, engine
from app.models import AcquisitionCampaign

VERSION = 'V0.5.1 Organic Growth Layer'


def add_columns():
    insp = inspect(engine)
    existing = {c['name'] for c in insp.get_columns('leads')}
    if 'funnel_session_id' not in existing:
        print('ADD leads.funnel_session_id')
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE leads ADD COLUMN funnel_session_id VARCHAR(120)'))
    with engine.begin() as conn:
        conn.execute(text('CREATE INDEX IF NOT EXISTS ix_leads_funnel_session_id ON leads (funnel_session_id)'))


def seed_campaigns():
    db = SessionLocal()
    try:
        rows = [
            dict(code='whatsapp_waldshut', name='WhatsApp Waldshut', channel='whatsapp', market_code='waldshut', source_id='whatsapp_waldshut', utm_source='whatsapp', utm_medium='group', utm_campaign='organic_waldshut'),
            dict(code='facebook_waldshut', name='Facebook Gruppen Waldshut', channel='facebook_group', market_code='waldshut', source_id='facebook_waldshut', utm_source='facebook', utm_medium='group', utm_campaign='organic_waldshut'),
            dict(code='whatsapp_koeln', name='WhatsApp Köln', channel='whatsapp', market_code='koeln', source_id='whatsapp_koeln', utm_source='whatsapp', utm_medium='group', utm_campaign='organic_koeln'),
            dict(code='facebook_koeln', name='Facebook Gruppen Köln', channel='facebook_group', market_code='koeln', source_id='facebook_koeln', utm_source='facebook', utm_medium='group', utm_campaign='organic_koeln'),
            dict(code='local_qr_waldshut', name='QR / Flyer Waldshut', channel='local_qr', market_code='waldshut', source_id='local_qr_waldshut', utm_source='offline', utm_medium='qr', utm_campaign='local_waldshut'),
            dict(code='local_qr_koeln', name='QR / Flyer Köln', channel='local_qr', market_code='koeln', source_id='local_qr_koeln', utm_source='offline', utm_medium='qr', utm_campaign='local_koeln'),
            dict(code='referral', name='Empfehlungen / Referral', channel='referral', market_code=None, source_id='referral', utm_source='referral', utm_medium='referral', utm_campaign='referral_program'),
        ]
        for row in rows:
            old = db.query(AcquisitionCampaign).filter(AcquisitionCampaign.code == row['code']).first()
            if not old:
                db.add(AcquisitionCampaign(vertical_code='balcony_pv', active=True, **row))
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    print(VERSION)
    Base.metadata.create_all(bind=engine)
    add_columns()
    seed_campaigns()
    print('V0.5.1 Migration abgeschlossen.')
