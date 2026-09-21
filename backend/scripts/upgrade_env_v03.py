from pathlib import Path
import secrets

base=Path(__file__).resolve().parents[1]
env=base/'.env'
backup=base/'.env.v02.backup'

lines=env.read_text(encoding='utf-8').splitlines() if env.exists() else []
values={}
for line in lines:
    if '=' in line and not line.lstrip().startswith('#'):
        k,v=line.split('=',1); values[k.strip()]=v.strip()

if env.exists() and not backup.exists():
    backup.write_text(env.read_text(encoding='utf-8'),encoding='utf-8')

if 'FRONTEND_ORIGINS' not in values:
    values['FRONTEND_ORIGINS']=values.get('FRONTEND_ORIGIN','http://localhost:3000')
values.pop('FRONTEND_ORIGIN',None)
values.setdefault('APP_ENV','development')
values.setdefault('DATABASE_URL','sqlite:///./solarlead.db')
values.setdefault('ALLOWED_HOSTS','localhost,127.0.0.1')
values.setdefault('DOCS_ENABLED','true')
values.setdefault('JWT_SECRET',secrets.token_urlsafe(48))
values.setdefault('ACCESS_TOKEN_MINUTES','480')
values.setdefault('COOKIE_SECURE','false')
values.setdefault('COOKIE_DOMAIN','')
values.setdefault('BOOTSTRAP_ADMIN_EMAIL','admin@solarlead.local')
if not values.get('BOOTSTRAP_ADMIN_PASSWORD'):
    values['BOOTSTRAP_ADMIN_PASSWORD']=secrets.token_urlsafe(18)
values.setdefault('API_KEY_SALT',secrets.token_urlsafe(32))
values.setdefault('DEFAULT_INGESTION_API_KEY','')
values.setdefault('META_VERIFY_TOKEN','')
values.setdefault('META_APP_SECRET','')
values.setdefault('USER_AGENT','SolarLead-Waldshut/0.3 contact@example.com')

order=['APP_ENV','DATABASE_URL','FRONTEND_ORIGINS','ALLOWED_HOSTS','DOCS_ENABLED','JWT_SECRET','ACCESS_TOKEN_MINUTES','COOKIE_SECURE','COOKIE_DOMAIN','BOOTSTRAP_ADMIN_EMAIL','BOOTSTRAP_ADMIN_PASSWORD','API_KEY_SALT','DEFAULT_INGESTION_API_KEY','META_VERIFY_TOKEN','META_APP_SECRET','USER_AGENT']
env.write_text('\n'.join(f'{k}={values.get(k,"")}' for k in order)+'\n',encoding='utf-8')
print('Lokale .env auf V0.3 aktualisiert.')
if backup.exists(): print('Backup:',backup)
print('Admin:',values['BOOTSTRAP_ADMIN_EMAIL'])
print('Passwort:',values['BOOTSTRAP_ADMIN_PASSWORD'])
print('Passwort jetzt sicher notieren; für Produktion NICHT diese lokale .env verwenden.')
