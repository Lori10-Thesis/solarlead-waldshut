#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FE=ROOT/'frontend/.env.local'
BE=ROOT/'backend/.env'

def ask(label, default=''):
    hint=f" [{default}]" if default else ''
    v=input(f"{label}{hint}: ").strip()
    return v or default

def read_env(path):
    data={}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line or line.lstrip().startswith('#') or '=' not in line: continue
            k,v=line.split('=',1); data[k]=v
    return data

def write_env(path,data):
    path.write_text('\n'.join(f'{k}={v}' for k,v in data.items())+'\n',encoding='utf-8')

print('Öffentliche Betreiber-/Brand-Konfiguration')
brand=ask('Consumer-Marke','BalkonCheck')
operator=ask('Betreibername / Firma')
legal=ask('Rechtsform (optional)')
addr1=ask('Straße + Hausnummer')
addr2=ask('Adresszusatz (optional)')
postal=ask('PLZ + Ort')
email=ask('Kontakt-E-Mail')
phone=ask('Telefon (optional)')
privacy=ask('Datenschutz-E-Mail',email)
site_url=ask('Öffentliche Basis-URL (für Preview kann localhost bleiben)','http://localhost:3000')
host=ask('Hosting-/Infrastrukturanbieter (optional)')
host_country=ask('Hosting-Land (optional)','Deutschland')
cloudflare=ask('Cloudflare aktiv? true/false','true').lower()

fe=read_env(FE)
fe.update({
 'NEXT_PUBLIC_CONSUMER_BRAND':brand,
 'NEXT_PUBLIC_PLATFORM_BRAND':'SolarLead',
 'NEXT_PUBLIC_OPERATOR_NAME':operator,
 'NEXT_PUBLIC_OPERATOR_LEGAL_FORM':legal,
 'NEXT_PUBLIC_OPERATOR_ADDRESS_LINE1':addr1,
 'NEXT_PUBLIC_OPERATOR_ADDRESS_LINE2':addr2,
 'NEXT_PUBLIC_OPERATOR_POSTAL_CITY':postal,
 'NEXT_PUBLIC_OPERATOR_COUNTRY':'Deutschland',
 'NEXT_PUBLIC_OPERATOR_EMAIL':email,
 'NEXT_PUBLIC_OPERATOR_PHONE':phone,
 'NEXT_PUBLIC_PRIVACY_EMAIL':privacy,
 'NEXT_PUBLIC_SITE_URL':site_url,
 'NEXT_PUBLIC_HOSTING_PROVIDER':host,
 'NEXT_PUBLIC_HOSTING_COUNTRY':host_country,
 'NEXT_PUBLIC_CLOUDFLARE_ENABLED':'true' if cloudflare=='true' else 'false',
})
write_env(FE,fe)

be=read_env(BE)
be['OPERATOR_NAME']=' '.join(x for x in [operator,legal] if x)
be['OPERATOR_CONTACT_EMAIL']=email
write_env(BE,be)
print(f'OK: {FE}')
print(f'OK: {BE}')
print('Danach Frontend neu bauen/starten, damit die öffentlichen Variablen übernommen werden.')
