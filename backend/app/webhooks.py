import os
import json
from app.recovery_service import mark_recovery_recovered

from fastapi import APIRouter, Request, Header, HTTPException

from app.database import get_connection
from app.razorpay_client import client


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


# --------------------------------------------------
# RAZORPAY WEBHOOK
# --------------------------------------------------

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None)
):

    # --------------------------------------------------
    # READ RAW REQUEST BODY
    # --------------------------------------------------

    body = await request.body()

    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay signature"
        )

    # --------------------------------------------------
    # WEBHOOK SECRET
    # --------------------------------------------------

    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    print("WEBHOOK SECRET LOADED:", bool(webhook_secret))
    print("WEBHOOK SECRET LENGTH:", len(webhook_secret) if webhook_secret else 0)

    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="RAZORPAY_WEBHOOK_SECRET is not configured"
        )

    # --------------------------------------------------
    # VERIFY RAZORPAY SIGNATURE
    # --------------------------------------------------

    try:
        client.utility.verify_webhook_signature(
            body.decode("utf-8"),
            x_razorpay_signature,
            webhook_secret
        )

    except Exception as e:

        print("WEBHOOK SIGNATURE ERROR:", repr(e))

        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature"
        )

    # --------------------------------------------------
    # PARSE EVENT
    # --------------------------------------------------

    try:
        payload = json.loads(body)

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )

    event = payload.get("event")

    print("RAZORPAY WEBHOOK EVENT:", event)

    # --------------------------------------------------
    # PAYMENT LINK PAID
    # --------------------------------------------------

    if event == "payment_link.paid":

        payment_link_data = (
            payload
            .get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
        )

        reference_id = payment_link_data.get("reference_id")

        print("RECOVERY REFERENCE ID:", reference_id)

        if not reference_id:
            return {
                "status": "ignored",
                "reason": "No reference_id found"
            }

        # --------------------------------------------------
        # CHECK RECOVERAI RECOVERY LINK
        #
        # Expected format:
        # recovery_<payment_id>
        #
        # Example:
        # recovery_pay_test_002
        # --------------------------------------------------

        if not reference_id.startswith("recovery_"):

            return {
                "status": "ignored",
                "reason": "Not a RecoverAI recovery link"
            }

        payment_id = reference_id[len("recovery_"):]

        print("RECOVERY PAYMENT ID:", payment_id)

        # --------------------------------------------------
        # UPDATE DATABASE
        # --------------------------------------------------

        conn = get_connection()

        transaction = conn.execute(
            """
            SELECT *
            FROM transactions
            WHERE payment_id = ?
            """,
            (payment_id,)
        ).fetchone()

        if not transaction:

            conn.close()

            return {
                "status": "ignored",
                "reason": "Transaction not found",
                "payment_id": payment_id
            }

        success = mark_recovery_recovered(payment_id)

        if not success:
            return {
                "status": "ignored",
                "reason": "Unable to mark recovery as recovered",
                "payment_id": payment_id
                }

        print(
            "RECOVERY SUCCESS:",
            payment_id,
            "-> recovered"
            )
        
        return {
            "status": "success",
            "event": event,
            "payment_id": payment_id,
            "recovery_status": "recovered"
        }

    # --------------------------------------------------
    # OTHER EVENTS
    # --------------------------------------------------

    return {
        "status": "ignored",
        "event": event
    }