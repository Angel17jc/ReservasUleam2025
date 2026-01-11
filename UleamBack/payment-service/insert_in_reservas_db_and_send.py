import psycopg2
import subprocess, sys

DBR = "postgresql://Reservas_ULEAM:123456789@localhost:5432/reservasuleam"
try:
    conn = psycopg2.connect(DBR)
    cur = conn.cursor()
    # check if payment table exists
    cur.execute("SELECT to_regclass('public.payment')")
    if cur.fetchone()[0] is None:
        print('No payment table in reservasuleam DB')
    else:
        cur.execute("""
        INSERT INTO payment (external_payment_id,reserva_id,usuario_id,provider_name,amount,currency,status,metadata_json)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (external_payment_id) DO NOTHING
        """, ("pi_test_123", 1, 1, "stripe", 50.00, "USD", "PENDING", '{}'))
        conn.commit()
        cur.execute("SELECT id, external_payment_id, status FROM payment WHERE external_payment_id=%s", ("pi_test_123",))
        print('Inserted/Found in reservasuleam:', cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print('Error connecting to reservas DB:', e)

print('Sending webhook...')
res = subprocess.run([sys.executable, 'send_test_stripe_webhook.py'], capture_output=True, text=True)
print(res.stdout)
print(res.stderr)
