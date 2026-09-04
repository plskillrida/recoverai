import os
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise RuntimeError(
        "Razorpay API credentials are missing. Check your .env file."
    )

if not RAZORPAY_WEBHOOK_SECRET:
    raise RuntimeError(
        "Razorpay webhook secret is missing. Check your .env file."
    )