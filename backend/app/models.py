from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class Vertical(Base):
    __tablename__ = 'verticals'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    funnel_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    scoring_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Market(Base):
    __tablename__ = 'markets'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    country_code: Mapped[str] = mapped_column(String(8), default='DE')
    state_code: Mapped[str] = mapped_column(String(16), index=True)
    center_lat: Mapped[float] = mapped_column(Float)
    center_lon: Mapped[float] = mapped_column(Float)
    bbox_west: Mapped[float] = mapped_column(Float)
    bbox_south: Mapped[float] = mapped_column(Float)
    bbox_east: Mapped[float] = mapped_column(Float)
    bbox_north: Mapped[float] = mapped_column(Float)
    postal_prefixes_json: Mapped[str] = mapped_column(Text, default='[]')
    building_provider: Mapped[str] = mapped_column(String(80), default='unknown')
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Partner(Base):
    __tablename__ = 'partners'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # V0.6: internal routing partner vs. real commercial buyer
    partner_type: Mapped[str] = mapped_column(String(40), default='internal', index=True)  # internal | buyer
    buyer_ready: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PartnerBuyRule(Base):
    __tablename__ = 'partner_buy_rules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(Integer, index=True)
    vertical_code: Mapped[str] = mapped_column(String(80), default='balcony_pv', index=True)
    market_code: Mapped[str] = mapped_column(String(80), index=True)
    lead_price_eur: Mapped[float] = mapped_column(Float, default=0.0)
    min_lead_score: Mapped[int] = mapped_column(Integer, default=0)
    daily_cap: Mapped[int] = mapped_column(Integer, default=20)
    exclusive: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LeadDelivery(Base):
    __tablename__ = 'lead_deliveries'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)
    partner_id: Mapped[int] = mapped_column(Integer, index=True)
    buy_rule_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    market_code: Mapped[str] = mapped_column(String(80), index=True)
    vertical_code: Mapped[str] = mapped_column(String(80), index=True)
    price_eur: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(40), default='delivered', index=True)  # delivered | accepted | rejected | won | lost | cancelled
    offered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    feedback_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    feedback_outcome: Mapped[str | None] = mapped_column(String(80), nullable=True)
    order_value_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    partner_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SalesRep(Base):
    __tablename__ = 'sales_reps'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Territory(Base):
    __tablename__ = 'territories'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    vertical_code: Mapped[str] = mapped_column(String(80), index=True)
    market_code: Mapped[str] = mapped_column(String(80), index=True)
    partner_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    sales_rep_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    postal_prefixes_json: Mapped[str] = mapped_column(Text, default='[]')
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)
    max_leads_per_day: Mapped[int] = mapped_column(Integer, default=999)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Lead(Base):
    __tablename__ = 'leads'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120), default='')
    email: Mapped[str] = mapped_column(String(255), default='', index=True)
    phone: Mapped[str] = mapped_column(String(80), index=True)

    postal_code: Mapped[str] = mapped_column(String(20), index=True)
    city: Mapped[str] = mapped_column(String(120), default='', index=True)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    house_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    vertical: Mapped[str] = mapped_column(String(80), default='balcony_pv', index=True)
    market_code: Mapped[str] = mapped_column(String(80), default='unassigned', index=True)
    geo_fit_score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(80), default='organic_web', index=True)
    source_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    duplicate_of_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    landing_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    project_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_token: Mapped[str | None] = mapped_column(String(160), nullable=True, unique=True, index=True)
    funnel_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    installation_location: Mapped[str] = mapped_column(String(40), default='balcony')
    orientation: Mapped[str] = mapped_column(String(20), default='unknown')
    shading: Mapped[str] = mapped_column(String(20), default='unknown')
    owner_status: Mapped[str] = mapped_column(String(20), default='unknown')
    annual_consumption_kwh: Mapped[int] = mapped_column(Integer, default=2500)
    electricity_price_eur_kwh: Mapped[float] = mapped_column(Float, default=0.34)
    wants_installation: Mapped[bool] = mapped_column(Boolean, default=False)
    purchase_timeframe: Mapped[str] = mapped_column(String(30), default='information')
    product_preference: Mapped[str | None] = mapped_column(String(60), nullable=True)
    contact_time: Mapped[str | None] = mapped_column(String(40), nullable=True)

    pv_yield_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_savings_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    lead_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    status: Mapped[str] = mapped_column(String(30), default='new', index=True)

    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(160), nullable=True)

    cost_eur: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_eur: Mapped[float] = mapped_column(Float, default=0.0)
    assigned_partner: Mapped[str | None] = mapped_column(String(160), nullable=True)
    assigned_partner_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    assigned_sales_rep_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)


    # V0.5: commercial origin + setter operations
    lead_origin: Mapped[str] = mapped_column(String(40), default='owned', index=True)  # owned | client_supplied
    client_account_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    setter_status: Mapped[str] = mapped_column(String(40), default='queued', index=True)
    setter_attempts: Mapped[int] = mapped_column(Integer, default=0)
    setter_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    setter_outcome: Mapped[str | None] = mapped_column(String(120), nullable=True)

    consent_marketing: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_partner_sharing: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_text_version: Mapped[str] = mapped_column(String(40), default='v2')
    consent_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    consent_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consent_user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    partner_consent_granted: Mapped[bool] = mapped_column(Boolean, default=False)
    partner_consent_partner_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    partner_consent_partner_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    partner_consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    partner_consent_setter: Mapped[str | None] = mapped_column(String(160), nullable=True)
    qualification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AcquisitionCampaign(Base):
    __tablename__ = 'acquisition_campaigns'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    channel: Mapped[str] = mapped_column(String(80), index=True)  # whatsapp, facebook_group, local_qr, referral, organic
    market_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    vertical_code: Mapped[str] = mapped_column(String(80), default='balcony_pv', index=True)
    source_id: Mapped[str] = mapped_column(String(160), index=True)
    utm_source: Mapped[str] = mapped_column(String(120), default='organic')
    utm_medium: Mapped[str] = mapped_column(String(120), default='organic')
    utm_campaign: Mapped[str] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ClientAccount(Base):
    __tablename__ = 'client_accounts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    vertical_code: Mapped[str] = mapped_column(String(80), default='generic', index=True)
    qualification_script_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    callback_target: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FunnelEvent(Base):
    __tablename__ = 'funnel_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(120), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    utm_content: Mapped[str | None] = mapped_column(String(160), nullable=True)
    landing_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    market_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    vertical_code: Mapped[str] = mapped_column(String(80), default='balcony_pv', index=True)
    lead_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class GeoCell(Base):
    __tablename__ = 'geo_cells'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    market_code: Mapped[str] = mapped_column(String(80), default='waldshut', index=True)
    vertical_code: Mapped[str] = mapped_column(String(80), default='balcony_pv', index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    potential_score: Mapped[int] = mapped_column(Integer, index=True)
    housing_density_score: Mapped[int] = mapped_column(Integer)
    building_fit_score: Mapped[int] = mapped_column(Integer)
    solar_score: Mapped[int] = mapped_column(Integer)
    market_gap_score: Mapped[int] = mapped_column(Integer)
    campaign_score: Mapped[int] = mapped_column(Integer)


class AdminUser(Base):
    __tablename__ = 'admin_users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    display_name: Mapped[str] = mapped_column(String(160), default='Admin')
    role: Mapped[str] = mapped_column(String(40), default='admin')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ApiClient(Base):
    __tablename__ = 'api_clients'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    source_id: Mapped[str] = mapped_column(String(160), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LeadEvent(Base):
    __tablename__ = 'lead_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    actor: Mapped[str | None] = mapped_column(String(160), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ConsentRecord(Base):
    __tablename__ = 'consent_records'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)
    consent_type: Mapped[str] = mapped_column(String(80), index=True)
    granted: Mapped[bool] = mapped_column(Boolean)
    text_version: Mapped[str] = mapped_column(String(40))
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str | None] = mapped_column(String(160), nullable=True)
    text_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class IntegrationEvent(Base):
    __tablename__ = 'integration_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    integration: Mapped[str] = mapped_column(String(80), index=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
