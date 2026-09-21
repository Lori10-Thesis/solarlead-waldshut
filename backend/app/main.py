import threading
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .config import get_settings
from .db import Base, SessionLocal, engine
from .models import AdminUser, ApiClient
from .request_utils import client_ip
from .routers import admin, auth, buyers, geo, ingestion, platform, public, webhooks
from .security import api_key_hash, hash_password
from .seed import seed_geo
from .platform_seed import seed_platform

settings = get_settings()
VERSION = '0.6.0'

if settings.app_env == 'production':
    insecure = [
        settings.jwt_secret == 'CHANGE-ME-IN-PRODUCTION',
        settings.bootstrap_admin_password == 'ChangeMe123!',
        settings.api_key_salt == 'CHANGE-ME-API-SALT',
        settings.database_url.startswith('sqlite'),
        not settings.cookie_secure,
        not settings.trust_proxy_headers,
    ]
    if any(insecure):
        raise RuntimeError('Production-Konfiguration ist unsicher/unvollständig. validate_live_config.py ausführen.')

app = FastAPI(
    title='SolarLead API', version=VERSION,
    docs_url='/docs' if settings.docs_enabled else None,
    redoc_url=None,
)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts or ['*'])
app.add_middleware(GZipMiddleware, minimum_size=1000)

_rate_lock = threading.Lock()
_rate_hits: dict[str, deque[float]] = defaultdict(deque)
_PUBLIC_LIMITED = {'/api/pv/calculate', '/api/leads', '/api/widget/leads', '/api/funnel/events'}


@app.middleware('http')
async def public_rate_limit(request: Request, call_next):
    if request.method == 'POST' and request.url.path in _PUBLIC_LIMITED:
        ip = client_ip(request) or 'unknown'
        key = f'{ip}:{request.url.path}'
        now = time.monotonic()
        cutoff = now - settings.public_rate_limit_window_seconds
        with _rate_lock:
            q = _rate_hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= settings.public_rate_limit_requests:
                return JSONResponse(status_code=429, content={'detail': 'Zu viele Anfragen. Bitte später erneut versuchen.'})
            q.append(now)
    return await call_next(request)


@app.middleware('http')
async def request_security_headers(request: Request, call_next):
    request_id = request.headers.get('x-request-id') or str(uuid.uuid4())
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if settings.app_env == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@app.on_event('startup')
def startup():
    if settings.database_url.startswith('postgresql'):
        with engine.begin() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if settings.app_env != 'production':
            seed_geo(db)
        seed_platform(db)
        email = settings.bootstrap_admin_email.strip().lower()
        if not db.query(AdminUser).filter(AdminUser.email == email).first():
            db.add(AdminUser(email=email, password_hash=hash_password(settings.bootstrap_admin_password), display_name='SolarLead Admin'))
        if settings.default_ingestion_api_key:
            h = api_key_hash(settings.default_ingestion_api_key)
            if not db.query(ApiClient).filter(ApiClient.key_hash == h).first():
                db.add(ApiClient(name='Default Partner API', key_hash=h, source_id='default_partner'))
        db.commit()
    finally:
        db.close()


@app.get('/health')
def health():
    return {'ok': True, 'version': VERSION, 'env': settings.app_env}


@app.get('/ready')
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            postgis = None
            if settings.database_url.startswith('postgresql'):
                postgis = bool(conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='postgis')")).scalar())
        return {'ok': True, 'database': 'ok', 'postgis': postgis}
    except Exception:
        return JSONResponse(status_code=503, content={'ok': False, 'database': 'unavailable'})


app.include_router(auth.router)
app.include_router(public.router)
app.include_router(platform.router)
app.include_router(ingestion.router)
app.include_router(admin.router)
app.include_router(buyers.router)
app.include_router(geo.router)
app.include_router(webhooks.router)
