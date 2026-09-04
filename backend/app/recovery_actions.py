from app.razorpay_client import client
from app.database import get_connection


def create_recovery_payment_link(transaction):

    connection = get_connection()

    # -----------------------------------------
    # Check whether a recovery link already
    # exists for this transaction
    # -----------------------------------------

    existing = connection.execute(
        """
        SELECT
            recovery_link,
            recovery_link_id,
            recovery_status
        FROM transactions
        WHERE payment_id = ?
        """,
        (transaction["payment_id"],)
    ).fetchone()

    if existing and existing["recovery_link"]:

        connection.close()

        return {
            "short_url": existing["recovery_link"],
            "recovery_link_id": existing["recovery_link_id"],
            "reused": True,
            "recovery_status": existing["recovery_status"],
        }

    # -----------------------------------------
    # Create new Razorpay Payment Link
    # -----------------------------------------

    payment_link = client.payment_link.create(
        {
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "description": "RecoverAI payment recovery",

            "reference_id": (
                f"recovery_{transaction['payment_id']}"
            ),

            "customer": {
                "email": transaction["email"],
                "contact": "9876543210",
            },
        }
    )

    # -----------------------------------------
    # Extract Razorpay Payment Link details
    # -----------------------------------------

    short_url = payment_link["short_url"]

    recovery_link_id = payment_link["id"]

    # -----------------------------------------
    # Save everything to database
    # -----------------------------------------

    connection.execute(
        """
        UPDATE transactions
        SET
            recovery_link = ?,
            recovery_link_id = ?,
            recovery_status = ?
        WHERE payment_id = ?
        """,
        (
            short_url,
            recovery_link_id,
            "initiated",
            transaction["payment_id"],
        )
    )

    connection.commit()
    connection.close()

    return {
        "short_url": short_url,
        "recovery_link_id": recovery_link_id,
        "reused": False,
        "recovery_status": "initiated",
    }