# SolarLead V0.5.1 – Organic Growth Layer

V0.5.1 macht die organische Akquise messbar. Neben UTM/source am fertigen Lead wird jetzt der gesamte anonyme Funnel erfasst:

`Landing View -> Funnel Start -> PV Result -> Contact Step -> Lead -> Qualified -> Appointment/Sold`

## Datenschutzprinzip

Vor dem freiwilligen Lead-Submit speichert das Funnel-Tracking keine Namen, Telefonnummern oder E-Mail-Adressen. Die anonyme Browser-Session wird erst beim Absenden mit dem Lead verknüpft.

## Upgrade

```bash
cd ~/Downloads/solarlead-waldshut
unzip -o ~/Downloads/solarlead-v0.5.1-organic-growth-patch.zip -d ~/Downloads/solarlead-waldshut
cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/migrate_v051.py
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd ~/Downloads/solarlead-waldshut/frontend
npm run dev
```

Danach `/admin/acquisition` öffnen. Dort gibt es getrennte Waldshut-/Köln-Links für WhatsApp, Facebook und QR sowie Conversionmetriken.
