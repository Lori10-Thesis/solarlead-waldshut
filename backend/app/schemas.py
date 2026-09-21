from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class PvRequest(BaseModel):
    postal_code: str = Field(min_length=4, max_length=10)
    city: str = ''
    street: str | None = None
    house_number: str | None = None
    orientation: str
    shading: str
    annual_consumption_kwh: int = Field(ge=500, le=20000)
    electricity_price_eur_kwh: float = Field(ge=0.05, le=1.5)


class PvResult(BaseModel):
    latitude: float
    longitude: float
    pv_yield_kwh: float
    annual_savings_eur: float
    ten_year_savings_eur: float
    potential_score: int
    calculation_source: str


class LeadCreate(PvRequest):
    vertical: str = 'balcony_pv'
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = ''
    email: EmailStr | None = None
    phone: str = Field(min_length=6, max_length=80)
    installation_location: str = 'balcony'
    owner_status: str
    wants_installation: bool
    purchase_timeframe: str
    product_preference: str | None = None
    contact_time: str | None = None
    review_confirmed: bool = False
    consent_marketing: bool
    consent_partner_sharing: bool
    consent_text_version: str = 'v3_public_contact'
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    source_id: str | None = None
    funnel_session_id: str | None = Field(default=None, max_length=120)
    landing_path: str | None = Field(default=None, max_length=300)
    referrer: str | None = Field(default=None, max_length=500)


class FunnelEventCreate(BaseModel):
    session_id: str = Field(min_length=8, max_length=120)
    event_type: str = Field(min_length=2, max_length=80)
    source_id: str | None = Field(default=None, max_length=160)
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=160)
    utm_content: str | None = Field(default=None, max_length=160)
    landing_path: str | None = Field(default=None, max_length=300)
    referrer: str | None = Field(default=None, max_length=500)
    market_code: str | None = Field(default=None, max_length=80)
    vertical_code: str = Field(default='balcony_pv', max_length=80)


class IngestLeadCreate(BaseModel):
    vertical: str = 'balcony_pv'
    source_type: str = 'partner_api'
    source_id: str | None = None
    external_id: str | None = None
    first_name: str
    last_name: str = ''
    email: EmailStr | None = None
    phone: str
    postal_code: str
    city: str = ''
    street: str | None = None
    house_number: str | None = None
    installation_location: str = 'balcony'
    orientation: str = 'unknown'
    shading: str = 'unknown'
    owner_status: str = 'unknown'
    annual_consumption_kwh: int = 2500
    electricity_price_eur_kwh: float = 0.34
    wants_installation: bool = False
    purchase_timeframe: str = 'information'
    product_preference: str | None = None
    contact_time: str | None = None
    review_confirmed: bool = False
    consent_marketing: bool
    consent_partner_sharing: bool
    consent_text_version: str = 'v3_public_contact'
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    referrer: str | None = None
    landing_path: str | None = None
    project_payload: dict | None = None
    lead_origin: str | None = None
    client_code: str | None = None
    setter_name: str | None = None
    cost_eur: float = 0.0


class PublicLeadReceipt(BaseModel):
    id: int
    status: str
    market_code: str
    lead_score: int
    geo_fit_score: int | None
    assigned: bool
    public_token: str | None


class OptionalAddressUpdate(BaseModel):
    street: str = Field(min_length=2, max_length=255)
    house_number: str = Field(min_length=1, max_length=40)
    city: str = ''


class LeadOut(BaseModel):
    id: int
    created_at: datetime
    first_name: str
    last_name: str
    email: str
    phone: str
    postal_code: str
    city: str
    vertical: str = 'balcony_pv'
    market_code: str = 'unassigned'
    geo_fit_score: int | None = None
    source_type: str = 'organic_web'
    source_id: str | None = None
    orientation: str
    shading: str
    owner_status: str
    purchase_timeframe: str
    product_preference: str | None = None
    contact_time: str | None = None
    wants_installation: bool
    pv_yield_kwh: float | None
    annual_savings_eur: float | None
    lead_score: int
    status: str
    utm_source: str | None
    utm_campaign: str | None
    cost_eur: float = 0.0
    revenue_eur: float = 0.0
    duplicate_of_id: int | None = None
    assigned_partner_id: int | None = None
    assigned_sales_rep_id: int | None = None
    lead_origin: str = 'owned'
    client_account_id: int | None = None
    setter_status: str = 'queued'
    setter_attempts: int = 0
    setter_name: str | None = None
    setter_outcome: str | None = None
    class Config:
        from_attributes = True


class LeadDetailOut(LeadOut):
    street: str | None
    house_number: str | None
    latitude: float | None
    longitude: float | None
    installation_location: str
    annual_consumption_kwh: int
    electricity_price_eur_kwh: float
    utm_medium: str | None
    utm_content: str | None
    consent_marketing: bool
    consent_partner_sharing: bool
    consent_text_version: str
    consent_timestamp: datetime
    qualification_notes: str | None
    assigned_partner: str | None = None


class LeadStatusUpdate(BaseModel):
    status: str


class QualificationUpdate(BaseModel):
    reached: bool = False
    interest_confirmed: bool = False
    project_fit_confirmed: bool = False
    appointment_requested: bool = False
    budget_or_purchase_ready: bool = False
    notes: str = ''
    status: str = 'contacted'


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminMe(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    class Config:
        from_attributes = True


class SourceAnalytics(BaseModel):
    source: str
    leads: int
    hot: int
    qualified: int
    won: int
    cost_eur: float
    revenue_eur: float
    cpl: float | None
    qualified_cpl: float | None


class MarketOut(BaseModel):
    code: str
    name: str
    state_code: str
    center_lat: float
    center_lon: float
    bbox_west: float
    bbox_south: float
    bbox_east: float
    bbox_north: float
    building_provider: str
    geo_cell_count: int = 0
    class Config:
        from_attributes = True


class VerticalOut(BaseModel):
    code: str
    name: str
    active: bool
    class Config:
        from_attributes = True


class SetterUpdate(BaseModel):
    setter_name: str = Field(min_length=1, max_length=160)
    reached: bool = False
    contact_valid: bool = True
    interest_confirmed: bool = False
    project_fit_confirmed: bool = False
    decision_maker_confirmed: bool = False
    purchase_ready: bool = False
    appointment_requested: bool = False
    partner_consent_granted: bool = False
    partner_id: int | None = None
    outcome: str = 'callback'  # qualified | appointment | callback | not_interested | invalid | unreachable
    notes: str = ''


class LeadSaleUpdate(BaseModel):
    partner_id: int | None = None
    revenue_eur: float = Field(ge=0, le=100000)
    status: str = 'sold'


class AcquisitionCampaignCreate(BaseModel):
    code: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=180)
    channel: str = Field(min_length=2, max_length=80)
    market_code: str | None = None
    vertical_code: str = 'balcony_pv'


class BuyerPartnerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    contact_name: str = Field(default='', max_length=160)
    contact_email: EmailStr | None = None
    contact_phone: str = Field(default='', max_length=80)
    website: str = Field(default='', max_length=500)
    notes: str = Field(default='', max_length=2000)
    market_code: str = Field(min_length=2, max_length=80)
    vertical_code: str = Field(default='balcony_pv', min_length=2, max_length=80)
    lead_price_eur: float = Field(ge=0, le=10000)
    min_lead_score: int = Field(default=60, ge=0, le=100)
    daily_cap: int = Field(default=20, ge=1, le=10000)


class BuyerPartnerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    active: bool | None = None
    buyer_ready: bool | None = None
    contact_name: str | None = Field(default=None, max_length=160)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class DeliveryCreate(BaseModel):
    lead_id: int
    partner_id: int
    price_override_eur: float | None = Field(default=None, ge=0, le=10000)


class DeliveryFeedback(BaseModel):
    outcome: str = Field(pattern='^(accepted|rejected|won|lost)$')
    order_value_eur: float | None = Field(default=None, ge=0, le=10000000)
    reason: str = Field(default='', max_length=500)
    notes: str = Field(default='', max_length=4000)
