import sqlite3
from app.config.config import METRICS_DB_PATH


def init_metrics_db():
    conn = sqlite3.connect(METRICS_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            value REAL NOT NULL,
            window TEXT NOT NULL,
            limit_value REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_metric_record(m):
    conn = sqlite3.connect(METRICS_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO metrics (timestamp, metric_type, value, window, limit_value, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        m["timestamp"], m["type"], m["value"],
        m["window"], m["limit"], m["status"]
    ))

    conn.commit()
    conn.close()
