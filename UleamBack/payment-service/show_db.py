"""Diagnostic helper for payment-service DB.
Run inside the payment-service virtualenv:
    python show_db.py

It prints DATABASE_URL, SECRET_KEY length, public tables and alembic_version.
"""

from app.config import settings
import psycopg2

print("DATABASE_URL:", settings.DATABASE_URL)
print("SECRET_KEY length:", len(settings.SECRET_KEY) if settings.SECRET_KEY else 0)

try:
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
    tables = [r[0] for r in cur.fetchall()]
    print("Public tables:", tables)
    try:
        cur.execute("SELECT version_num FROM alembic_version;")
        versions = [r[0] for r in cur.fetchall()]
        print("alembic_version:", versions)
    except Exception as e:
        print("alembic_version: could not query (maybe not present):", e)
    cur.close()
    conn.close()
except Exception as e:
    print("ERROR connecting to DB:\n", e)
