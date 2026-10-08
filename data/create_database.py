import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "database.sqlite"

transactions = [
    ("2026-01-15", "Houston", "Software", 1200.00, "Completed"),
    ("2026-01-22", "Dallas", "Advisory", 2400.00, "Completed"),
    ("2026-02-03", "Houston", "Tax", 1800.00, "Completed"),
    ("2026-02-14", "Austin", "Software", 950.00, "Pending"),
    ("2026-02-28", "Dallas", "Advisory", 3100.00, "Completed"),
    ("2026-03-05", "Houston", "Tax", 2100.00, "Completed"),
    ("2026-03-18", "Austin", "Software", 1450.00, "Cancelled"),
    ("2026-03-27", "Dallas", "Tax", 1750.00, "Completed"),
]

with sqlite3.connect(DATABASE_PATH) as connection:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT NOT NULL,
            region TEXT NOT NULL,
            service_line TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    connection.execute("DELETE FROM transactions")
    connection.executemany(
        """
        INSERT INTO transactions
        (transaction_date, region, service_line, amount_usd, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        transactions,
    )

print(f"Created synthetic database at {DATABASE_PATH}")
print(f"Inserted {len(transactions)} transactions")