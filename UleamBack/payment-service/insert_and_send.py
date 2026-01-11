import psycopg2
import subprocess
import sys

DB = "postgresql://postgres:123456789@localhost:5432/payment_service_db"

conn = psycopg2.connect(DB)
cur = conn.cursor()
cur.execute("""
INSERT INTO payment (external_payment_id,reserva_id,usuario_id,provider_name,amount,currency,status,metadata_json)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT (external_payment_id) DO NOTHING
""", ("pi_test_123", 1, 1, "stripe", 50.00, "USD", "PENDING", '{}'))
conn.commit()
cur.execute("SELECT id, external_payment_id, status, amount FROM payment WHERE external_payment_id=%s", ("pi_test_123",))
row = cur.fetchone()
print('Inserted/Found payment:', row)
cur.close()
conn.close()

# Run the webhook sender
print('Sending webhook...')
res = subprocess.run([sys.executable, 'send_test_stripe_webhook.py'], capture_output=True, text=True)
print('--- send_test_stripe_webhook stdout ---')
print(res.stdout)
print('--- send_test_stripe_webhook stderr ---')
print(res.stderr)
