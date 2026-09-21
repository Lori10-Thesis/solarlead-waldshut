from pathlib import Path
import getpass, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.db import SessionLocal
from app.models import AdminUser
from app.security import hash_password

email=(sys.argv[1] if len(sys.argv)>1 else input('Admin E-Mail: ')).strip().lower()
pw=getpass.getpass('Neues Passwort: ')
if len(pw)<12: raise SystemExit('Mindestens 12 Zeichen verwenden.')
db=SessionLocal()
try:
    user=db.query(AdminUser).filter(AdminUser.email==email).first()
    if not user: raise SystemExit('Admin nicht gefunden.')
    user.password_hash=hash_password(pw); db.commit(); print('Passwort aktualisiert.')
finally: db.close()
