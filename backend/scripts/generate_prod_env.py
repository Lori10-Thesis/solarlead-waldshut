#!/usr/bin/env python3
from pathlib import Path
import getpass
import secrets

ROOT = Path(__file__).resolve().parents[2]
out = ROOT / '.env.production'

domain = input('Domain (z.B. leads.example.de): ').strip()
if not domain or '://' in domain:
    raise SystemExit('Bitte nur Hostname ohne https:// eingeben.')
admin_email = input('Admin-E-Mail: ').strip().lower()
if '@' not in admin_email:
    raise SystemExit('Ungültige Admin-E-Mail.')

postgres_password = secrets.token_hex(24)
jwt_secret = secrets.token_urlsafe(48)
api_salt = secrets.token_urlsafe(32)
admin_password = secrets.token_urlsafe(18)

content = f'''DOMAIN={domain}
POSTGRES_DB=solarlead
POSTGRES_USER=solarlead
POSTGRES_PASSWORD={postgres_password}

APP_ENV=production
DATABASE_URL=postgresql+psycopg://solarlead:{postgres_password}@db:5432/solarlead
FRONTEND_ORIGINS=https://{domain}
ALLOWED_HOSTS={domain},backend
DOCS_ENABLED=false
JWT_SECRET={jwt_secret}
ACCESS_TOKEN_MINUTES=480
COOKIE_SECURE=true
COOKIE_DOMAIN={domain}
BOOTSTRAP_ADMIN_EMAIL={admin_email}
BOOTSTRAP_ADMIN_PASSWORD={admin_password}
API_KEY_SALT={api_salt}
DEFAULT_INGESTION_API_KEY=
META_VERIFY_TOKEN=
META_APP_SECRET=
USER_AGENT=SolarLead/0.3.3 contact@{domain}
TRUST_PROXY_HEADERS=true
PUBLIC_RATE_LIMIT_REQUESTS=60
PUBLIC_RATE_LIMIT_WINDOW_SECONDS=60
'''
out.write_text(content, encoding='utf-8')
print(f'\nGeschrieben: {out}')
print('WICHTIG – Admin-Passwort jetzt sicher speichern:')
print(admin_password)
print('\nPostgreSQL-Passwort und Secrets liegen ausschließlich in .env.production.')
