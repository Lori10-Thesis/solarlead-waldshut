#!/usr/bin/env python3
from app.config import get_settings

s = get_settings()
issues = []

if s.app_env != 'production': issues.append('APP_ENV muss production sein')
if s.database_url.startswith('sqlite'): issues.append('DATABASE_URL muss PostgreSQL verwenden')
if not s.database_url.startswith('postgresql+psycopg://'): issues.append('DATABASE_URL sollte postgresql+psycopg:// verwenden')
if s.jwt_secret == 'CHANGE-ME-IN-PRODUCTION' or len(s.jwt_secret) < 32: issues.append('JWT_SECRET ist zu kurz/Default')
if s.api_key_salt == 'CHANGE-ME-API-SALT' or len(s.api_key_salt) < 24: issues.append('API_KEY_SALT ist zu kurz/Default')
if s.bootstrap_admin_password == 'ChangeMe123!' or len(s.bootstrap_admin_password) < 12: issues.append('BOOTSTRAP_ADMIN_PASSWORD ist unsicher')
if not s.cookie_secure: issues.append('COOKIE_SECURE muss true sein')
if not s.trust_proxy_headers: issues.append('TRUST_PROXY_HEADERS muss hinter Caddy true sein')
if s.docs_enabled: issues.append('DOCS_ENABLED sollte im Internet false sein')
if any(o.startswith('http://') for o in s.origins): issues.append('FRONTEND_ORIGINS muss in production HTTPS sein')
if not s.hosts or 'localhost' in s.hosts: issues.append('ALLOWED_HOSTS auf echte Domain beschränken')

if issues:
    print('LIVE-CONFIG: FEHLER')
    for i in issues: print(' -', i)
    raise SystemExit(1)

print('LIVE-CONFIG: OK')
print('DB:', s.database_url.split('@')[-1])
print('Origins:', ', '.join(s.origins))
print('Hosts:', ', '.join(s.hosts))
