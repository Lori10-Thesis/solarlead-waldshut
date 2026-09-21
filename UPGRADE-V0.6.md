# Upgrade auf V0.6

```bash
cd ~/Downloads/solarlead-waldshut
cp backend/solarlead.db backend/solarlead-before-v06.db
unzip -o ~/Downloads/solarlead-v0.6-buyer-layer-patch.zip -d ~/Downloads/solarlead-waldshut

cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/migrate_v06.py
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Frontend in einem zweiten Terminal:

```bash
cd ~/Downloads/solarlead-waldshut/frontend
npm run dev
```

Danach:

- `/admin/buyers`
- echten Buyer anlegen
- in `/admin/setter` einen qualifizierten Lead an genau diesen Buyer freigeben
- zurück nach `/admin/buyers`
- Lead ausliefern
- Abschlussfeedback erfassen
