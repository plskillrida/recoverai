from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.recovery_engine import analyze_payment

router = APIRouter(
    prefix="/recoveries",
    tags=["Recoveries"],
)


@router.get("")
def get_recoveries():

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

    transactions = conn.execute(
        """
        SELECT
            payment_id,
            order_id,
            amount,
            currency,
            status,
            method,
            error_code,
            error_description,
            recovery_link,
            recovery_status,
            created_at
        FROM transactions
        WHERE recovery_link IS NOT NULL
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    recoveries = []

    for transaction in transactions:

        transaction = dict(transaction)

        decision = analyze_payment(transaction)

        recoveries.append({
            "payment_id": transaction["payment_id"],
            "order_id": transaction["order_id"],
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "method": transaction["method"],
            "error_code": transaction["error_code"],
            "error_description": transaction["error_description"],
            "recovery_link": transaction["recovery_link"],
            "recovery_status": transaction["recovery_status"],
            "decision": decision,
            "created_at": transaction["created_at"],
        })

    return recoveries

# --------------------------------------------------
# UPDATE RECOVERY STATUS
# --------------------------------------------------

@router.patch("/{payment_id}/status")
def update_recovery_status(
    payment_id: str,
    status: str
):

    allowed_statuses = {
        "initiated",
        "pending",
        "recovered",
        "failed",
        "expired"
    }

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid recovery status. "
                "Use: initiated, pending, recovered, failed, expired"
            )
        )

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

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

    # Make sure a recovery actually exists
    if not transaction["recovery_link"]:
        conn.close()

        raise HTTPException(
            status_code=400,
            detail="No recovery link exists for this payment"
        )

    conn.execute(
        """
        UPDATE transactions
        SET recovery_status = ?
        WHERE payment_id = ?
        """,
        (
            status,
            payment_id
        )
    )

    conn.commit()

    updated_status = conn.execute(
        """
        SELECT recovery_status
        FROM transactions
        WHERE payment_id = ?
        """,
        (payment_id,)
    ).fetchone()["recovery_status"]

    conn.close()

    return {
        "payment_id": payment_id,
        "recovery_status": updated_status,
        "message": "Recovery status updated successfully"
    }