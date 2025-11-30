import json
import sqlite3

from app.config.config import VENTILATION_DB_PATH


def init_ventilation_db():
    conn = sqlite3.connect(VENTILATION_DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ventilation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            mode TEXT NOT NULL,
            fan_supply INTEGER NOT NULL,
            fan_exhaust INTEGER NOT NULL,
            ac_power INTEGER NOT NULL,
            reasons TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def insert_ventilation_record(record):
    conn = sqlite3.connect(VENTILATION_DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO ventilation_history
            (timestamp, mode, fan_supply, fan_exhaust, ac_power, reasons)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            record["timestamp"],
            record["ventilation_mode"],
            record["fan_supply_speed"],
            record["fan_exhaust_speed"],
            record["ac_power"],
            json.dumps(record.get("reasons", [])),
        ),
    )

    conn.commit()
    conn.close()