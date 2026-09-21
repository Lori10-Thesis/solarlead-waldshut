from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
checks=[]

fe=root/'frontend/.env.local'
if not fe.exists():
    checks.append('frontend/.env.local fehlt.')
else:
    txt=fe.read_text(encoding='utf-8')
    required=['NEXT_PUBLIC_OPERATOR_NAME=','NEXT_PUBLIC_OPERATOR_ADDRESS_LINE1=','NEXT_PUBLIC_OPERATOR_POSTAL_CITY=','NEXT_PUBLIC_OPERATOR_EMAIL=']
    for key in required:
        line=next((x for x in txt.splitlines() if x.startswith(key)),None)
        if not line or not line.split('=',1)[1].strip(): checks.append(f'{key[:-1]} fehlt.')

prod=root/'.env.production'
if prod.exists():
    txt=prod.read_text(encoding='utf-8')
    for token in ['CHANGE_BEFORE_FIRST_START','GENERATE_A_LONG_PASSWORD','GENERATE_AT_LEAST_32_RANDOM_BYTES','GENERATE_RANDOM_API_SALT','example.de']:
        if token in txt: checks.append(f'.env.production enthält noch Platzhalter: {token}')
else:
    print('Hinweis: .env.production fehlt – für Quick-Tunnel-Preview okay, für dauerhaften Livebetrieb nicht.')

if checks:
    print('NICHT öffentlich bewerben:')
    for x in checks: print(' -',x)
    sys.exit(1)
print('OK: Betreiberangaben für kontrollierten Public-Test sind gesetzt.')
print('Vor dauerhaftem Livebetrieb: individuelle Rechtsprüfung + Production-Secrets + stabile Domain/Hosting.')
