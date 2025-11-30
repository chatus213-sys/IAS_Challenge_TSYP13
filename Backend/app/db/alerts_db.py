import sqlite3
from app.config.config import ALERTS_DB_PATH


def init_alerts_db():
    conn = sqlite3.connect(ALERTS_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            value REAL NOT NULL,
            limit_value REAL NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_alert_record(alert):
    conn = sqlite3.connect(ALERTS_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO alerts (timestamp, category, value, limit_value, severity, message)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        alert["timestamp"], alert["category"], alert["value"],
        alert["limit"], alert["severity"], alert["message"]
    ))

    conn.commit()
    conn.close()

# Backward-compatible alias used by some call sites/documentation
def insert_alert(alert):
    """Insert an alert record (alias for insert_alert_record)."""
    insert_alert_record(alert)