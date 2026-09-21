# SolarLead V0.5 – Organic Acquisition + Setter Ops

## Ziel
V0.5 arbeitet ohne Paid Ads und ohne kostenpflichtige Leadquellen. Zwei Geschäftsmodelle laufen im selben Kern:

1. **Owned Leads** – über eigene organische Links/Funnel generiert, qualifiziert und später verkauft.
2. **Setter Service** – opt-in/inbound Leads eines Kunden per API oder CSV übernehmen, mit festem Skript vorqualifizieren und zurückgeben.

## Upgrade

```bash
cd ~/Downloads/solarlead-waldshut
cp backend/solarlead.db backend/solarlead-before-v05.db 2>/dev/null || true
unzip -o ~/Downloads/solarlead-v0.5-organic-setter-patch.zip -d ~/Downloads/solarlead-waldshut
cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/migrate_v05.py
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd ~/Downloads/solarlead-waldshut/frontend
npm run dev
```

## Organic Acquisition

`http://localhost:3000/admin/acquisition`

Vorgefertigte Trackinglinks:
- WhatsApp Waldshut
- Facebook Gruppen Köln
- lokale QR/Flyer
- Referral

Jeder Link schreibt `source_id` + UTM-Parameter in den Lead. So sehen wir später genau, welche Gruppe/Region wirklich Qualified Leads produziert.

## Setter Ops

Kundenkonto anlegen:

```bash
cd ~/Downloads/solarlead-waldshut/backend
source .venv/bin/activate
PYTHONPATH=. python scripts/create_client_account.py ikv_energy "IKV Energy" --vertical balcony_pv
```

Danach kann der Kunde Leads über `POST /api/v1/client-leads` schicken und `client_code: "ikv_energy"` setzen. Für Setter-Leads reicht eine dokumentierte Kontakt-/Telefon-Einwilligung; eine Weitergabe an weitere Partner ist davon getrennt.

Alternativ CSV:

```bash
PYTHONPATH=. python scripts/import_client_leads_csv.py ikv_energy ./leads.csv --vertical balcony_pv
```

Call Queue:

`http://localhost:3000/admin/setter`

## Kommerzialisierung

Eigene Leads: `owned` -> qualifizieren -> `/api/admin/marketplace/ready` -> Partner zuweisen/verkaufen.

Kundenleads: `client_supplied` -> Setter Queue -> qualifiziert / Termin / Rückruf / nicht geeignet.

## Nicht Teil der kostenlosen Phase
- Paid Meta/Google Ads
- SMS OTP
- bezahlte Leadlisten
- gekaufte Datenbanken

Die Adapter können später an denselben Ingestion-Layer angeschlossen werden.
