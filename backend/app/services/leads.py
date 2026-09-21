import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models import ClientAccount, ConsentRecord, FunnelEvent, Lead, LeadEvent
from ..pv import calculate_pv
from ..routing import route_lead
from ..scoring import lead_score
from ..request_utils import client_ip
from ..consent_texts import PUBLIC_CONTACT_VERSION, public_contact_text


def normalize_phone(value: str) -> str:
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('00'):
        digits = digits[2:]
    if digits.startswith('0'):
        digits = '49' + digits[1:]
    return digits


def dedupe_key(vertical: str, email: str | None, phone: str) -> str:
    raw = f"{vertical}|{(email or '').strip().lower()}|{normalize_phone(phone)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def find_duplicate(db: Session, key: str, days: int = 90) -> Lead | None:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return db.query(Lead).filter(Lead.dedupe_key == key, Lead.created_at >= cutoff).order_by(Lead.created_at.desc()).first()


def record_event(db: Session, lead_id: int | None, event_type: str, actor: str | None = None, payload: dict | None = None):
    db.add(LeadEvent(lead_id=lead_id, event_type=event_type, actor=actor, payload_json=json.dumps(payload or {}, ensure_ascii=False)))


def record_consents(db: Session, lead: Lead):
    contact_snapshot = public_contact_text() if lead.consent_text_version == PUBLIC_CONTACT_VERSION else None
    for kind, granted in [('marketing', lead.consent_marketing), ('partner_sharing', lead.consent_partner_sharing)]:
        db.add(ConsentRecord(
            lead_id=lead.id, consent_type=kind, granted=granted,
            text_version=lead.consent_text_version, ip_address=lead.consent_ip,
            user_agent=lead.consent_user_agent, source=lead.source_type,
            text_snapshot=contact_snapshot if kind == 'marketing' else None,
            context_json=json.dumps({'stage': 'public_funnel'}, ensure_ascii=False),
        ))


async def refresh_lead_intelligence(db: Session, lead: Lead, payload_like):
    pv = None
    if lead.vertical == 'balcony_pv':
        try:
            pv = await calculate_pv(payload_like)
        except Exception:
            pv = None
    if pv:
        lead.latitude = pv['latitude']; lead.longitude = pv['longitude']
        lead.pv_yield_kwh = pv['pv_yield_kwh']; lead.annual_savings_eur = pv['annual_savings_eur']
    routing = route_lead(db, lead)
    try:
        project = json.loads(lead.project_payload or '{}')
    except Exception:
        project = {}
    score_data = {
        'phone': lead.phone, 'email': lead.email, 'street': lead.street, 'house_number': lead.house_number,
        'installation_location': lead.installation_location, 'orientation': lead.orientation, 'shading': lead.shading,
        'owner_status': lead.owner_status, 'purchase_timeframe': lead.purchase_timeframe,
        'wants_installation': lead.wants_installation, 'product_preference': lead.product_preference,
        'contact_time': lead.contact_time, 'review_confirmed': bool(project.get('review_confirmed')),
        'geo_fit_score': lead.geo_fit_score,
    }
    lead.lead_score = lead_score(score_data) if lead.vertical == 'balcony_pv' else 50
    return routing


async def create_lead_from_payload(db: Session, payload, request, *, source_type: str, source_id: str | None = None, actor: str = 'public'):
    data = payload.model_dump() if hasattr(payload, 'model_dump') else dict(payload)
    vertical = data.get('vertical') or 'balcony_pv'
    external_id = data.get('external_id')
    if external_id:
        existing = (db.query(Lead)
            .filter(Lead.source_type == source_type, Lead.source_id == (source_id or data.get('source_id')), Lead.external_id == external_id)
            .order_by(Lead.created_at.desc()).first())
        if existing:
            record_event(db, existing.id, 'ingestion_replayed', actor, {'external_id': external_id})
            db.commit(); return existing

    email = str(data.get('email') or '')
    key = dedupe_key(vertical, email, data.get('phone',''))
    duplicate = find_duplicate(db, key)
    project_payload = dict(data.get('project_payload') or {})
    if 'review_confirmed' in data:
        project_payload['review_confirmed'] = bool(data.get('review_confirmed'))

    client_account_id = None
    client_code = data.get('client_code')
    if client_code:
        client = db.query(ClientAccount).filter(ClientAccount.code == client_code, ClientAccount.active == True).first()  # noqa: E712
        if client:
            client_account_id = client.id

    lead = Lead(
        first_name=data['first_name'], last_name=data.get('last_name') or '', email=email, phone=data['phone'],
        postal_code=data['postal_code'], city=data.get('city') or '', street=data.get('street'), house_number=data.get('house_number'),
        vertical=vertical, source_type=source_type, source_id=source_id or data.get('source_id'), external_id=data.get('external_id'),
        dedupe_key=key, duplicate_of_id=duplicate.id if duplicate else None, referrer=data.get('referrer'), landing_path=data.get('landing_path'),
        project_payload=json.dumps(project_payload, ensure_ascii=False), public_token=secrets.token_urlsafe(24),
        funnel_session_id=data.get('funnel_session_id'),
        installation_location=data.get('installation_location','balcony'), orientation=data.get('orientation','unknown'), shading=data.get('shading','unknown'),
        owner_status=data.get('owner_status','unknown'), annual_consumption_kwh=data.get('annual_consumption_kwh',2500),
        electricity_price_eur_kwh=data.get('electricity_price_eur_kwh',0.34), wants_installation=data.get('wants_installation',False),
        purchase_timeframe=data.get('purchase_timeframe','information'), product_preference=data.get('product_preference'), contact_time=data.get('contact_time'),
        lead_score=0, status='duplicate' if duplicate else 'new',
        utm_source=data.get('utm_source'), utm_medium=data.get('utm_medium'), utm_campaign=data.get('utm_campaign'), utm_content=data.get('utm_content'),
        cost_eur=float(data.get('cost_eur') or 0),
        lead_origin=data.get('lead_origin') or ('client_supplied' if client_account_id else 'owned'), client_account_id=client_account_id,
        setter_status='queued', setter_name=data.get('setter_name'),
        consent_marketing=data.get('consent_marketing',False), consent_partner_sharing=data.get('consent_partner_sharing',False),
        consent_text_version=data.get('consent_text_version',PUBLIC_CONTACT_VERSION), consent_ip=client_ip(request),
        consent_user_agent=request.headers.get('user-agent'),
    )
    db.add(lead); db.flush()

    # Link anonymous funnel events to the lead only after the user voluntarily submits.
    # Before this point the funnel event stream contains no contact details.
    session_id = data.get('funnel_session_id')
    if session_id:
        db.query(FunnelEvent).filter(
            FunnelEvent.session_id == session_id, FunnelEvent.lead_id.is_(None)
        ).update({FunnelEvent.lead_id: lead.id}, synchronize_session=False)

    routing = await refresh_lead_intelligence(db, lead, payload)

    if session_id:
        db.add(FunnelEvent(
            session_id=session_id, event_type='lead_submitted',
            source_id=source_id or data.get('source_id'),
            utm_source=data.get('utm_source'), utm_medium=data.get('utm_medium'),
            utm_campaign=data.get('utm_campaign'), utm_content=data.get('utm_content'),
            landing_path=data.get('landing_path'), referrer=data.get('referrer'),
            market_code=lead.market_code, vertical_code=vertical, lead_id=lead.id,
        ))
    record_consents(db, lead)
    record_event(db, lead.id, 'lead_created', actor, {
        'source_type': source_type, 'duplicate_of_id': lead.duplicate_of_id,
        'market_code': lead.market_code, 'routing': routing,
    })
    db.commit(); db.refresh(lead)
    return lead
