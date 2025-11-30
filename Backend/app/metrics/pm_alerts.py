from app.db.alerts_db import insert_alert_record

def create_pm_alert(timestamp, category, value, limit, severity):
    insert_alert_record({
        "timestamp": timestamp,
        "category": category,
        "value": value,
        "limit": limit,
        "severity": severity,
        "message": f"{category} exceeded: {value} > {limit}"
    })
