import psycopg2

# Connect directly with simple credentials
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='reservasuleam',
    user='postgres',
    password='postgres',
    client_encoding='utf8'
)
cur = conn.cursor()

# Change the DB user password to something simple
cur.execute("ALTER USER \"Reservas_ULEAM\" WITH PASSWORD 'simple123';")
conn.commit()

print("✅ Password changed to: simple123")

cur.close()
conn.close()
