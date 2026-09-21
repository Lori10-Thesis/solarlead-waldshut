from pathlib import Path
import secrets, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.db import SessionLocal
from app.models import ApiClient
from app.security import api_key_hash

name=sys.argv[1] if len(sys.argv)>1 else 'Partner'
source=sys.argv[2] if len(sys.argv)>2 else name.lower().replace(' ','_')
raw='sl_'+secrets.token_urlsafe(32)
db=SessionLocal()
try:
    db.add(ApiClient(name=name,key_hash=api_key_hash(raw),source_id=source)); db.commit()
finally: db.close()
print('API-Key (nur jetzt sichtbar):')
print(raw)
print('source_id:',source)
