import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import get_connection


connection = get_connection()

transactions = connection.execute(
    """
    SELECT *
    FROM transactions
    ORDER BY id DESC
    """
).fetchall()

connection.close()

for transaction in transactions:
    print(dict(transaction))