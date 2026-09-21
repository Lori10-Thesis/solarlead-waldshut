import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AdminUser, Lead, LeadDelivery, Market, Partner, PartnerBuyRule, Vertical
from ..schemas import BuyerPartnerCreate, BuyerPartnerUpdate, DeliveryCreate, DeliveryFeedback
from ..security import get_current_admin, require_csrf
from ..services.leads import record_event

router = APIRouter(prefix='/api/admin/buyers', tags=['buyers'], dependencies=[Depends(get_current_admin)])

READY_STATUSES = {'qualified', 'sales_ready', 'appointment'}
ACTIVE_DELIVERY_STATUSES = {'delivered', 'accepted', 'won'}


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = value.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-') or 'partner'
    return value[:100]


def _unique_slug(db: Session, name: str) -> str:
    base = _slugify(name)
    slug = base
    i = 2
    while db.query(Partner).filter(Partner.slug == slug).first():
        slug = f'{base}-{i}'[:120]
        i += 1
    return slug


def _partner_dict(db: Session, partner: Partner):
    rules = db.query(PartnerBuyRule).filter(PartnerBuyRule.partner_id == partner.id).order_by(PartnerBuyRule.market_code).all()
    deliveries = db.query(LeadDelivery).filter(LeadDelivery.partner_id == partner.id).all()
    won = sum(1 for d in deliveries if d.status == 'won')
    delivered = sum(1 for d in deliveries if d.status in {'delivered', 'accepted', 'won', 'lost', 'rejected'})
    revenue = round(sum(d.price_eur or 0 for d in deliveries if d.status != 'cancelled'), 2)
    order_value = round(sum(d.order_value_eur or 0 for d in deliveries if d.status == 'won'), 2)
    return {
        'id': partner.id,
        'name': partner.name,
        'slug': partner.slug,
        'active': partner.active,
        'partner_type': partner.partner_type,
        'buyer_ready': partner.buyer_ready,
        'contact_name': partner.contact_name,
        'contact_email': partner.contact_email,
        'contact_phone': partner.contact_phone,
        'website': partner.website,
        'notes': partner.notes,
        'rules': [{
            'id': r.id, 'market_code': r.market_code, 'vertical_code': r.vertical_code,
            'lead_price_eur': r.lead_price_eur, 'min_lead_score': r.min_lead_score,
            'daily_cap': r.daily_cap, 'exclusive': r.exclusive, 'active': r.active,
        } for r in rules],
        'metrics': {
            'delivered': delivered,
            'won': won,
            'win_rate': round(won / delivered * 100, 1) if delivered else None,
            'lead_revenue_eur': revenue,
            'order_value_eur': order_value,
        },
    }


@router.get('/partners')
def list_buyers(eligible: bool = False, db: Session = Depends(get_db)):
    q = db.query(Partner)
    if eligible:
        q = q.filter(Partner.partner_type == 'buyer', Partner.buyer_ready == True, Partner.active == True)  # noqa: E712
    else:
        q = q.filter(Partner.partner_type == 'buyer')
    return [_partner_dict(db, p) for p in q.order_by(Partner.name).all()]


@router.post('/partners', dependencies=[Depends(require_csrf)])
def create_buyer(payload: BuyerPartnerCreate, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if not db.query(Market).filter(Market.code == payload.market_code, Market.active == True).first():  # noqa: E712
        raise HTTPException(status_code=400, detail='Market nicht aktiv oder unbekannt.')
    if not db.query(Vertical).filter(Vertical.code == payload.vertical_code, Vertical.active == True).first():  # noqa: E712
        raise HTTPException(status_code=400, detail='Vertical nicht aktiv oder unbekannt.')

    partner = Partner(
        name=payload.name.strip(), slug=_unique_slug(db, payload.name), active=True,
        partner_type='buyer', buyer_ready=True,
        contact_name=payload.contact_name.strip() or None,
        contact_email=(str(payload.contact_email).strip().lower() if payload.contact_email else None),
        contact_phone=payload.contact_phone.strip() or None,
        website=payload.website.strip() or None,
        notes=payload.notes.strip() or None,
    )
    db.add(partner); db.flush()
    rule = PartnerBuyRule(
        partner_id=partner.id, market_code=payload.market_code, vertical_code=payload.vertical_code,
        lead_price_eur=payload.lead_price_eur, min_lead_score=payload.min_lead_score,
        daily_cap=payload.daily_cap, exclusive=True, active=True,
    )
    db.add(rule)
    db.commit(); db.refresh(partner)
    return _partner_dict(db, partner)


@router.patch('/partners/{partner_id}', dependencies=[Depends(require_csrf)])
def update_buyer(partner_id: int, payload: BuyerPartnerUpdate, db: Session = Depends(get_db)):
    partner = db.get(Partner, partner_id)
    if not partner or partner.partner_type != 'buyer':
        raise HTTPException(status_code=404, detail='Buyer nicht gefunden.')
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == 'contact_email' and value is not None:
            value = str(value).strip().lower()
        if isinstance(value, str):
            value = value.strip() or None
        setattr(partner, field, value)
    db.commit(); db.refresh(partner)
    return _partner_dict(db, partner)


@router.get('/ready')
def ready_leads(db: Session = Depends(get_db)):
    leads = (db.query(Lead)
        .filter(
            Lead.lead_origin == 'owned',
            Lead.status.in_(list(READY_STATUSES)),
            Lead.partner_consent_granted == True,  # noqa: E712
            Lead.partner_consent_partner_id.isnot(None),
        )
        .order_by(Lead.lead_score.desc(), Lead.created_at.asc()).all())
    out = []
    for lead in leads:
        partner = db.get(Partner, lead.partner_consent_partner_id) if lead.partner_consent_partner_id else None
        rule = None
        reason = None
        if not partner or not partner.active or not partner.buyer_ready or partner.partner_type != 'buyer':
            reason = 'Freigegebener Partner ist noch kein aktiver Buyer.'
        else:
            rule = (db.query(PartnerBuyRule)
                .filter(
                    PartnerBuyRule.partner_id == partner.id,
                    PartnerBuyRule.market_code == lead.market_code,
                    PartnerBuyRule.vertical_code == lead.vertical,
                    PartnerBuyRule.active == True,  # noqa: E712
                ).order_by(PartnerBuyRule.id.desc()).first())
            if not rule:
                reason = 'Keine aktive Buy Rule für Markt/Vertical.'
            elif lead.lead_score < rule.min_lead_score:
                reason = f'Lead Score unter Mindestscore {rule.min_lead_score}.'
        existing = (db.query(LeadDelivery).filter(
            LeadDelivery.lead_id == lead.id,
            LeadDelivery.status.in_(list(ACTIVE_DELIVERY_STATUSES)),
        ).first())
        if existing:
            reason = f'Bereits als Delivery #{existing.id} ausgeliefert.'
        out.append({
            'lead': {
                'id': lead.id, 'created_at': lead.created_at.isoformat(), 'first_name': lead.first_name,
                'last_name': lead.last_name, 'phone': lead.phone, 'email': lead.email,
                'postal_code': lead.postal_code, 'city': lead.city, 'market_code': lead.market_code,
                'vertical': lead.vertical, 'lead_score': lead.lead_score, 'geo_fit_score': lead.geo_fit_score,
                'purchase_timeframe': lead.purchase_timeframe, 'product_preference': lead.product_preference,
                'status': lead.status,
            },
            'partner': {'id': partner.id, 'name': partner.name} if partner else None,
            'rule': ({'id': rule.id, 'price_eur': rule.lead_price_eur, 'min_lead_score': rule.min_lead_score, 'daily_cap': rule.daily_cap} if rule else None),
            'commercially_ready': reason is None,
            'reason': reason,
        })
    return out


@router.post('/deliveries', dependencies=[Depends(require_csrf)])
def create_delivery(payload: DeliveryCreate, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    lead = db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead nicht gefunden.')
    if lead.lead_origin != 'owned' or lead.status not in READY_STATUSES:
        raise HTTPException(status_code=400, detail='Lead ist nicht für kommerzielle Auslieferung freigegeben.')
    if not lead.partner_consent_granted or lead.partner_consent_partner_id != payload.partner_id:
        raise HTTPException(status_code=400, detail='Es liegt keine dokumentierte Freigabe für genau diesen Partner vor.')

    partner = db.get(Partner, payload.partner_id)
    if not partner or not partner.active or not partner.buyer_ready or partner.partner_type != 'buyer':
        raise HTTPException(status_code=400, detail='Partner ist kein aktiver Buyer.')

    existing = db.query(LeadDelivery).filter(LeadDelivery.lead_id == lead.id, LeadDelivery.status.in_(list(ACTIVE_DELIVERY_STATUSES))).first()
    if existing:
        raise HTTPException(status_code=409, detail=f'Lead wurde bereits als Delivery #{existing.id} ausgeliefert.')

    rule = (db.query(PartnerBuyRule).filter(
        PartnerBuyRule.partner_id == partner.id,
        PartnerBuyRule.market_code == lead.market_code,
        PartnerBuyRule.vertical_code == lead.vertical,
        PartnerBuyRule.active == True,  # noqa: E712
    ).order_by(PartnerBuyRule.id.desc()).first())
    if not rule:
        raise HTTPException(status_code=400, detail='Keine aktive Buy Rule für diesen Lead vorhanden.')
    if lead.lead_score < rule.min_lead_score:
        raise HTTPException(status_code=400, detail=f'Lead Score liegt unter Mindestscore {rule.min_lead_score}.')

    today = datetime.utcnow().date()
    todays = db.query(LeadDelivery).filter(LeadDelivery.partner_id == partner.id, LeadDelivery.created_at >= datetime(today.year, today.month, today.day)).count()
    if todays >= rule.daily_cap:
        raise HTTPException(status_code=409, detail=f'Tageslimit des Buyers ({rule.daily_cap}) erreicht.')

    price = payload.price_override_eur if payload.price_override_eur is not None else rule.lead_price_eur
    delivery = LeadDelivery(
        lead_id=lead.id, partner_id=partner.id, buy_rule_id=rule.id,
        market_code=lead.market_code, vertical_code=lead.vertical,
        price_eur=price, status='delivered', delivered_at=datetime.utcnow(),
    )
    db.add(delivery); db.flush()
    lead.assigned_partner_id = partner.id
    lead.assigned_partner = partner.name
    lead.revenue_eur = price
    lead.status = 'sold'
    record_event(db, lead.id, 'buyer_delivery', user.email, {'delivery_id': delivery.id, 'partner_id': partner.id, 'partner_name': partner.name, 'price_eur': price})
    db.commit(); db.refresh(delivery)
    return {'id': delivery.id, 'lead_id': lead.id, 'partner_id': partner.id, 'partner_name': partner.name, 'price_eur': delivery.price_eur, 'status': delivery.status}


@router.get('/deliveries')
def list_deliveries(db: Session = Depends(get_db)):
    deliveries = db.query(LeadDelivery).order_by(LeadDelivery.created_at.desc()).limit(500).all()
    out=[]
    for d in deliveries:
        lead=db.get(Lead,d.lead_id); partner=db.get(Partner,d.partner_id)
        out.append({
            'id':d.id,'lead_id':d.lead_id,'partner_id':d.partner_id,'partner_name':partner.name if partner else f'Partner {d.partner_id}',
            'lead_name':f'{lead.first_name} {lead.last_name}'.strip() if lead else f'Lead {d.lead_id}',
            'market_code':d.market_code,'vertical_code':d.vertical_code,'price_eur':d.price_eur,'status':d.status,
            'feedback_outcome':d.feedback_outcome,'order_value_eur':d.order_value_eur,'rejection_reason':d.rejection_reason,
            'created_at':d.created_at.isoformat(),'feedback_at':d.feedback_at.isoformat() if d.feedback_at else None,
        })
    return out


@router.patch('/deliveries/{delivery_id}/feedback', dependencies=[Depends(require_csrf)])
def delivery_feedback(delivery_id: int, payload: DeliveryFeedback, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    delivery = db.get(LeadDelivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail='Delivery nicht gefunden.')
    lead = db.get(Lead, delivery.lead_id)
    delivery.status = payload.outcome
    delivery.feedback_outcome = payload.outcome
    delivery.feedback_at = datetime.utcnow()
    delivery.order_value_eur = payload.order_value_eur
    delivery.rejection_reason = payload.reason.strip() or None
    delivery.partner_notes = payload.notes.strip() or None
    if lead:
        if payload.outcome == 'won':
            lead.status = 'won'
        elif payload.outcome == 'lost':
            lead.status = 'lost'
        elif payload.outcome == 'rejected':
            # Re-contact is required before another partner can receive data.
            lead.status = 'qualified'
        elif payload.outcome == 'accepted':
            lead.status = 'sold'
        record_event(db, lead.id, 'buyer_feedback', user.email, {'delivery_id': delivery.id, **payload.model_dump()})
    db.commit(); db.refresh(delivery)
    return {'ok':True,'delivery_id':delivery.id,'status':delivery.status}


@router.get('/dashboard')
def buyer_dashboard(db: Session = Depends(get_db)):
    buyers = db.query(Partner).filter(Partner.partner_type == 'buyer', Partner.active == True).count()  # noqa: E712
    deliveries = db.query(LeadDelivery).all()
    delivered = sum(1 for d in deliveries if d.status != 'cancelled')
    won = sum(1 for d in deliveries if d.status == 'won')
    revenue = round(sum(d.price_eur or 0 for d in deliveries if d.status != 'cancelled'), 2)
    order_value = round(sum(d.order_value_eur or 0 for d in deliveries if d.status == 'won'), 2)
    ready_count = 0
    for lead in db.query(Lead).filter(Lead.lead_origin == 'owned', Lead.status.in_(list(READY_STATUSES)), Lead.partner_consent_granted == True).all():  # noqa: E712
        if lead.partner_consent_partner_id:
            ready_count += 1
    return {
        'active_buyers': buyers,
        'ready_leads': ready_count,
        'deliveries': delivered,
        'won': won,
        'win_rate': round(won/delivered*100,1) if delivered else None,
        'lead_revenue_eur': revenue,
        'reported_order_value_eur': order_value,
    }
