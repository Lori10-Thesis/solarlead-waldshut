#!/usr/bin/env python3
"""Copy SolarLead data from SQLite to an empty PostgreSQL database.

Usage from backend/:
  TARGET_DATABASE_URL='postgresql+psycopg://...' PYTHONPATH=. python scripts/migrate_sqlite_to_postgres.py

The script preserves primary keys and aborts when the target already contains rows.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, func, select, text

from app.models import Base

BASE = Path(__file__).resolve().parents[1]
SOURCE_URL = os.getenv('SOURCE_DATABASE_URL', f'sqlite:///{BASE / "solarlead.db"}')
TARGET_URL = os.getenv('TARGET_DATABASE_URL')
if not TARGET_URL:
    raise SystemExit('TARGET_DATABASE_URL fehlt.')
if not TARGET_URL.startswith('postgresql'):
    raise SystemExit('TARGET_DATABASE_URL muss PostgreSQL sein.')

source = create_engine(SOURCE_URL, future=True)
target = create_engine(TARGET_URL, future=True, pool_pre_ping=True)

with target.begin() as conn:
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
Base.metadata.create_all(target)

order = [
    'admin_users', 'api_clients', 'geo_cells', 'leads',
    'lead_events', 'consent_records', 'integration_events'
]
tables = {t.name: t for t in Base.metadata.sorted_tables}

with source.connect() as src, target.begin() as dst:
    for name in order:
        table = tables.get(name)
        if table is None:
            continue
        try:
            existing = dst.execute(select(func.count()).select_from(table)).scalar_one()
        except Exception as exc:
            raise SystemExit(f'Zieltabelle {name} nicht lesbar: {exc}')
        if existing:
            raise SystemExit(f'ABBRUCH: Zieltabelle {name} enthält bereits {existing} Datensätze.')

        rows = [dict(r._mapping) for r in src.execute(select(table)).all()]
        if rows:
            dst.execute(table.insert(), rows)
        print(f'{name}: {len(rows)} kopiert')

    # Reset PostgreSQL sequences after explicit ID import.
    for name in order:
        table = tables.get(name)
        if table is None or 'id' not in table.c:
            continue
        dst.execute(text(f"SELECT setval(pg_get_serial_sequence('{name}','id'), COALESCE((SELECT MAX(id) FROM {name}),1), EXISTS(SELECT 1 FROM {name}))"))

print('Migration SQLite -> PostgreSQL abgeschlossen.')
