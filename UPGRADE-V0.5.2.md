# Upgrade V0.5.1 → V0.5.2

Keine Datenbankmigration notwendig.

1. Server stoppen und Backup anlegen.
2. Patch in den Projektroot entpacken.
3. Frontend Dependencies bleiben unverändert.
4. Backend/Frontend normal starten und lokal testen.
5. Für kostenlosen externen Preview-Test `./deploy/public-preview.sh` verwenden.

Hinweis: `NEXT_PUBLIC_API_URL` ist jetzt standardmäßig leer; API-Aufrufe laufen same-origin. Lokal übernimmt Next.js den Proxy zu `BACKEND_INTERNAL_URL=http://127.0.0.1:8000`.
