# SolarLead V0.3.3 – Live Readiness

Diese Version macht aus V0.3 eine belastbare Deployment-Basis.

## Neu

- einheitliche DB-Konfiguration über `backend/.env` / Environment
- PostgreSQL + PostGIS Production-Betrieb
- SQLite -> PostgreSQL Datenmigration mit ID-Erhalt
- `/ready` Readiness-Check mit DB/PostGIS-Test
- echte Client-IP hinter Caddy für Consent-Audit
- einfache Public-Endpoint Rate Limits
- Idempotenz für Partner-API über `external_id`
- Production-Konfigurationsprüfung
- Generator für sichere Production-Secrets
- Docker Healthchecks
- Caddy Reverse Proxy + HTTPS-Struktur
- PostgreSQL Backup-Script
- Live Smoke-Test
- in Production keine Demo-Geo-Seeds

## Wichtig

Das ist eine **Production-Basis**, aber vor öffentlichem Traffic müssen Betreiberangaben,
Datenschutz-/Consent-Texte und das konkrete Vermittlungsmodell final geprüft werden.

Siehe `LIVE-DEPLOY.md`.
