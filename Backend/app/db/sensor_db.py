import sqlite3
from app.config.config import SENSOR_DB_PATH


def init_sensor_db():
    conn = sqlite3.connect(SENSOR_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temp REAL,
            pressure REAL,
            co_mean REAL,
            co_max REAL,
            co_valid INTEGER,
            pm2_5 REAL,
            pm10 REAL,
            co2 REAL
        )
    """)

    conn.commit()
    conn.close()


def insert_sensor_reading(r):
    conn = sqlite3.connect(SENSOR_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sensor_readings
        (timestamp, temp, pressure, co_mean, co_max, co_valid, pm2_5, pm10, co2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        r["timestamp"], r["temp"], r["pressure"],
        r["co_mean"], r["co_max"],
        1 if r["co_valid"] else 0,
        r["pm2_5"], r["pm10"], r["co2"]
    ))

    conn.commit()
    conn.close()
