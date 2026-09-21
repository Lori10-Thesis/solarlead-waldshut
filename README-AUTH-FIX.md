# SolarLead V0.3.2 Auth Fix

Dieser Patch ist **flach gepackt** und überschreibt beim Entpacken direkt `backend/...` und `frontend/...`.

Er behebt:

1. falsche `.local` Default-E-Mail,
2. robustes Laden von `backend/.env` unabhängig vom Startverzeichnis,
3. normalisierte Login-E-Mail,
4. klarere Frontend-Fehler,
5. einen Reparaturbefehl, der Admin + Passwort direkt in der aktuell verwendeten Datenbank setzt und den Hash sofort verifiziert.

## Anwendung

```bash
cd ~/Downloads/solarlead-waldshut
unzip -o ~/Downloads/solarlead-v0.3.2-auth-fix.zip -d ~/Downloads/solarlead-waldshut

cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/repair_admin_login.py
```

Danach Backend komplett neu starten.
