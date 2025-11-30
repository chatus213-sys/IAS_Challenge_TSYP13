from app.config.thresholds import CO_STEL, CO_TWA, CO_CEILING
from app.utils.time_utils import parse_timestamp
from app.db.sensor_db import insert_sensor_reading


def compute_co_ceiling(timestamp, co_max):
    return {
        "timestamp": timestamp,
        "type": "CO_CEILING",
        "value": co_max,
        "window": "instant",
        "limit": CO_CEILING,
        "status": "danger" if co_max > CO_CEILING else "safe"
    }
