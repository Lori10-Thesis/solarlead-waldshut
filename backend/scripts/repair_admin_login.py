from pathlib import Path
import getpass
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from app.config import get_settings
from app.db import SessionLocal, engine
from app.models import AdminUser
from app.security import hash_password, verify_password

settings = get_settings()

print('SolarLead Auth-Reparatur')
print('-------------------------')
print('Datenbank:', engine.url)
print('Geladene .env:', BASE / '.env')

email = input('Neue Admin-E-Mail [admin@example.com]: ').strip().lower() or 'admin@example.com'
if '@' not in email or '.' not in email.split('@', 1)[1]:
    raise SystemExit('Bitte eine normale gültige E-Mail verwenden, z. B. admin@example.com.')

pw1 = getpass.getpass('Neues Admin-Passwort (mind. 12 Zeichen): ')
pw2 = getpass.getpass('Passwort wiederholen: ')
if pw1 != pw2:
    raise SystemExit('Passwörter stimmen nicht überein.')
if len(pw1) < 12:
    raise SystemExit('Passwort muss mindestens 12 Zeichen haben.')

with SessionLocal() as db:
    admins = db.query(AdminUser).order_by(AdminUser.id).all()
    print('Vorhandene Admins:', ', '.join(f'{u.id}:{u.email}' for u in admins) or '(keine)')

    user = db.query(AdminUser).filter(AdminUser.email == email).first()
    if not user:
        if len(admins) == 1:
            user = admins[0]
            print(f'Benenne vorhandenen Admin um: {user.email} -> {email}')
            user.email = email
        else:
            user = AdminUser(email=email, display_name='SolarLead Admin', role='admin', is_active=True, password_hash='')
            db.add(user)
            db.flush()
            print('Neuen Admin angelegt:', email)

    user.is_active = True
    user.password_hash = hash_password(pw1)
    db.commit()
    db.refresh(user)

    if not verify_password(pw1, user.password_hash):
        raise SystemExit('Interner Passwort-Selbsttest fehlgeschlagen.')

    user_id = user.id

# Keep bootstrap email consistent, but do not store the new password in plaintext.
env = BASE / '.env'
if env.exists():
    lines = env.read_text(encoding='utf-8').splitlines()
    out = []
    found = False
    for line in lines:
        if line.startswith('BOOTSTRAP_ADMIN_EMAIL='):
            out.append(f'BOOTSTRAP_ADMIN_EMAIL={email}')
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f'BOOTSTRAP_ADMIN_EMAIL={email}')
    env.write_text('\n'.join(out) + '\n', encoding='utf-8')

print('\nOK: Admin wurde repariert und Passwort-Hash erfolgreich geprüft.')
print('Admin-ID:', user_id)
print('Login-E-Mail:', email)
print('Jetzt Backend neu starten und exakt diese E-Mail verwenden.')
