from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import ApiClient
from ..schemas import IngestLeadCreate, LeadOut
from ..security import require_api_client
from ..services.leads import create_lead_from_payload

router = APIRouter(prefix='/api/v1', tags=['ingestion'])

@router.post('/leads', response_model=LeadOut)
async def ingest_lead(
    payload: IngestLeadCreate,
    request: Request,
    client: ApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    if not payload.consent_marketing or not payload.consent_partner_sharing:
        raise HTTPException(status_code=400, detail='Einwilligungsnachweis fehlt')
    source_id = payload.source_id or client.source_id
    return await create_lead_from_payload(db, payload, request, source_type=payload.source_type or 'partner_api', source_id=source_id, actor=f'api:{client.name}')


@router.post('/client-leads', response_model=LeadOut)
async def ingest_client_lead(
    payload: IngestLeadCreate,
    request: Request,
    client: ApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    if not payload.client_code:
        raise HTTPException(status_code=400, detail='client_code fehlt')
    if not payload.consent_marketing:
        raise HTTPException(status_code=400, detail='Kontakt-/Telefon-Einwilligungsnachweis fehlt')
    normalized = payload.model_copy(update={'lead_origin':'client_supplied'})
    source_id = payload.source_id or client.source_id or payload.client_code
    return await create_lead_from_payload(db, normalized, request, source_type='client_api', source_id=source_id, actor=f'client_api:{client.name}')
