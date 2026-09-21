import csv
import io
import json
from collections import defaultdict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AcquisitionCampaign, AdminUser, ClientAccount, ConsentRecord, FunnelEvent, Lead, Market, Partner, SalesRep, Territory, Vertical
from ..schemas import AcquisitionCampaignCreate, LeadDetailOut, LeadOut, LeadSaleUpdate, LeadStatusUpdate, QualificationUpdate, SetterUpdate, SourceAnalytics
from ..security import get_current_admin, require_csrf
from ..services.leads import record_event
from ..consent_texts import PARTNER_TRANSFER_VERSION, partner_transfer_text

router = APIRouter(prefix='/api/admin', tags=['admin'], dependencies=[Depends(get_current_admin)])
ALLOWED = {'new','duplicate','contacted','qualified','sales_ready','appointment','sold','won','lost'}

@router.get('/leads', response_model=list[LeadOut])
def list_leads(market: str | None = None, vertical: str | None = None, db: Session = Depends(get_db)):
    q=db.query(Lead)
    if market: q=q.filter(Lead.market_code==market)
    if vertical: q=q.filter(Lead.vertical==vertical)
    return q.order_by(Lead.lead_score.desc(), Lead.created_at.desc()).all()

@router.get('/leads/{lead_id}', response_model=LeadDetailOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead: raise HTTPException(status_code=404, detail='Lead nicht gefunden')
    return lead

@router.patch('/leads/{lead_id}/status', response_model=LeadOut, dependencies=[Depends(require_csrf)])
def update_status(lead_id: int, payload: LeadStatusUpdate, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if payload.status not in ALLOWED: raise HTTPException(status_code=400, detail='Ungültiger Status')
    lead = db.get(Lead, lead_id)
    if not lead: raise HTTPException(status_code=404, detail='Lead nicht gefunden')
    lead.status = payload.status
    record_event(db, lead.id, 'status_changed', user.email, {'status': payload.status})
    db.commit(); db.refresh(lead); return lead

@router.patch('/leads/{lead_id}/qualification', response_model=LeadDetailOut, dependencies=[Depends(require_csrf)])
def update_qualification(lead_id: int, payload: QualificationUpdate, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if payload.status not in ALLOWED: raise HTTPException(status_code=400, detail='Ungültiger Status')
    lead = db.get(Lead, lead_id)
    if not lead: raise HTTPException(status_code=404, detail='Lead nicht gefunden')
    lead.qualification_notes = json.dumps(payload.model_dump(), ensure_ascii=False)
    lead.status = payload.status
    record_event(db, lead.id, 'qualification_updated', user.email, payload.model_dump())
    db.commit(); db.refresh(lead); return lead

@router.get('/analytics/sources', response_model=list[SourceAnalytics])
def source_analytics(db: Session = Depends(get_db)):
    rows = db.query(Lead).all()
    agg = defaultdict(lambda: {'leads':0,'hot':0,'qualified':0,'won':0,'cost':0.0,'revenue':0.0})
    for l in rows:
        key = l.source_id or l.utm_source or l.source_type or 'unknown'
        a=agg[key]; a['leads']+=1; a['hot']+=int(l.lead_score>=80)
        a['qualified']+=int(l.status in {'qualified','appointment','sold','won'}); a['won']+=int(l.status=='won')
        a['cost']+=l.cost_eur or 0; a['revenue']+=l.revenue_eur or 0
    out=[]
    for source,a in sorted(agg.items(), key=lambda x:x[1]['leads'], reverse=True):
        out.append(SourceAnalytics(source=source, leads=a['leads'], hot=a['hot'], qualified=a['qualified'], won=a['won'],
            cost_eur=round(a['cost'],2), revenue_eur=round(a['revenue'],2),
            cpl=round(a['cost']/a['leads'],2) if a['leads'] else None,
            qualified_cpl=round(a['cost']/a['qualified'],2) if a['qualified'] else None))
    return out


@router.get('/routing')
def routing_overview(db: Session = Depends(get_db)):
    partners={p.id:p.name for p in db.query(Partner).all()}
    reps={r.id:r.name for r in db.query(SalesRep).all()}
    return {
        'markets':[{'code':m.code,'name':m.name,'state_code':m.state_code,'building_provider':m.building_provider,'active':m.active} for m in db.query(Market).order_by(Market.name).all()],
        'verticals':[{'code':v.code,'name':v.name,'active':v.active} for v in db.query(Vertical).order_by(Vertical.name).all()],
        'partners':[{'id':p.id,'name':p.name,'slug':p.slug,'active':p.active} for p in db.query(Partner).order_by(Partner.name).all()],
        'sales_reps':[{'id':r.id,'name':r.name,'partner_id':r.partner_id,'partner':partners.get(r.partner_id),'active':r.active} for r in db.query(SalesRep).order_by(SalesRep.name).all()],
        'territories':[{'id':t.id,'name':t.name,'market_code':t.market_code,'vertical_code':t.vertical_code,'partner':partners.get(t.partner_id),'sales_rep':reps.get(t.sales_rep_id),'priority':t.priority,'max_leads_per_day':t.max_leads_per_day,'active':t.active} for t in db.query(Territory).order_by(Territory.market_code,Territory.priority.desc()).all()],
    }

@router.get('/leads.csv')
def export_leads(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    buf=io.StringIO(); w=csv.writer(buf)
    w.writerow(['id','created_at','name','email','phone','postal_code','city','vertical','market_code','geo_fit_score','source_type','source_id','score','status','assigned_partner_id','assigned_sales_rep_id','cost_eur','revenue_eur'])
    for l in leads:
        w.writerow([l.id,l.created_at.isoformat(),f'{l.first_name} {l.last_name}',l.email,l.phone,l.postal_code,l.city,l.vertical,l.market_code,l.geo_fit_score,l.source_type,l.source_id,l.lead_score,l.status,l.assigned_partner_id,l.assigned_sales_rep_id,l.cost_eur,l.revenue_eur])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type='text/csv', headers={'Content-Disposition':'attachment; filename=solarlead-leads.csv'})


@router.get('/acquisition/campaigns')
def acquisition_campaigns(db: Session = Depends(get_db)):
    rows=db.query(AcquisitionCampaign).filter(AcquisitionCampaign.active==True).order_by(AcquisitionCampaign.created_at).all()  # noqa: E712
    return [{
        'id':c.id,'code':c.code,'name':c.name,'channel':c.channel,'market_code':c.market_code,'vertical_code':c.vertical_code,
        'source_id':c.source_id,'utm_source':c.utm_source,'utm_medium':c.utm_medium,'utm_campaign':c.utm_campaign,
        'query':f"src={c.source_id}&utm_source={c.utm_source}&utm_medium={c.utm_medium}&utm_campaign={c.utm_campaign}" + (f"&market={c.market_code}" if c.market_code else '')
    } for c in rows]


@router.get('/acquisition/performance')
def acquisition_performance(db: Session = Depends(get_db)):
    campaigns=db.query(AcquisitionCampaign).filter(AcquisitionCampaign.active==True).order_by(AcquisitionCampaign.name).all()  # noqa: E712
    out=[]
    for c in campaigns:
        def sessions(event_type: str) -> int:
            return (db.query(FunnelEvent.session_id)
                .filter(FunnelEvent.source_id==c.source_id, FunnelEvent.event_type==event_type)
                .distinct().count())

        leads=db.query(Lead).filter(Lead.source_id==c.source_id).all()
        qualified=sum(1 for l in leads if l.status in {'qualified','sales_ready','appointment','sold','won'})
        appointments=sum(1 for l in leads if l.status in {'appointment','sold','won'})
        sold=sum(1 for l in leads if l.status in {'sold','won'})
        revenue=round(sum((l.revenue_eur or 0) for l in leads),2)
        views=sessions('landing_view')
        starts=sessions('funnel_started')
        results=sessions('pv_result_viewed')
        contact=sessions('contact_step_viewed')
        lead_count=len(leads)
        out.append({
            'code':c.code,'name':c.name,'channel':c.channel,'market_code':c.market_code,'source_id':c.source_id,
            'views':views,'starts':starts,'results':results,'contact_views':contact,'leads':lead_count,
            'qualified':qualified,'appointments':appointments,'sold':sold,'revenue_eur':revenue,
            'start_rate':round(starts/views*100,1) if views else None,
            'lead_rate':round(lead_count/views*100,1) if views else None,
            'qualified_rate':round(qualified/lead_count*100,1) if lead_count else None,
        })
    return out

@router.post('/acquisition/campaigns', dependencies=[Depends(require_csrf)])
def create_acquisition_campaign(payload: AcquisitionCampaignCreate, db: Session = Depends(get_db)):
    if db.query(AcquisitionCampaign).filter(AcquisitionCampaign.code==payload.code).first():
        raise HTTPException(status_code=409,detail='Campaign-Code existiert bereits')
    c=AcquisitionCampaign(code=payload.code,name=payload.name,channel=payload.channel,market_code=payload.market_code,
        vertical_code=payload.vertical_code,source_id=payload.code,utm_source=payload.channel,utm_medium='organic',utm_campaign=payload.code,active=True)
    db.add(c);db.commit();db.refresh(c);return {'id':c.id,'code':c.code}


@router.get('/setter/clients')
def setter_clients(db: Session = Depends(get_db)):
    clients=db.query(ClientAccount).filter(ClientAccount.active==True).order_by(ClientAccount.name).all()  # noqa: E712
    out=[]
    for c in clients:
        total=db.query(Lead).filter(Lead.client_account_id==c.id).count()
        queued=db.query(Lead).filter(Lead.client_account_id==c.id,Lead.setter_status.in_(['queued','callback'])).count()
        qualified=db.query(Lead).filter(Lead.client_account_id==c.id,Lead.setter_status.in_(['qualified','appointment'])).count()
        try: script=json.loads(c.qualification_script_json or '[]')
        except Exception: script=[]
        out.append({'id':c.id,'code':c.code,'name':c.name,'vertical_code':c.vertical_code,'total':total,'queued':queued,'qualified':qualified,'script':script})
    return out


@router.get('/setter/queue', response_model=list[LeadOut])
def setter_queue(client_id: int | None = None, origin: str | None = None, db: Session = Depends(get_db)):
    q=db.query(Lead).filter(Lead.status.notin_(['sold','won','lost','duplicate']))
    if client_id: q=q.filter(Lead.client_account_id==client_id)
    if origin: q=q.filter(Lead.lead_origin==origin)
    return q.order_by(Lead.lead_score.desc(),Lead.created_at.asc()).all()


@router.patch('/leads/{lead_id}/setter', response_model=LeadDetailOut, dependencies=[Depends(require_csrf)])
def setter_update(lead_id: int, payload: SetterUpdate, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    lead=db.get(Lead,lead_id)
    if not lead: raise HTTPException(status_code=404,detail='Lead nicht gefunden')
    lead.setter_attempts=(lead.setter_attempts or 0)+1
    lead.setter_name=payload.setter_name.strip()
    lead.setter_outcome=payload.outcome
    mapping={'qualified':'qualified','appointment':'appointment','callback':'contacted','not_interested':'lost','invalid':'lost','unreachable':'contacted'}
    lead.setter_status=payload.outcome
    lead.status=mapping.get(payload.outcome,lead.status)
    data=payload.model_dump()

    if payload.partner_consent_granted:
        if not payload.partner_id:
            raise HTTPException(status_code=400, detail='Für Partnerweitergabe muss ein konkreter Partner ausgewählt werden.')
        partner=db.get(Partner,payload.partner_id)
        if not partner or not partner.active:
            raise HTTPException(status_code=400, detail='Ausgewählter Partner ist nicht aktiv.')
        lead.consent_partner_sharing=True
        lead.partner_consent_granted=True
        lead.partner_consent_partner_id=partner.id
        lead.partner_consent_partner_name=partner.name
        lead.partner_consent_timestamp=datetime.utcnow()
        lead.partner_consent_setter=payload.setter_name.strip()
        db.add(ConsentRecord(
            lead_id=lead.id, consent_type='partner_sharing', granted=True,
            text_version=PARTNER_TRANSFER_VERSION, ip_address=None, user_agent=None,
            source='setter_call', text_snapshot=partner_transfer_text(partner.name),
            context_json=json.dumps({'partner_id': partner.id, 'partner_name': partner.name, 'setter': payload.setter_name.strip()}, ensure_ascii=False),
        ))
        record_event(db,lead.id,'partner_transfer_consent',payload.setter_name,{'partner_id':partner.id,'partner_name':partner.name})

    lead.qualification_notes=json.dumps(data,ensure_ascii=False)
    record_event(db,lead.id,'setter_qualification',payload.setter_name,data)
    db.commit();db.refresh(lead);return lead


@router.get('/marketplace/ready', response_model=list[LeadOut])
def sale_ready_leads(db: Session = Depends(get_db)):
    # Legacy endpoint kept read-only for compatibility. Commercial delivery happens in Buyer Ops.
    return (db.query(Lead)
        .filter(
            Lead.lead_origin=='owned',
            Lead.status.in_(['qualified','sales_ready','appointment']),
            Lead.partner_consent_granted==True,  # noqa: E712
            Lead.partner_consent_partner_id.isnot(None),
        )
        .order_by(Lead.lead_score.desc(),Lead.created_at.asc()).all())


@router.patch('/leads/{lead_id}/sale', response_model=LeadOut, dependencies=[Depends(require_csrf)])
def sell_lead(lead_id: int, payload: LeadSaleUpdate, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    raise HTTPException(status_code=410, detail='V0.6: Direkter Verkauf ist deaktiviert. Bitte Buyer Ops /api/admin/buyers/deliveries verwenden.')
