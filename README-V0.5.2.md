# SolarLead V0.5.2 – Public Launch

## Ziel
V0.5.2 macht den organischen Funnel öffentlich testbar, ohne bereits Paid Ads zu benötigen.

## Neu
- Same-origin API-Proxy über Next.js für lokale/öffentliche Preview
- temporärer Cloudflare Quick-Tunnel Workflow
- relative API-URLs im Browser statt hartem localhost:8000
- robots.txt: Admin und Geo Intelligence werden nicht indexiert
- sitemap.xml für öffentliche Seiten
- generisches SolarLead-Metadata statt Waldshut-Branding
- Impressum/Datenschutz Links im öffentlichen Funnel
- Production-Docker-Build mit Site-/Backend-URL
- Public-Launch-Checker verhindert versehentlichen Livegang mit Platzhalter-Rechtstexten/Secrets

## Kostenloser Preview-Test
Backend lokal starten:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Auf macOS einmalig Cloudflared installieren, falls nicht vorhanden:

```bash
brew install cloudflared
```

Dann aus dem Projektroot:

```bash
./deploy/public-preview.sh
```

Cloudflare gibt eine zufällige `*.trycloudflare.com` URL aus. Diese URL nur für einen kontrollierten Test verwenden.

## Produktion
Für echte dauerhafte Lead-Akquise: Domain + VPS, `.env.production`, PostgreSQL/PostGIS, Caddy/HTTPS und finale Betreiber-/Datenschutztexte.

Vor Produktivstart:

```bash
python3 deploy/check-public-launch.py
```
