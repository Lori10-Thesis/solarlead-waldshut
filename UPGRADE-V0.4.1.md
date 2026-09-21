# Upgrade V0.4 -> V0.4.1

1. Backend/Frontend stoppen.
2. Projekt und `backend/data` sichern.
3. Patch im Projektroot entpacken.
4. Keine DB-Migration erforderlich.
5. Backend aktivieren.
6. Köln-Pipeline ausführen.
7. Danach beide Märkte auf Geo Score v2 rebuilden.

```bash
cd ~/Downloads/solarlead-waldshut/backend
source .venv/bin/activate

PYTHONPATH=. python scripts/run_koeln_geo_pipeline.py
PYTHONPATH=. python scripts/rebuild_geo_v2.py

uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd ~/Downloads/solarlead-waldshut/frontend
npm run dev
```

Danach unter `/geo` zwischen Waldshut und Köln wechseln.
