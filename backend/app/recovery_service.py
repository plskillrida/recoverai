from app.database import get_connection


def mark_recovery_recovered(payment_id: str):
    """
    Mark a transaction as recovered.
    Used by both webhook handling and API verification.
    """

    conn = get_connection()

    transaction = conn.execute(
        """
        SELECT payment_id, recovery_link, recovery_status
        FROM transactions
        WHERE payment_id = ?
        """,
        (payment_id,)
    ).fetchone()

    if not transaction:
        conn.close()
        return False

    if not transaction["recovery_link"]:
        conn.close()
        return False

    conn.execute(
        """
        UPDATE transactions
        SET recovery_status = ?
        WHERE payment_id = ?
        """,
        ("recovered", payment_id)
    )

    conn.commit()
    conn.close()

    print(
        "RECOVERY MARKED AS RECOVERED:",
        payment_id
    )

    return True