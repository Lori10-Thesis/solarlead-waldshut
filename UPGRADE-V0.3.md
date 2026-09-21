# Upgrade von V0.2.3 auf V0.3

## 0. Server stoppen
In Backend- und Frontend-Terminal jeweils `CTRL+C`.

## 1. Backup
```bash
cd ~/Downloads/solarlead-waldshut
cp backend/solarlead.db backend/solarlead-before-v03.db 2>/dev/null || true
cp -R backend/data backend/data-before-v03
```

## 2. Patch entpacken
```bash
unzip -o ~/Downloads/solarlead-waldshut-v0.3-live-patch.zip -d ~/Downloads/solarlead-waldshut
```

## 3. Python-Pakete
```bash
cd ~/Downloads/solarlead-waldshut/backend
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Lokale Config aktualisieren
```bash
python scripts/upgrade_env_v03.py
```
Admin-E-Mail und generiertes Passwort aus der Ausgabe notieren.

## 5. Datenbank migrieren
```bash
python scripts/migrate_v03.py
```
Deine bisherigen Leads und Geo-Daten bleiben erhalten.

## 6. Backend starten
```bash
uvicorn app.main:app --reload --port 8000
```

## 7. Frontend aktualisieren/starten
Neues Terminal:
```bash
cd ~/Downloads/solarlead-waldshut/frontend
npm install
npm run dev
```

## 8. Login
`http://localhost:3000/admin/login`

## 9. Prüfen
- `/admin` nur nach Login erreichbar
- `/geo` nur nach Login erreichbar
- `/admin/analytics` zeigt Leadquellen
- bestehender Funnel unter `/` erzeugt weiterhin Leads
- `/widget?source=test_partner` öffnet Embed-Widget

## 10. Partner-API testen
```bash
cd ~/Downloads/solarlead-waldshut/backend
source .venv/bin/activate
python scripts/create_api_key.py "Test Partner" test_partner
```
Den ausgegebenen Key einsetzen:
```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: DEIN_KEY' \
  -d '{
    "vertical":"heatpump",
    "source_type":"partner_api",
    "first_name":"Max",
    "last_name":"Muster",
    "email":"max@example.de",
    "phone":"01761234567",
    "postal_code":"79761",
    "city":"Waldshut-Tiengen",
    "consent_marketing":true,
    "consent_partner_sharing":true
  }'
```
