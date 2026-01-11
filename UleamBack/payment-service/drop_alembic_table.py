"""Drop alembic_version table safely.

Run inside the payment-service virtualenv:
    python drop_alembic_table.py

This will DROP TABLE IF EXISTS alembic_version; so Alembic can
run the initial migration (001_initial) and subsequent ones.
"""
from app.config import settings
import psycopg2
import sys

def main():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS alembic_version;")
        conn.commit()
        cur.close()
        conn.close()
        print("alembic_version table dropped (if existed)")
    except Exception as e:
        print("ERROR dropping alembic_version:\n", e, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
