from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.razorpay_client import client
from app.recovery_service import mark_recovery_recovered

router = APIRouter(
    prefix="/recovery",
    tags=["Recovery Verification"],
)


@router.get("/verify/{payment_id}")
def verify_recovery(payment_id: str):

    # -----------------------------------------
    # 1. Get transaction
    # -----------------------------------------

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

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction = dict(transaction)

    # -----------------------------------------
    # 2. Check recovery link ID
    # -----------------------------------------

    recovery_link_id = transaction.get(
        "recovery_link_id"
    )

    if not recovery_link_id:

        conn.close()

        return {
            "payment_id": payment_id,
            "verified": False,
            "status": "verification_unavailable",
            "message": (
                "This recovery link was created before "
                "Recovery Link ID tracking was enabled"
            )
        }

    # -----------------------------------------
    # 3. Fetch exact Payment Link from Razorpay
    # -----------------------------------------

    try:

        payment_link = client.payment_link.fetch(
            recovery_link_id
        )

    except Exception as e:

        conn.close()

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to fetch Razorpay Payment Link: "
                f"{str(e)}"
            )
        )

    # -----------------------------------------
    # 4. Verify reference ID
    # -----------------------------------------

    expected_reference_id = (
        f"recovery_{payment_id}"
    )

    actual_reference_id = payment_link.get(
        "reference_id"
    )

    if actual_reference_id != expected_reference_id:

        conn.close()

        return {
            "payment_id": payment_id,
            "verified": False,
            "status": "reference_mismatch",
            "expected_reference_id": expected_reference_id,
            "actual_reference_id": actual_reference_id,
            "message": (
                "Razorpay Payment Link reference ID "
                "does not match the transaction"
            )
        }

    # -----------------------------------------
    # 5. Get Razorpay status
    # -----------------------------------------

    razorpay_status = payment_link.get(
        "status"
    )

    # -----------------------------------------
    # 6. Payment successfully recovered
    # -----------------------------------------

    if razorpay_status == "paid":
        success = mark_recovery_recovered(payment_id)

        conn.close()

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Unable to mark recovery as recovered"
                )


        return {
            "payment_id": payment_id,
            "verified": True,
            "status": "recovered",
            "razorpay_status": razorpay_status,
            "recovery_link_id": recovery_link_id,
            "reference_id": actual_reference_id,
            "message": (
                "Recovery payment successfully verified"
            )
        }

    # -----------------------------------------
    # 7. Payment Link exists but isn't paid
    # -----------------------------------------

    conn.execute(
        """
        UPDATE transactions
        SET recovery_status = ?
        WHERE payment_id = ?
        """,
        ("pending", payment_id)
    )

    conn.commit()
    conn.close()

    return {
        "payment_id": payment_id,
        "verified": False,
        "status": "pending",
        "razorpay_status": razorpay_status,
        "recovery_link_id": recovery_link_id,
        "reference_id": actual_reference_id,
        "message": (
            "Recovery Payment Link exists but "
            "payment is not completed"
        )
    }