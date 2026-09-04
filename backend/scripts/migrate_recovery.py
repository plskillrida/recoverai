import sys
from pathlib import Path
import sqlite3

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))


# recoverai.db is inside the backend folder
DATABASE_PATH = Path(__file__).resolve().parent.parent / "recoverai.db"

connection = sqlite3.connect(DATABASE_PATH)


# --------------------------------------------------
# Add recovery_link column
# --------------------------------------------------

try:
    connection.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN recovery_link TEXT
        """
    )

    print("Added recovery_link column.")

except sqlite3.OperationalError as e:

    if "duplicate column name" in str(e).lower():
        print("recovery_link column already exists.")
    else:
        raise


# --------------------------------------------------
# Add recovery_status column
# --------------------------------------------------

try:
    connection.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN recovery_status TEXT
        """
    )

    print("Added recovery_status column.")

except sqlite3.OperationalError as e:

    if "duplicate column name" in str(e).lower():
        print("recovery_status column already exists.")
    else:
        raise


connection.commit()
connection.close()

print("Database migration complete.")