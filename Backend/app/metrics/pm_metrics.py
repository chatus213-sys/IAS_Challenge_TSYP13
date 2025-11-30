from app.db.alerts_db import insert_alert_record
from app.config.thresholds import PM25_LIMITS, PM10_LIMITS


def _classify(value: float, limits: dict):
    for level, (low, high) in limits.items():
        if low <= value < high:
            return level, low, high
    return "unknown", None, None


def _level_to_severity(level):
    return {
        "green": "none",
        "yellow": "none",
        "orange": "warning",
        "red": "high",
        "dark-red": "critical",
        "purple": "critical",
    }.get(level, "none")


def classify_pm25(value):
    level, low, high = _classify(value, PM25_LIMITS)
    severity = _level_to_severity(level)
    return level, severity, low, high


def classify_pm10(value):
    level, low, high = _classify(value, PM10_LIMITS)
    severity = _level_to_severity(level)
    return level, severity, low, high


def process_pm_metrics(timestamp, pm25, pm10):
    results = {}

    # PM2.5
    level25, sev25, low25, high25 = classify_pm25(pm25)
    results["pm2_5"] = {
        "value": pm25,
        "level": level25,
        "severity": sev25,
        "low": low25,
        "high": high25,
    }
    if sev25 != "none":
        insert_alert_record({
            "timestamp": timestamp,
            "category": "PM2.5",
            "value": pm25,
            "limit": high25,
            "severity": sev25,
            "message": f"PM2.5={pm25} is {level25.upper()} ({low25}-{high25})"
        })

    # PM10
    level10, sev10, low10, high10 = classify_pm10(pm10)
    results["pm10"] = {
        "value": pm10,
        "level": level10,
        "severity": sev10,
        "low": low10,
        "high": high10,
    }
    if sev10 != "none":
        insert_alert_record({
            "timestamp": timestamp,
            "category": "PM10",
            "value": pm10,
            "limit": high10,
            "severity": sev10,
            "message": f"PM10={pm10} is {level10.upper()} ({low10}-{high10})"
        })

    return results
