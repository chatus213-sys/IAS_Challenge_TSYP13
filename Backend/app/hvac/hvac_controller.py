"""
Decides HVAC actions (fan speeds, AC power, mode) based on the
unified status packet produced by the metrics/evaluator.

Expected status_packet structure:

status_packet = {
    "timestamp": "...",
    "co":   {"value": float, "level": str, "severity": str},
    "pm": {
        "pm2_5": {"value": float, "level": str, "severity": str},
        "pm10":  {"value": float, "level": str, "severity": str},
    },
    "temp": {"value": float, "level": str, "severity": str},
    "wbgt": {"value": float, "level": str, "severity": str},
    "pressure": {"value": float, "level": str, "severity": str},
}

Levels:    "green", "yellow", "orange", "red", "dark_red", "purple"
Severity:  "none", "warning", "high", "critical"
"""

from typing import Any, Dict
from datetime import datetime, timezone

def _clamp_percent(x: int) -> int:
    """Clamp fan/AC values into [0, 100]."""
    return max(0, min(100, int(x)))


def decide_hvac_actions(status_packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main HVAC decision function.

    Returns a dict like:
    {
        "ventilation_mode": "NORMAL" | "EMERGENCY_PURGE" | "DUST_CONTROL" | "HEAT_STRESS" | "PRESSURE_CORRECTION",
        "fan_supply_speed": int,  # 0..100
        "fan_exhaust_speed": int, # 0..100
        "ac_power": int,          # 0..100 (0 for now if no AC control)
        "reasons": [str, ...],
    }
    """

    # ---- Default "normal" mode ----
    actions = {
        "timestamp": status_packet.get("timestamp")
        or datetime.now(timezone.utc).isoformat(),
        "ventilation_mode": "NORMAL",
        "fan_supply_speed": 40,
        "fan_exhaust_speed": 30,
        "ac_power": 0,
        "reasons": [],
    }

    # --- Helper to safely read nested values ---
    def get(path, default=None):
        """
        Small helper to read nested values like:
        get(("pm", "pm10", "severity"), "none")
        """
        cur = status_packet
        for p in path:
            if not isinstance(cur, dict) or p not in cur:
                return default
            cur = cur[p]
        return cur

    # ------------------------------------------------
    # 1) CO — PRIORITY #1 (Toxic gas)
    # ------------------------------------------------
    co_severity = get(("co", "severity"), "none")
    co_level = get(("co", "level"), "green")
    co_value = get(("co", "value"), 0.0)

    if co_severity in ("high", "critical"):
        # EMERGENCY_PURGE:
        # - Strong exhaust to push CO out
        # - Some supply so we don't create too much vacuum
        actions["ventilation_mode"] = "EMERGENCY_PURGE"
        actions["fan_exhaust_speed"] = 100
        actions["fan_supply_speed"] = 40
        actions["ac_power"] = 0
        actions["reasons"].append(
            f"CO {co_level.upper()} ({co_value:.1f} ppm) → EMERGENCY_PURGE"
        )
        # CO danger overrides all other conditions
        return _finalize_actions(actions)
    
    co2_severity = get(("co2", "severity"), "none")
    co2_value = get(("co2", "value"), 0.0)
    co2_level = get(("co2", "level"), "green")

    if co2_severity in ("high", "critical"):
        actions["ventilation_mode"] = "CO2_PURGE"
        actions["fan_supply_speed"] = max(actions["fan_supply_speed"], 90)
        actions["fan_exhaust_speed"] = max(actions["fan_exhaust_speed"], 75)
        actions["reasons"].append(
            f"CO2 {co2_level.upper()} ({co2_value:.0f} ppm) → increase fresh air"
        )
    elif co2_severity == "warning":
        actions["fan_supply_speed"] = max(actions["fan_supply_speed"], 70)
        actions["fan_exhaust_speed"] = max(actions["fan_exhaust_speed"], 55)
        actions["reasons"].append(
            f"CO2 warning ({co2_value:.0f} ppm) → boost ventilation"
        )

    # ------------------------------------------------
    # 2) PM (Dust) — PM2.5 / PM10
    # ------------------------------------------------
    pm25_sev = get(("pm", "pm2_5", "severity"), "none")
    pm10_sev = get(("pm", "pm10", "severity"), "none")
    pm25_val = get(("pm", "pm2_5", "value"), 0.0)
    pm10_val = get(("pm", "pm10", "value"), 0.0)
    pm25_lvl = get(("pm", "pm2_5", "level"), "green")
    pm10_lvl = get(("pm", "pm10", "level"), "green")

    # If any PM is dangerous
    if pm25_sev in ("high", "critical") or pm10_sev in ("high", "critical"):
        actions["ventilation_mode"] = "DUST_CONTROL"
        actions["fan_exhaust_speed"] = 90   # strong exhaust
        actions["fan_supply_speed"] = 60    # keep enough fresh air
        actions["ac_power"] = 0
        actions["reasons"].append(
            f"PM danger: PM2.5={pm25_val:.1f}µg/m³ ({pm25_lvl}), PM10={pm10_val:.1f}µg/m³ ({pm10_lvl})"
        )

    # Moderate dust: warning only
    elif pm25_sev == "warning" or pm10_sev == "warning":
        actions["ventilation_mode"] = "DUST_CONTROL"
        actions["fan_exhaust_speed"] = max(actions["fan_exhaust_speed"], 70)
        actions["fan_supply_speed"] = max(actions["fan_supply_speed"], 50)
        actions["reasons"].append(
            f"PM warning: PM2.5={pm25_val:.1f}µg/m³ ({pm25_lvl}), PM10={pm10_val:.1f}µg/m³ ({pm10_lvl})"
        )

    # (if no PM issue, we keep whatever actions we already have)

    # ------------------------------------------------
    # 3) Temperature / WBGT — Heat stress
    # ------------------------------------------------
    temp_sev = get(("temp", "severity"), "none")
    temp_val = get(("temp", "value"), 0.0)
    temp_lvl = get(("temp", "level"), "green")

    wbgt_sev = get(("wbgt", "severity"), "none")
    wbgt_val = get(("wbgt", "value"), 0.0)
    wbgt_lvl = get(("wbgt", "level"), "green")

    # Heat stress if either temp or WBGT is high
    if wbgt_sev in ("high", "critical") or temp_sev in ("high", "critical"):
        actions["ventilation_mode"] = "HEAT_STRESS"
        actions["fan_supply_speed"] = max(actions["fan_supply_speed"], 80)
        actions["fan_exhaust_speed"] = max(actions["fan_exhaust_speed"], 60)
        actions["ac_power"] = max(actions["ac_power"], 80)
        actions["reasons"].append(
            f"Heat danger: Temp={temp_val:.1f}°C ({temp_lvl}), WBGT={wbgt_val:.1f}°C ({wbgt_lvl})"
        )

    elif wbgt_sev == "warning" or temp_sev == "warning":
        # Moderate heat → increase supply, some exhaust
        if actions["ventilation_mode"] == "NORMAL":
            actions["ventilation_mode"] = "HEAT_STRESS"
        actions["fan_supply_speed"] = max(actions["fan_supply_speed"], 60)
        actions["fan_exhaust_speed"] = max(actions["fan_exhaust_speed"], 50)
        actions["ac_power"] = max(actions["ac_power"], 50)
        actions["reasons"].append(
            f"Heat warning: Temp={temp_val:.1f}°C ({temp_lvl}), WBGT={wbgt_val:.1f}°C ({wbgt_lvl})"
        )

    # ------------------------------------------------
    # 4) Pressure — HVAC balance (supply vs exhaust)
    # ------------------------------------------------
    pressure_val = get(("pressure", "value"), 1015.0)
    pressure_lvl = get(("pressure", "level"), "green")
    pressure_sev = get(("pressure", "severity"), "none")

    # Example thresholds: normal ~ 1005–1025 hPa
    # If pressure is low → increase supply
    if pressure_lvl in ("orange", "red") and pressure_val < 1005:
        actions["fan_supply_speed"] += 15
        actions["reasons"].append(
            f"Low pressure ({pressure_val:.1f} hPa) → increase supply"
        )

    # If pressure is high → increase exhaust
    if pressure_lvl in ("orange", "red") and pressure_val > 1025:
        actions["fan_exhaust_speed"] += 15
        actions["reasons"].append(
            f"High pressure ({pressure_val:.1f} hPa) → increase exhaust"
        )

    # If pressure itself is severe anomaly:
    if pressure_sev in ("high", "critical"):
        if actions["ventilation_mode"] == "NORMAL":
            actions["ventilation_mode"] = "PRESSURE_CORRECTION"
        actions["reasons"].append(
            f"Pressure anomaly severity={pressure_sev}"
        )

    # Final clamp and cleanup
    return _finalize_actions(actions)


def _finalize_actions(actions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure fan and AC values are within [0, 100] and deduplicate reasons.
    """
    actions["fan_supply_speed"] = _clamp_percent(actions.get("fan_supply_speed", 0))
    actions["fan_exhaust_speed"] = _clamp_percent(actions.get("fan_exhaust_speed", 0))
    actions["ac_power"] = _clamp_percent(actions.get("ac_power", 0))

    # Remove duplicate reasons while keeping order
    seen = set()
    unique_reasons = []
    for r in actions.get("reasons", []):
        if r not in seen:
            unique_reasons.append(r)
            seen.add(r)
    actions["reasons"] = unique_reasons

    return actions