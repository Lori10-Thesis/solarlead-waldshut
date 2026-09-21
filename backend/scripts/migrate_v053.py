from sqlalchemy import inspect, text
from app.db import engine, Base
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)

def add_column(table: str, column: str, ddl: str):
    insp=inspect(engine)
    cols={c['name'] for c in insp.get_columns(table)}
    if column in cols:
        print(f"OK {table}.{column}")
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
    print(f"ADD {table}.{column}")

add_column('leads','partner_consent_granted','partner_consent_granted BOOLEAN NOT NULL DEFAULT 0')
add_column('leads','partner_consent_partner_id','partner_consent_partner_id INTEGER')
add_column('leads','partner_consent_partner_name','partner_consent_partner_name VARCHAR(160)')
add_column('leads','partner_consent_timestamp','partner_consent_timestamp DATETIME')
add_column('leads','partner_consent_setter','partner_consent_setter VARCHAR(160)')
add_column('consent_records','text_snapshot','text_snapshot TEXT')
add_column('consent_records','context_json','context_json TEXT')
print('V0.5.3 Migration abgeschlossen.')
