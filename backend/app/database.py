import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "recoverai.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():

    connection = get_connection()

    # -----------------------------------------
    # Users
    # -----------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # -----------------------------------------
    # Webhook events
    # -----------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # -----------------------------------------
    # Transactions
    # -----------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT UNIQUE,
            order_id TEXT,
            amount INTEGER,
            currency TEXT,
            status TEXT,
            method TEXT,
            email TEXT,
            contact TEXT,
            error_code TEXT,
            error_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # -----------------------------------------
    # Recovery columns
    # -----------------------------------------

    columns = connection.execute(
        "PRAGMA table_info(transactions)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "recovery_link" not in column_names:

        connection.execute(
            """
            ALTER TABLE transactions
            ADD COLUMN recovery_link TEXT
            """
        )

    if "recovery_status" not in column_names:

        connection.execute(
            """
            ALTER TABLE transactions
            ADD COLUMN recovery_status TEXT
            """
        )

    if "recovery_link_id" not in column_names:

        connection.execute(
            """
            ALTER TABLE transactions
            ADD COLUMN recovery_link_id TEXT
            """
        )

    connection.commit()
    connection.close()