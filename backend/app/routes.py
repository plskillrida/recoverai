from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.recovery_engine import analyze_payment
from app.recovery_actions import create_recovery_payment_link
from .razorpay_client import client


router = APIRouter(
    prefix="/razorpay",
    tags=["Razorpay"],
)


# --------------------------------------------------
# ANALYZE A FAILED PAYMENT
# --------------------------------------------------

@router.get("/recovery/analyze/{payment_id}")
def analyze_recovery(payment_id: str):

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

    conn.close()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction = dict(transaction)

    decision = analyze_payment(transaction)

    return {
        "payment_id": payment_id,
        "amount": transaction["amount"],
        "currency": transaction["currency"],
        "decision": decision
    }


# --------------------------------------------------
# EXECUTE RECOVERY
# --------------------------------------------------

@router.post("/recovery/execute/{payment_id}")
def execute_recovery(payment_id: str):

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

    conn.close()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction = dict(transaction)

    decision = analyze_payment(transaction)

    if not decision["eligible"]:
        return {
            "payment_id": payment_id,
            "status": "not_executed",
            "reason": decision["reason"]
        }

    if decision["action"] != "retry_payment":
        return {
            "payment_id": payment_id,
            "status": "not_executed",
            "reason": "Recovery action is not supported"
        }

    # Create a new recovery link only if one
    # does not already exist.
    payment_link = create_recovery_payment_link(transaction)

    return {
        "payment_id": payment_id,
        "status": (
            "recovery_reused"
            if payment_link["reused"]
            else "recovery_initiated"
        ),
        "action": decision["action"],
        "payment_link": payment_link["short_url"],
        "reused": payment_link["reused"],
        "recovery_status": payment_link["recovery_status"],
        "amount": transaction["amount"],
        "currency": transaction["currency"],
    }

# --------------------------------------------------
# CREATE TEST FAILED TRANSACTION
# --------------------------------------------------

@router.post("/test-transaction")
def create_test_transaction():
    conn = get_connection()

    # Find the latest test transaction number
    rows = conn.execute("""
        SELECT payment_id
        FROM transactions
        WHERE payment_id LIKE 'pay_test_%'
    """).fetchall()

    numbers = []

    for row in rows:
        try:
            number = int(row[0].replace("pay_test_", ""))
            numbers.append(number)
        except ValueError:
            pass

    next_number = max(numbers, default=0) + 1

    payment_id = f"pay_test_{next_number:03d}"
    order_id = f"order_test_{next_number:03d}"

    conn.execute("""
        INSERT INTO transactions (
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        payment_id,
        order_id,
        249900,
        "INR",
        "failed",
        "card",
        "BAD_REQUEST_ERROR",
        "Card payment failed",
        None,
        None,
    ))

    conn.commit()
    conn.close()

    return {
        "payment_id": payment_id,
        "order_id": order_id,
        "status": "failed",
        "amount": 249900,
        "currency": "INR",
        "message": "Test failed transaction created"
    }

# --------------------------------------------------
# CREATE TEST RAZORPAY ORDER
# --------------------------------------------------

@router.post("/test-order")
def create_test_order():

    order = client.order.create(
        {
            "amount": 50000,
            "currency": "INR",
            "receipt": "recoverai_test_001",
        }
    )

    return order

# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------

@router.get("/dashboard/summary")
def dashboard_summary():

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

    # Total failed payments
    failed_result = conn.execute(
        """
        SELECT
            COUNT(*) AS count,
            COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE status = 'failed'
        """
    ).fetchone()

    # Recovered payments
    recovered_result = conn.execute(
        """
        SELECT
            COUNT(*) AS count,
            COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE recovery_status = 'recovered'
        """
    ).fetchone()

    # Recovery links
    links_result = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE recovery_link IS NOT NULL
        """
    ).fetchone()

    conn.close()

    failed_amount = failed_result["amount"]
    recovered_amount = recovered_result["amount"]

    recovery_rate = 0

    if failed_amount > 0:
        recovery_rate = round(
            (recovered_amount / failed_amount) * 100,
            2
        )

    return {
        "revenue_at_risk": failed_amount,
        "revenue_recovered": recovered_amount,
        "failed_payments": failed_result["count"],
        "recovery_links": links_result["count"],
        "recovered_payments": recovered_result["count"],
        "recovery_rate": recovery_rate,
    }
# --------------------------------------------------
# DASHBOARD TRANSACTIONS
# --------------------------------------------------

@router.get("/dashboard/transactions")
def dashboard_transactions():

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

    transactions = conn.execute(
        """
        SELECT
            payment_id,
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
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    return {
        "transactions": [
            dict(transaction)
            for transaction in transactions
        ]
    }