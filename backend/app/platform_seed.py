import json
from sqlalchemy.orm import Session
from .models import Market, Partner, SalesRep, Territory, Vertical

BALCONY_FUNNEL = {
    'version': 1,
    'steps': ['postal_code','owner_status','installation_location','orientation','shading','consumption','purchase_timeframe','product_preference','result','contact','review']
}


def seed_platform(db: Session):
    if not db.query(Vertical).filter(Vertical.code == 'balcony_pv').first():
        db.add(Vertical(code='balcony_pv', name='Balkonkraftwerk', active=True,
            funnel_config_json=json.dumps(BALCONY_FUNNEL), scoring_config_json=json.dumps({'strategy':'buyer_intent_v1'})))

    markets = [
        dict(code='waldshut', name='Waldshut / Hochrhein', country_code='DE', state_code='BW',
             center_lat=47.6237, center_lon=8.2172, bbox_west=8.10, bbox_south=47.56, bbox_east=8.38, bbox_north=47.69,
             postal_prefixes_json=json.dumps(['797']), building_provider='LGL_BW'),
        dict(code='koeln', name='Köln', country_code='DE', state_code='NW',
             center_lat=50.9375, center_lon=6.9603, bbox_west=6.77, bbox_south=50.83, bbox_east=7.17, bbox_north=51.09,
             postal_prefixes_json=json.dumps(['506','507','508','509','510','511']), building_provider='GEOBASIS_NRW'),
    ]
    for item in markets:
        if not db.query(Market).filter(Market.code == item['code']).first():
            db.add(Market(**item))
    db.flush()

    partners = [('pilot_waldshut','Pilotpartner Waldshut'),('pilot_koeln','Pilotpartner Köln')]
    partner_ids = {}
    for slug, name in partners:
        p = db.query(Partner).filter(Partner.slug == slug).first()
        if not p:
            p = Partner(slug=slug, name=name, active=True); db.add(p); db.flush()
        partner_ids[slug] = p.id

    reps = [('Waldshut Vertrieb', partner_ids['pilot_waldshut']), ('Köln Vertrieb', partner_ids['pilot_koeln'])]
    rep_ids = {}
    for name, partner_id in reps:
        r = db.query(SalesRep).filter(SalesRep.name == name, SalesRep.partner_id == partner_id).first()
        if not r:
            r = SalesRep(name=name, partner_id=partner_id, active=True); db.add(r); db.flush()
        rep_ids[name] = r.id

    territories = [
        ('Balkon-PV Waldshut','balcony_pv','waldshut',partner_ids['pilot_waldshut'],rep_ids['Waldshut Vertrieb'],['797']),
        ('Balkon-PV Köln','balcony_pv','koeln',partner_ids['pilot_koeln'],rep_ids['Köln Vertrieb'],['506','507','508','509','510','511']),
    ]
    for name, vertical, market, partner_id, rep_id, prefixes in territories:
        if not db.query(Territory).filter(Territory.name == name).first():
            db.add(Territory(name=name, vertical_code=vertical, market_code=market, partner_id=partner_id,
                sales_rep_id=rep_id, postal_prefixes_json=json.dumps(prefixes), priority=100, max_leads_per_day=50, active=True))
    db.commit()
