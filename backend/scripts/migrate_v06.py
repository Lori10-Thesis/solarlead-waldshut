from sqlalchemy import inspect, text
from app.db import Base, engine
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)


def add_column(table: str, column: str, ddl: str):
    insp = inspect(engine)
    cols = {c['name'] for c in insp.get_columns(table)}
    if column in cols:
        print(f'OK {table}.{column}')
        return
    with engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}'))
    print(f'ADD {table}.{column}')


add_column('partners', 'partner_type', "VARCHAR(40) NOT NULL DEFAULT 'internal'")
add_column('partners', 'buyer_ready', 'BOOLEAN NOT NULL DEFAULT FALSE')
add_column('partners', 'contact_name', 'VARCHAR(160)')
add_column('partners', 'contact_email', 'VARCHAR(255)')
add_column('partners', 'contact_phone', 'VARCHAR(80)')
add_column('partners', 'website', 'VARCHAR(500)')
add_column('partners', 'notes', 'TEXT')

with engine.begin() as conn:
    conn.execute(text('CREATE INDEX IF NOT EXISTS ix_partners_partner_type ON partners (partner_type)'))
    conn.execute(text('CREATE INDEX IF NOT EXISTS ix_partners_buyer_ready ON partners (buyer_ready)'))
    # Existing pilot partners are routing objects, never implicit commercial buyers.
    conn.execute(text("UPDATE partners SET partner_type='internal', buyer_ready=FALSE WHERE partner_type IS NULL OR partner_type=''"))

print('V0.6 Migration abgeschlossen.')
print('Hinweis: Bestehende Pilotpartner bleiben interne Routingobjekte. Reale Buyer über /admin/buyers anlegen.')
