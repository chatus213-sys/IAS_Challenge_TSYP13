from app.metrics.co_metrics import compute_co_ceiling
from app.metrics.pm_metrics import process_pm_metrics
from app.config.thresholds import CO_LIMITS, CO2_LIMITS
from app.metrics.temp_pressure_wbgt import (
    build_environment_alert,
    classify_pressure,
    classify_temp,
    compute_wbgt,
    level_to_severity,
    process_wbgt,
    wbgt_level_to_severity,
)
from app.metrics.co_alerts import process_co_alerts

def _classify_from_limits(value, limits):
    if isinstance(limits, dict):
        thresholds = sorted(limits.items(), key=lambda item: item[1][0])
        for level, (low, high) in thresholds:
            if low <= value < high:
                return level, low, high
    else:
        for level, low, high in limits:
            if low <= value < high:
                return level, low, high

    return "unknown", None, None

def evaluate_all_metrics(reading):
    ts = reading["timestamp"]

    metrics = []
    alerts = []
    results = {}
    status_packet = {"timestamp": ts}

    # -------------------------
    # CO Ceiling (instant)
    # -------------------------
    co_ceiling_m = compute_co_ceiling(ts, reading["co_max"])
    metrics.append(co_ceiling_m)
    co_level = _classify_from_limits(reading["co_max"], CO_LIMITS)
    co_status = {
        "value": reading["co_max"],
        "level": co_level[0],
        "severity": level_to_severity(co_level[0]),
    }
    results["co"] = co_status

    # -------------------------
    # CO2 (air quality / ventilation)
    # -------------------------
    co2_level = _classify_from_limits(reading["co2"], CO2_LIMITS)
    co2_status = {
        "value": reading["co2"],
        "level": co2_level[0],
        "severity": level_to_severity(co2_level[0]),
    }

    # -------------------------
    # PM Metrics
    # -------------------------
    pm = process_pm_metrics(ts, reading["pm2_5"], reading["pm10"])
    for key, metric in pm.items():
        metrics.append({
            "timestamp": ts,
            "type": f"{key.upper()}_LEVEL",
            "value": metric["value"],
            "window": "instant",
            "limit": metric["high"],
            "status": metric["level"],
        })
    # Alerts are generated inside process_pm_metrics

    # -------------------------
    # CO STEL/TWA Alerts
    # (you can integrate STEL/TWA code)
    # -------------------------
    co_stel = None       # compute if needed
    co_twa = None        # compute if needed
    ceiling = reading["co_max"]

    co_alert_list = process_co_alerts(ts, co_stel, co_twa, ceiling)
    alerts.extend(co_alert_list)

    # -------------------------
    # Temperature / Pressure
    # -------------------------
    temp_lvl = classify_temp(reading["temp"])
    pressure_lvl = classify_pressure(reading["pressure"])

    # WBGT  (approx)
    wbgt_val = compute_wbgt(reading["temp"])
    wbgt_status, wbgt_alert = process_wbgt(ts, wbgt_val)
    results["wbgt"] = wbgt_status
    temp_severity = level_to_severity(temp_lvl[0])
    pressure_severity = level_to_severity(pressure_lvl[0])
    wbgt_severity = wbgt_level_to_severity(wbgt_status["level"])

    # Add them as passive metrics (no alerts yet)
    metrics.append({
        "timestamp": ts,
        "type": "TEMP_LEVEL",
        "value": reading["temp"],
        "window": "instant",
        "limit": temp_lvl[2],
        "status": temp_lvl[0]
    })

    metrics.append({
        "timestamp": ts,
        "type": "PRESSURE_LEVEL",
        "value": reading["pressure"],
        "window": "instant",
        "limit": pressure_lvl[2],
        "status": pressure_lvl[0]
    })

    metrics.append({
        "timestamp": ts,
        "type": "CO2_LEVEL",
        "value": reading["co2"],
        "window": "instant",
        "limit": co2_level[2],
        "status": co2_level[0],
    })

    metrics.append({
        "timestamp": ts,
        "type": "WBGT",
        "value": wbgt_status["value"],
        "window": "instant",
        "limit": wbgt_status["range"][1],
        "status": wbgt_status["level"]
    })
    if wbgt_alert:
        alerts.append(wbgt_alert)
    # Add alerts for non-green levels
    for alert in (
        build_environment_alert("TEMP", ts, reading["temp"], temp_lvl),
        build_environment_alert("PRESSURE", ts, reading["pressure"], pressure_lvl),
        build_environment_alert("CO2", ts, reading["co2"], co2_level),
    ):
        if alert:
            alerts.append(alert)
        status_packet.update(
        {
            "co": co_status,
            "co2": co2_status,
            "pm": {
                "pm2_5": {
                    "value": pm["pm2_5"]["value"],
                    "level": pm["pm2_5"]["level"],
                    "severity": pm["pm2_5"]["severity"],
                },
                "pm10": {
                    "value": pm["pm10"]["value"],
                    "level": pm["pm10"]["level"],
                    "severity": pm["pm10"]["severity"],
                },
            },
            "temp": {
                "value": reading["temp"],
                "level": temp_lvl[0],
                "severity": temp_severity,
            },
            "wbgt": {
                "value": wbgt_status["value"],
                "level": wbgt_status["level"],
                "severity": wbgt_severity,
            },
            "pressure": {
                "value": reading["pressure"],
                "level": pressure_lvl[0],
                "severity": pressure_severity,
            },
        }
    )
    results["status_packet"] = status_packet

    return {
        "metrics": metrics,
        "alerts": alerts,
        "results": results,
    }
