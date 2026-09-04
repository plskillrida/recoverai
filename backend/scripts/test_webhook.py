import hashlib
import hmac
import json

import requests


WEBHOOK_SECRET = "recoverai_webhook_secret_2026"

payload = {
    "event": "payment.failed",
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test_002",
                "order_id": "order_test_002",
                "amount": 249900,
                "currency": "INR",
                "status": "failed",
                "method": "card",
                "email": "customer@example.com",
                "contact": "9999999999",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Payment failed",
            }
        }
    },
}

body = json.dumps(
    payload,
    separators=(",", ":"),
).encode()

signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    body,
    hashlib.sha256,
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Razorpay-Signature": signature,
    "X-Razorpay-Event-Id": "evt_test_002",
}

response = requests.post(
    "http://127.0.0.1:8000/webhooks/razorpay",
    data=body,
    headers=headers,
)

print("Status:", response.status_code)
print("Response:", response.json())