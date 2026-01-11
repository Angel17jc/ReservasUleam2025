import os, time, json, hmac, hashlib, requests

# Read webhook secret from .env (fallback to environment)
secret = os.getenv('STRIPE_WEBHOOK_SECRET')
if not secret:
    # try reading .env file in current dir
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('STRIPE_WEBHOOK_SECRET='):
                    secret = line.strip().split('=',1)[1]
                    break

if not secret:
    raise SystemExit('STRIPE_WEBHOOK_SECRET not found in env or .env')

# Build fake stripe event
timestamp = int(time.time())
event = {
    "id": "evt_test_123",
    "type": "payment_intent.succeeded",
    "data": {
        "object": {
            "id": "pi_test_123",
            "amount": 5000,
            "currency": "usd",
            "status": "succeeded",
            "metadata": {}
        }
    },
    "created": timestamp
}

payload = json.dumps(event, separators=(',',':'))

signed_payload = f"{timestamp}.{payload}"

sig = hmac.new(secret.encode('utf-8'), signed_payload.encode('utf-8'), hashlib.sha256).hexdigest()
header = f"t={timestamp},v1={sig}"

url = 'http://127.0.0.1:8001/api/v1/webhooks/providers/stripe'
print('Sending webhook to', url)
print('Stripe-Signature header:', header)

resp = requests.post(url, data=payload, headers={
    'Content-Type':'application/json',
    'Stripe-Signature': header
})

print('Response status:', resp.status_code)
try:
    print('Response body:', resp.json())
except Exception:
    print('Response text:', resp.text)
