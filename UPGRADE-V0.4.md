# Upgrade auf V0.4 Platform Core

1. Backend/Frontend stoppen.
2. Backup von `backend/solarlead.db` und `backend/data` erstellen.
3. Patch über das bestehende Projekt entpacken.
4. Im Backend:

```bash
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python scripts/migrate_v04.py
PYTHONPATH=. python scripts/platform_status.py
uvicorn app.main:app --reload --port 8000
```

5. Frontend:

```bash
cd frontend
npm install
npm run dev
```

V0.4 behält bestehende Waldshut-Zellen und markiert sie als `market_code=waldshut`, `vertical_code=balcony_pv`.
Köln wird als Markt/Routinggebiet angelegt, erhält aber erst nach einem echten Datenimport Geo-Zellen.
