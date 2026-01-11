"""Reset alembic_version safely from Python.

Run inside the payment-service virtualenv:
    python reset_alembic.py

This script connects using the app.settings.DATABASE_URL and writes
'001_initial' into alembic_version so Alembic won't look for old revisions.
"""

from app.config import settings
import psycopg2
import sys

def main():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS alembic_version;")
        cur.execute("CREATE TABLE alembic_version (version_num varchar(32) NOT NULL);")
        cur.execute("INSERT INTO alembic_version (version_num) VALUES ('001_initial');")
        conn.commit()
        cur.close()
        conn.close()
        print("alembic_version reseteada a 001_initial")
    except Exception as e:
        print("ERROR: no se pudo resetear alembic_version:\n", e, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
