def validate_payload(d):
    required = [
        "timestamp", "temp", "pressure",
        "co_mean", "co_max", "co_valid",
        "pm2_5", "pm10", "co2"
    ]

    for r in required:
        if r not in d:
            raise ValueError(f"Missing field: {r}")

    return {
        "timestamp": d["timestamp"],
        "temp": float(d["temp"]),
        "pressure": float(d["pressure"]),
        "co_mean": float(d["co_mean"]),
        "co_max": float(d["co_max"]),
        "co_valid": bool(d["co_valid"]),
        "pm2_5": float(d["pm2_5"]),
        "pm10": float(d["pm10"]),
        "co2": float(d["co2"])
    }
