# SolarLead V0.3.3 – Live Deployment

## Zielarchitektur

```text
Internet
  -> Caddy (HTTPS)
      -> Next.js frontend
      -> FastAPI backend
          -> PostgreSQL + PostGIS
```

Das Backend ist im Production-Compose **nicht direkt öffentlich veröffentlicht**. PostgreSQL ist nur an `127.0.0.1:5432` gebunden, damit eine kontrollierte Migration vom Server-Host möglich bleibt.

## 1. Server-Voraussetzungen

- Linux VPS
- Docker Engine + Docker Compose Plugin
- Domain mit A/AAAA-Record auf den Server
- Ports 80/443 offen

## 2. Production-Secrets erzeugen

Im Projektroot:

```bash
python3 backend/scripts/generate_prod_env.py
```

Danach **Admin-Passwort sofort in einem Passwortmanager sichern**.

Prüfen:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/validate_live_config.py
```

Für diese Prüfung muss die Production-Konfiguration in `backend/.env` liegen oder als Environment geladen sein. Auf dem Server kann alternativ geprüft werden mit:

```bash
set -a; . ../.env.production; set +a
PYTHONPATH=. python scripts/validate_live_config.py
```

## 3. PostgreSQL zuerst starten

```bash
cd ..
docker compose --env-file .env.production -f docker-compose.prod.yml up -d db
```

## 4. Bestehende lokale SQLite-Daten migrieren

Wenn `backend/solarlead.db` auf dem Server liegt:

```bash
cd backend
source .venv/bin/activate
set -a; . ../.env.production; set +a
export TARGET_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"
PYTHONPATH=. python scripts/migrate_sqlite_to_postgres.py
```

Das Script bricht ab, wenn das Ziel bereits Daten enthält.

## 5. Vollständig starten

```bash
cd ..
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Status:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Logs:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
```

## 6. Smoke-Test

```bash
SOLARLEAD_BASE_URL="https://DEINE-DOMAIN" python backend/scripts/live_smoke_test.py
```

Erwartet: `/health` und `/ready` liefern HTTP 200.

## 7. Partner API Key

```bash
cd backend
set -a; . ../.env.production; set +a
PYTHONPATH=. python scripts/create_api_key.py "Pilot Partner" pilot_partner
```

API-Key nur einmalig sicher an den Partner übergeben.

## 8. Backup

```bash
./deploy/backup-postgres.sh
```

Backups landen in `backups/` und sollten zusätzlich **außerhalb des Servers** gesichert werden.

## Vor echtem Traffic

- Impressum mit realem Betreiber füllen
- Datenschutzerklärung / Consent-Texte juristisch prüfen
- echte Kontakt-/Widerrufsinformationen eintragen
- Domain und Absenderadresse finalisieren
- regelmäßige DB-Backups einrichten
- Server-Firewall aktivieren
- Meta/Google erst verbinden, wenn Basis-Tracking/Consent final ist
