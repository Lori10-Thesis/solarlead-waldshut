# Upgrade auf V0.5.1

1. Backend und Frontend stoppen.
2. Bestehende Datenbank sichern.
3. Patch in den Projektroot entpacken.
4. Migration ausführen.
5. Backend und Frontend neu starten.

```bash
cd ~/Downloads/solarlead-waldshut
cp backend/solarlead.db backend/solarlead-before-v051.db 2>/dev/null || true
unzip -o ~/Downloads/solarlead-v0.5.1-organic-growth-patch.zip -d ~/Downloads/solarlead-waldshut

cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/migrate_v051.py
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Zweites Terminal:

```bash
cd ~/Downloads/solarlead-waldshut/frontend
npm run dev
```

Test:
- `/admin/acquisition` öffnen
- z. B. `Facebook Gruppen Köln` Link kopieren
- Link in neuem privaten Browserfenster öffnen
- Funnel bis zum Lead durchlaufen
- `/admin/acquisition` aktualisieren
- Aufrufe/Starts/Ergebnisse/Kontakt/Leads sollten hochzählen
