# SolarLead V0.3 – Live Foundation

V0.3 macht aus dem lokalen Waldshut-MVP eine produktionsfähige Plattformbasis.

## Neu
- geschütztes Admin-Login (JWT in HttpOnly Cookie + CSRF Double Submit)
- universelle Partner-Ingestion: `POST /api/v1/leads` + `X-API-Key`
- Embed-Widget: `/widget?source=partner_slug`
- Deduplizierung über 90 Tage
- unveränderliche Consent-/Lead-Events
- Quellen-/Kosten-/Umsatzanalytics
- Meta Leadgen Webhook-Verifikation + Event-Speicherung
- PostgreSQL/PostGIS Docker-Stack
- Caddy Reverse Proxy + automatisches TLS
- Security Header, Trusted Hosts, CORS-Whitelist

## Lokales Upgrade aus V0.2.x
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python scripts/migrate_v03.py
```
`.env` um die Werte aus `.env.example` ergänzen und insbesondere Admin-Passwort/JWT-Secret ändern.

Dann:
```bash
uvicorn app.main:app --reload --port 8000
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```
Admin: `http://localhost:3000/admin/login`

## Partner API Key erzeugen
```bash
cd backend
source .venv/bin/activate
python scripts/create_api_key.py "Elektro Müller" elektro_mueller
```
Der Key wird genau einmal angezeigt.

Beispiel:
```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: sl_...' \
  -d '{
    "vertical":"balcony_pv",
    "source_type":"partner_api",
    "first_name":"Max","last_name":"Muster",
    "email":"max@example.de","phone":"01761234567",
    "postal_code":"79761","city":"Waldshut-Tiengen",
    "consent_marketing":true,"consent_partner_sharing":true
  }'
```

## Embed-Widget
```html
<iframe
  src="https://DEINE-DOMAIN/widget?source=elektro_mueller"
  style="width:100%;height:650px;border:0;border-radius:18px"
  loading="lazy">
</iframe>
```

## Production
1. `.env.production.example` nach `.env.production` kopieren.
2. alle Secrets und Domain setzen.
3. DNS A/AAAA auf den Server richten.
4. `docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build`
5. Erst danach Traffic aufschalten.

### Vor echter Lead-Vermittlung
- finalen Datenschutz-/Consent-Text anwaltlich prüfen lassen
- Partner/Empfänger transparent abbilden
- Lösch-/Auskunftsprozess ergänzen
- Backups, Monitoring, Rate Limiting/WAF, Error Tracking aktivieren
- Meta Adapter erst mit echten App-/Page-Tokens aktivieren
