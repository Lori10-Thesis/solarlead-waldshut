import argparse, json
from app.db import SessionLocal
from app.models import ClientAccount

DEFAULT_SCRIPT = [
    'Ist die Anfrage aktuell und darf ich kurz 2–3 Minuten dazu fragen?',
    'Was genau möchten Sie lösen bzw. kaufen?',
    'Ist das Projekt grundsätzlich real und umsetzbar?',
    'Treffen Sie die Entscheidung selbst oder ist noch jemand beteiligt?',
    'In welchem Zeitraum möchten Sie starten?',
    'Möchten Sie als nächsten Schritt ein Angebot / Beratungsgespräch?',
]

p=argparse.ArgumentParser()
p.add_argument('code')
p.add_argument('name')
p.add_argument('--vertical', default='generic')
a=p.parse_args()

db=SessionLocal()
try:
    obj=db.query(ClientAccount).filter(ClientAccount.code==a.code).first()
    if obj:
        print(f'Existiert bereits: {obj.code} · {obj.name}')
    else:
        obj=ClientAccount(code=a.code,name=a.name,vertical_code=a.vertical,active=True,qualification_script_json=json.dumps(DEFAULT_SCRIPT,ensure_ascii=False))
        db.add(obj);db.commit();db.refresh(obj)
        print(f'Client erstellt: id={obj.id} code={obj.code} name={obj.name}')
finally:
    db.close()
