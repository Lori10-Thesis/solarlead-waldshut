#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
PORT="${PORT:-3000}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared fehlt. Auf macOS z.B.: brew install cloudflared"
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm fehlt."
  exit 1
fi

python3 - <<PY
import urllib.request,sys
try:
    urllib.request.urlopen('${BACKEND_URL}/health', timeout=4).read()
except Exception as e:
    print('Backend nicht erreichbar unter ${BACKEND_URL}/health:', e)
    print('Starte zuerst im backend-Ordner: PYTHONPATH=. uvicorn app.main:app --reload --port 8000')
    sys.exit(1)
PY

echo "Prüfe öffentliche Betreiberangaben …"
python3 "$ROOT/deploy/check-public-launch.py"

cd "$ROOT/frontend"
if [ ! -d node_modules ]; then npm install; fi

echo "Baue öffentliche Preview (same-origin API proxy) …"
NEXT_PUBLIC_API_URL="" \
NEXT_PUBLIC_SITE_URL="http://localhost:${PORT}" \
BACKEND_INTERNAL_URL="$BACKEND_URL" \
npm run build

echo "Starte Next.js auf 127.0.0.1:${PORT} …"
NEXT_PUBLIC_API_URL="" \
NEXT_PUBLIC_SITE_URL="http://localhost:${PORT}" \
BACKEND_INTERNAL_URL="$BACKEND_URL" \
PORT="$PORT" HOSTNAME="127.0.0.1" npm run start >/tmp/solarlead-next-preview.log 2>&1 &
NEXT_PID=$!
cleanup(){ kill "$NEXT_PID" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM

for i in {1..30}; do
  if curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then break; fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  echo "Frontend konnte nicht gestartet werden. Log: /tmp/solarlead-next-preview.log"
  exit 1
fi

echo
echo "Öffentliche TEST-URL wird jetzt erzeugt. CTRL+C beendet Preview + Tunnel."
echo "Nur für kontrollierte Tests; nicht als dauerhafte Produktions-URL verwenden."
echo
cloudflared tunnel --url "http://127.0.0.1:${PORT}"
