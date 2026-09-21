"""Idempotente lokale Migration V0.2.x -> V0.3 für SQLite/PostgreSQL.
Für einen frischen Produktions-DB-Start genügt Base.metadata.create_all beim ersten Start.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text
from app.db import Base, engine

NEW_LEAD_COLUMNS = {
    'updated_at': 'DATETIME',
    'vertical': "VARCHAR(80) DEFAULT 'balcony_pv'",
    'source_type': "VARCHAR(80) DEFAULT 'organic_web'",
    'source_id': 'VARCHAR(160)',
    'external_id': 'VARCHAR(200)',
    'dedupe_key': 'VARCHAR(64)',
    'duplicate_of_id': 'INTEGER',
    'referrer': 'VARCHAR(500)',
    'landing_path': 'VARCHAR(300)',
    'project_payload': 'TEXT',
    'cost_eur': 'FLOAT DEFAULT 0',
    'revenue_eur': 'FLOAT DEFAULT 0',
    'assigned_partner': 'VARCHAR(160)',
    'consent_user_agent': 'VARCHAR(500)',
}

insp=inspect(engine)
if 'leads' in insp.get_table_names():
    existing={c['name'] for c in insp.get_columns('leads')}
    with engine.begin() as conn:
        for name,sqltype in NEW_LEAD_COLUMNS.items():
            if name not in existing:
                print('ADD leads.'+name)
                conn.execute(text(f'ALTER TABLE leads ADD COLUMN {name} {sqltype}'))
Base.metadata.create_all(bind=engine)
print('V0.3 Migration abgeschlossen.')
