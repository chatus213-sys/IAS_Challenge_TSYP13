from app.db.alerts_db import insert_alert_record
from app.config.thresholds import CO_STEL, CO_TWA, CO_CEILING


def process_co_alerts(timestamp, stel, twa, ceiling):
    alerts = []

    if stel is not None and stel > CO_STEL:
        alerts.append({
            "timestamp": timestamp,
            "category": "CO_STEL",
            "value": stel,
            "limit": CO_STEL,
            "severity": "high",
            "message": f"CO STEL exceeded: {stel} > {CO_STEL}"
        })

    if twa is not None and twa > CO_TWA:
        alerts.append({
            "timestamp": timestamp,
            "category": "CO_TWA",
            "value": twa,
            "limit": CO_TWA,
            "severity": "warning",
            "message": f"CO TWA exceeded: {twa} > {CO_TWA}"
        })

    if ceiling > CO_CEILING:
        alerts.append({
            "timestamp": timestamp,
            "category": "CO_CEILING",
            "value": ceiling,
            "limit": CO_CEILING,
            "severity": "critical",
            "message": f"CO CEILING exceeded: {ceiling} > {CO_CEILING}"
        })

    for a in alerts:
        insert_alert_record(a)

    return alerts
