"""Import opt-in client leads into SolarLead Setter Ops.
CSV columns: first_name,last_name,email,phone,postal_code,city,external_id,contact_permission
Optional: orientation,shading,owner_status,purchase_timeframe,notes

Important: only import leads the client is permitted to contact / have qualified.
"""
import argparse, csv, json, hashlib, re
from pathlib import Path
from app.db import SessionLocal
from app.models import ClientAccount, Lead, LeadEvent
from app.services.leads import dedupe_key
from app.routing import route_lead

p=argparse.ArgumentParser()
p.add_argument('client_code')
p.add_argument('csv_path')
p.add_argument('--vertical', default='generic')
a=p.parse_args()

db=SessionLocal(); created=0; skipped=0
try:
    client=db.query(ClientAccount).filter(ClientAccount.code==a.client_code, ClientAccount.active==True).first()
    if not client: raise SystemExit(f'Client {a.client_code} nicht gefunden. create_client_account.py zuerst ausführen.')
    with Path(a.csv_path).open(newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            ext=(r.get('external_id') or '').strip() or None
            if ext and db.query(Lead).filter(Lead.client_account_id==client.id,Lead.external_id==ext).first():
                skipped+=1; continue
            phone=(r.get('phone') or '').strip()
            allowed=(r.get('contact_permission') or '').strip().lower() in {'1','true','yes','ja','y'}
            if not phone or not allowed: skipped+=1; continue
            lead=Lead(
                first_name=(r.get('first_name') or '').strip() or 'Unbekannt', last_name=(r.get('last_name') or '').strip(),
                email=(r.get('email') or '').strip(), phone=phone, postal_code=(r.get('postal_code') or '').strip(), city=(r.get('city') or '').strip(),
                vertical=a.vertical, source_type='client_csv', source_id=a.client_code, external_id=ext,
                dedupe_key=dedupe_key(a.vertical,(r.get('email') or ''),phone), project_payload=json.dumps({'client_notes':r.get('notes') or ''},ensure_ascii=False),
                installation_location='unknown', orientation=r.get('orientation') or 'unknown', shading=r.get('shading') or 'unknown', owner_status=r.get('owner_status') or 'unknown',
                purchase_timeframe=r.get('purchase_timeframe') or 'information', wants_installation=False,
                lead_score=50,status='new',lead_origin='client_supplied',client_account_id=client.id,setter_status='queued',
                consent_marketing=True,consent_partner_sharing=False,consent_text_version='client_provided',
            )
            db.add(lead);db.flush(); route_lead(db,lead)
            db.add(LeadEvent(lead_id=lead.id,event_type='client_csv_imported',actor=f'client:{client.code}',payload_json=json.dumps({'client_code':client.code})))
            created+=1
        db.commit()
    print(f'Import fertig: erstellt={created}, übersprungen={skipped}')
finally:
    db.close()
