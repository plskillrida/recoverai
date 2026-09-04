from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.recovery_engine import analyze_payment


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------

@router.get("/summary")
def dashboard_summary():

    conn = get_connection()

    revenue_at_risk = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE status = 'failed'
        """
    ).fetchone()[0]

    revenue_recovered = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE recovery_status = 'recovered'
        """
    ).fetchone()[0]

    failed_payments = conn.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE status = 'failed'
        """
    ).fetchone()[0]

    recovery_links = conn.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE recovery_link IS NOT NULL
        """
    ).fetchone()[0]

    # Get latest failed transaction for AI decision
    latest = conn.execute(
        """
        SELECT *
        FROM transactions
        WHERE status = 'failed'
        ORDER BY created_at DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    if revenue_at_risk > 0:
        recovery_rate = round(
            (revenue_recovered / revenue_at_risk) * 100,
            2
        )
    else:
        recovery_rate = 0

    # AI decision
    ai_decision = None

    if latest:
        latest = dict(latest)
        ai_decision = analyze_payment(latest)

    return {
        "revenue_at_risk": revenue_at_risk,
        "revenue_recovered": revenue_recovered,
        "recovery_rate": recovery_rate,
        "failed_payments": failed_payments,
        "recovery_links": recovery_links,
        "ai_decision": ai_decision,
    }


# --------------------------------------------------
# RECENT FAILED TRANSACTIONS
# --------------------------------------------------

@router.get("/transactions")
def dashboard_transactions():

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

    transactions = conn.execute(
        """
        SELECT
            payment_id,
            amount,
            currency,
            method,
            error_code,
            status,
            recovery_link,
            recovery_status,
            created_at
        FROM transactions
        WHERE status = 'failed'
        ORDER BY created_at DESC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    return [dict(transaction) for transaction in transactions]


# --------------------------------------------------
# SINGLE TRANSACTION
# --------------------------------------------------

@router.get("/transactions/{payment_id}")
def get_transaction(payment_id: str):

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
        "transaction": transaction,
        "decision": decision
    }