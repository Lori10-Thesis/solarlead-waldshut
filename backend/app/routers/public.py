from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import FunnelEvent, Lead
from ..pv import calculate_pv
from ..schemas import FunnelEventCreate, LeadCreate, OptionalAddressUpdate, PublicLeadReceipt, PvRequest, PvResult
from ..services.leads import create_lead_from_payload, record_event, refresh_lead_intelligence

router = APIRouter(tags=['public'])


ALLOWED_FUNNEL_EVENTS = {
    'landing_view', 'funnel_started', 'pv_result_viewed',
    'contact_step_viewed', 'review_viewed'
}


@router.post('/api/funnel/events')
def funnel_event(payload: FunnelEventCreate, db: Session = Depends(get_db)):
    if payload.event_type not in ALLOWED_FUNNEL_EVENTS:
        raise HTTPException(status_code=400, detail='Unbekanntes Funnel-Event')

    # De-dupe identical browser events for the same session. This keeps page reloads
    # from inflating the organic conversion funnel.
    exists = db.query(FunnelEvent).filter(
        FunnelEvent.session_id == payload.session_id,
        FunnelEvent.event_type == payload.event_type,
    ).first()
    if exists:
        return {'ok': True, 'deduped': True}

    db.add(FunnelEvent(**payload.model_dump()))
    db.commit()
    return {'ok': True, 'deduped': False}

@router.post('/api/pv/calculate', response_model=PvResult)
async def pv_calculate(payload: PvRequest):
    return await calculate_pv(payload)


def receipt(lead: Lead) -> PublicLeadReceipt:
    return PublicLeadReceipt(id=lead.id, status=lead.status, market_code=lead.market_code,
        lead_score=lead.lead_score, geo_fit_score=lead.geo_fit_score,
        assigned=bool(lead.assigned_partner_id or lead.assigned_sales_rep_id), public_token=lead.public_token)

@router.post('/api/leads', response_model=PublicLeadReceipt)
async def create_public_lead(payload: LeadCreate, request: Request, db: Session = Depends(get_db)):
    if not payload.review_confirmed:
        raise HTTPException(status_code=400, detail='Bitte Angaben vor dem Absenden bestätigen.')
    if not payload.consent_marketing:
        raise HTTPException(status_code=400, detail='Kontakt-Einwilligung fehlt')
    lead=await create_lead_from_payload(db,payload,request,source_type='organic_web',source_id=payload.source_id,actor='public_funnel')
    return receipt(lead)

@router.post('/api/widget/leads', response_model=PublicLeadReceipt)
async def create_widget_lead(payload: LeadCreate, request: Request, db: Session = Depends(get_db)):
    if not payload.review_confirmed or not payload.consent_marketing:
        raise HTTPException(status_code=400, detail='Bestätigung/Kontakt-Einwilligung fehlt')
    source_id=payload.source_id or request.query_params.get('source') or 'unknown_widget'
    lead=await create_lead_from_payload(db,payload,request,source_type='embed_widget',source_id=source_id,actor='widget')
    return receipt(lead)

@router.patch('/api/leads/{public_token}/address', response_model=PublicLeadReceipt)
async def optional_address(public_token: str, payload: OptionalAddressUpdate, request: Request, db: Session = Depends(get_db)):
    lead=db.query(Lead).filter(Lead.public_token==public_token).first()
    if not lead: raise HTTPException(status_code=404, detail='Anfrage nicht gefunden')
    lead.street=payload.street.strip(); lead.house_number=payload.house_number.strip()
    if payload.city.strip(): lead.city=payload.city.strip()
    class PvLike:
        postal_code=lead.postal_code; city=lead.city; street=lead.street; house_number=lead.house_number
        orientation=lead.orientation; shading=lead.shading; annual_consumption_kwh=lead.annual_consumption_kwh
        electricity_price_eur_kwh=lead.electricity_price_eur_kwh
    await refresh_lead_intelligence(db, lead, PvLike())
    record_event(db, lead.id, 'optional_address_added', 'public_funnel', {'street_supplied': True})
    db.commit(); db.refresh(lead); return receipt(lead)
