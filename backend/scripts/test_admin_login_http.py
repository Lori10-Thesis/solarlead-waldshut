import getpass
import httpx

email = input('Login-E-Mail [admin@example.com]: ').strip() or 'admin@example.com'
password = getpass.getpass('Passwort: ')

try:
    r = httpx.post(
        'http://127.0.0.1:8000/api/auth/login',
        json={'email': email, 'password': password},
        timeout=10,
    )
except Exception as exc:
    raise SystemExit(f'Backend nicht erreichbar: {exc}')

print('HTTP Status:', r.status_code)
print('Antwort:', r.text)
if r.status_code == 200:
    cookie_names = [part.split('=', 1)[0] for part in r.headers.get_list('set-cookie')]
    print('Set-Cookie:', ', '.join(cookie_names) or '(keine)')
    print('OK: Backend-Login funktioniert. Falls der Browser noch scheitert, liegt es im Frontend/Cookie-Pfad.')
else:
    print('Backend-Login ist noch nicht erfolgreich; Status und Antwort oben sind die entscheidende Diagnose.')
