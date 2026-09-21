import hashlib
import hmac
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from ..config import get_settings
from ..db import get_db
from ..models import IntegrationEvent

router=APIRouter(prefix='/api/webhooks', tags=['webhooks'])
settings=get_settings()

@router.get('/meta')
def meta_verify(
    hub_mode: str | None = Query(None, alias='hub.mode'),
    hub_verify_token: str | None = Query(None, alias='hub.verify_token'),
    hub_challenge: str | None = Query(None, alias='hub.challenge'),
):
    if hub_mode == 'subscribe' and settings.meta_verify_token and hub_verify_token == settings.meta_verify_token:
        return int(hub_challenge or '0')
    raise HTTPException(status_code=403, detail='Meta-Verifikation fehlgeschlagen')

@router.post('/meta')
async def meta_webhook(request: Request, db: Session = Depends(get_db)):
    raw=await request.body()
    if settings.meta_app_secret:
        signature=request.headers.get('x-hub-signature-256','')
        expected='sha256='+hmac.new(settings.meta_app_secret.encode(),raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail='Meta-Signatur ungültig')
    payload=json.loads(raw or b'{}')
    db.add(IntegrationEvent(integration='meta_leadgen', external_id=None, payload_json=json.dumps(payload,ensure_ascii=False)))
    db.commit()
    return {'received': True, 'note': 'Webhook gespeichert; Lead-Abruf wird im nächsten Adapter-Schritt aktiviert.'}
