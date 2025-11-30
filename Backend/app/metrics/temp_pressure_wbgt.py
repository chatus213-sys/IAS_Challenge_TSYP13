import math

from app.config.thresholds import TEMP_LIMITS, PRESSURE_LIMITS, WBGT_THRESHOLDS
from app.db.alerts_db import insert_alert

DEFAULT_WBGT_RH = 40


def estimate_wet_bulb(temp_c: float, humidity: float = DEFAULT_WBGT_RH) -> float:
    """Estimate wet-bulb temperature using Stull approximation (2011).

    Defaults to 40% RH as a stand-in when no humidity sensor is present.
    """

    T = temp_c
    RH = humidity

    return (
        T * math.atan(0.151977 * math.sqrt(RH + 8.313659))
        + math.atan(T + RH)
        - math.atan(RH - 1.676331)
        + 0.00391838 * (RH ** 1.5) * math.atan(0.023101 * RH)
        - 4.686035
    )


def compute_wbgt(temp_c: float, humidity: float = DEFAULT_WBGT_RH) -> float:
    """Approximate WBGT using wet-bulb estimate and dry-bulb temperature.

    When no humidity reading is provided, a 40% default is used to match the
    agreed-upon baseline for environments without a dedicated humidity sensor.
    """

    twb = estimate_wet_bulb(temp_c, humidity)
    return 0.7 * twb + 0.3 * temp_c


def _classify(value, limits):
    if isinstance(limits, dict):
        thresholds = ((level, bounds[0], bounds[1]) for level, bounds in limits.items())
    else:
        thresholds = limits

    for level, low, high in thresholds:
        if low <= value < high:
            return level, low, high
    return "unknown", None, None

def _level_to_severity(level: str):
    return {
        "green": "none",
        "yellow": "warning",
        "yellow-low": "warning",
        "yellow-high": "warning",
        "orange-low": "warning",
        "orange-high": "warning",
        "orange": "warning",
        "red-low": "high",
        "red-high": "high",
        "red": "high",
        "dark-red-low": "critical",
        "dark-red-high": "critical",
        "dark-red": "critical",
        "dark_red": "critical",
        "purple-low": "critical",
        "purple-high": "critical",
        "purple": "critical",
    }.get(level, "none")

def level_to_severity(level: str) -> str:
    """Public wrapper for mapping band names to severity strings."""

    return _level_to_severity(level)


def classify_temp(temp):
    return _classify(temp, TEMP_LIMITS)


def classify_pressure(p):
    return _classify(p, PRESSURE_LIMITS)


def classify_wbgt(w):
    return _classify(w, WBGT_THRESHOLDS)

def process_wbgt(timestamp, wbgt_value):
    level, low, high = classify_wbgt(wbgt_value)

    alert = None
    severity = wbgt_level_to_severity(level)
    if severity != "none":
        alert = {
            "timestamp": timestamp,
            "category": "WBGT",
            "value": wbgt_value,
            "limit": high,
            "severity": severity,
            "message": f"WBGT={wbgt_value:.1f}°C → {level.upper()} risk level",
        }

    return {
        "value": wbgt_value,
        "level": level,
        "range": (low, high),
    }, alert


def wbgt_level_to_severity(level: str) -> str:
    if level in ("green", "yellow", "unknown"):
        return "none"
    if level == "orange":
        return "warning"
    return "critical"

def build_environment_alert(category: str, timestamp: str, value: float, level_data):
    level, low, high = level_data
    severity = _level_to_severity(level)

    if severity == "none":
        return None

    return {
        "timestamp": timestamp,
        "category": category,
        "value": value,
        "limit": high,
        "severity": severity,
        "message": f"{category}={value} is {level.upper()} ({low}-{high})"
    }
