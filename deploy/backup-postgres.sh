#!/usr/bin/env sh
set -eu
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p backups
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "backups/solarlead-$STAMP.dump"
echo "Backup: backups/solarlead-$STAMP.dump"
