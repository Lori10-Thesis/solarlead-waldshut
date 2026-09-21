import json
from datetime import datetime
from math import cos, radians
from sqlalchemy.orm import Session
from .models import GeoCell, Lead, Market, Partner, SalesRep, Territory


def _prefixes(raw: str | None) -> list[str]:
    try:
        return [str(x).strip() for x in json.loads(raw or '[]') if str(x).strip()]
    except Exception:
        return []


def prefix_match(postal_code: str, prefixes: list[str]) -> bool:
    pc = (postal_code or '').strip()
    return any(pc.startswith(p) for p in prefixes)


def resolve_market(db: Session, postal_code: str) -> Market | None:
    candidates = []
    for market in db.query(Market).filter(Market.active == True).all():  # noqa: E712
        matches = [p for p in _prefixes(market.postal_prefixes_json) if postal_code.startswith(p)]
        if matches:
            candidates.append((max(len(x) for x in matches), market))
    return sorted(candidates, key=lambda x: x[0], reverse=True)[0][1] if candidates else None


def nearest_geo_fit(db: Session, market_code: str, vertical_code: str, lat: float | None, lon: float | None) -> int | None:
    if lat is None or lon is None or not market_code or market_code == 'unassigned':
        return None
    cells = db.query(GeoCell).filter(GeoCell.market_code == market_code, GeoCell.vertical_code == vertical_code).all()
    if not cells:
        return None
    lon_factor = max(0.2, cos(radians(lat)))
    best = min(cells, key=lambda c: (c.latitude-lat)**2 + ((c.longitude-lon)*lon_factor)**2)
    return int(best.potential_score)


def route_lead(db: Session, lead: Lead):
    market = resolve_market(db, lead.postal_code)
    lead.market_code = market.code if market else 'unassigned'
    lead.geo_fit_score = nearest_geo_fit(db, lead.market_code, lead.vertical, lead.latitude, lead.longitude)
    if not market:
        return None

    today = datetime.utcnow().date()
    candidates = []
    territories = db.query(Territory).filter(
        Territory.active == True, Territory.vertical_code == lead.vertical, Territory.market_code == market.code  # noqa: E712
    ).order_by(Territory.priority.desc()).all()
    for territory in territories:
        if not prefix_match(lead.postal_code, _prefixes(territory.postal_prefixes_json)):
            continue
        q = db.query(Lead).filter(Lead.assigned_sales_rep_id == territory.sales_rep_id)
        assigned_today = sum(1 for x in q.all() if x.created_at.date() == today)
        if assigned_today >= territory.max_leads_per_day:
            continue
        candidates.append((assigned_today, -territory.priority, territory))

    if not candidates:
        return None
    territory = sorted(candidates, key=lambda x: (x[0], x[1]))[0][2]
    lead.assigned_partner_id = territory.partner_id
    lead.assigned_sales_rep_id = territory.sales_rep_id
    partner = db.get(Partner, territory.partner_id) if territory.partner_id else None
    lead.assigned_partner = partner.name if partner else None
    rep = db.get(SalesRep, territory.sales_rep_id) if territory.sales_rep_id else None
    return {'territory': territory.name, 'partner': partner.name if partner else None, 'sales_rep': rep.name if rep else None}
