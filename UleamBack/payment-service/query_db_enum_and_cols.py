import psycopg2
conn = psycopg2.connect("postgresql://postgres:123456789@localhost:5432/payment_service_db")
cur = conn.cursor()
# Get enum labels for type paymentstatus
cur.execute("SELECT t.typname, e.enumlabel FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typname = 'paymentstatus';")
rows = cur.fetchall()
print('enum paymentstatus labels:')
for r in rows:
    print('-', r[1])
# Get columns for payment table
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='payment';")
cols = cur.fetchall()
print('\npayment table columns:')
for c in cols:
    print('-', c[0], c[1])
cur.close()
conn.close()
