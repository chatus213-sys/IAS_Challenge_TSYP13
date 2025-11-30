import json
import paho.mqtt.client as mqtt

from app.models.validate_payload import validate_payload
from app.db.sensor_db import insert_sensor_reading
from app.metrics.evaluator import evaluate_all_metrics
from app.db.metrics_db import insert_metric_record
from app.db.alerts_db import insert_alert_record
from app.db.ventilation_db import insert_ventilation_record
from app.hvac.hvac_controller import decide_hvac_actions
from app.config.config import (
    MQTT_SERVER,
    MQTT_PORT,
    MQTT_TOPIC,
    MQTT_UNITY_TOPIC,
    MQTT_UNITY_ALERT_TOPIC,
    MQTT_VENTILATION_TOPIC,
)


def _extract_color(level: str) -> str:
    sanitized = (level or "").replace("_", "-")
    return sanitized.split("-")[0] if "-" in sanitized else sanitized or "unknown"


def build_unity_payload(status_packet):
    return {
        "timestamp": status_packet.get("timestamp"),
        "co": _extract_color(status_packet.get("co", {}).get("level", "")),
        "co2": _extract_color(status_packet.get("co2", {}).get("level", "")),
        "pm2_5": _extract_color(
            status_packet.get("pm", {}).get("pm2_5", {}).get("level", "")
        ),
        "pm10": _extract_color(
            status_packet.get("pm", {}).get("pm10", {}).get("level", "")
        ),
        "temp": _extract_color(status_packet.get("temp", {}).get("level", "")),
        "wbgt": _extract_color(status_packet.get("wbgt", {}).get("level", "")),
        "pressure": _extract_color(status_packet.get("pressure", {}).get("level", "")),
    }

def build_unity_alert_messages(status_packet):
    ts = status_packet.get("timestamp")

    severity_rank = {"none": 0, "warning": 1, "high": 2, "critical": 3}

    def _append_if_active(messages, name, data):
        if not data:
            return

        severity = data.get("severity", "none")
        if severity not in {"warning", "high", "critical"}:
            return

        messages.append(
            {
                "gas": name,
                "predicted_value": data.get("value"),
                "level": severity,
                "timestamp": ts,
            }
        )

    alerts = []
    pm = status_packet.get("pm", {})
    _append_if_active(alerts, "co", status_packet.get("co"))
    _append_if_active(alerts, "co2", status_packet.get("co2"))
    _append_if_active(alerts, "pm2_5", pm.get("pm2_5"))
    _append_if_active(alerts, "pm10", pm.get("pm10"))
    _append_if_active(alerts, "temp", status_packet.get("temp"))
    _append_if_active(alerts, "wbgt", status_packet.get("wbgt"))
    _append_if_active(alerts, "pressure", status_packet.get("pressure"))

    if not alerts:
        return []

    def _score(alert):
        base = severity_rank.get(alert.get("level", "none"), 0)
        value = alert.get("predicted_value")
        return (base, value if isinstance(value, (int, float)) else float("-inf"))

    worst = alerts[0]
    worst_score = _score(worst)

    for alert in alerts[1:]:
        score = _score(alert)
        if score > worst_score:
            worst, worst_score = alert, score

    return [worst]



def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        reading = validate_payload(data)

        insert_sensor_reading(reading)

        results = evaluate_all_metrics(reading)

        # Store metrics
        for m in results["metrics"]:
            insert_metric_record(m)

        # Store alerts
        for a in results["alerts"]:
            insert_alert_record(a)

        status_packet = results["results"]["status_packet"]
        ventilation_actions = decide_hvac_actions(status_packet)
        insert_ventilation_record(ventilation_actions)

        publish_payload = dict(ventilation_actions)
        publish_payload.pop("reasons", None)

        client.publish(MQTT_VENTILATION_TOPIC, json.dumps(publish_payload))
        unity_payload = build_unity_payload(status_packet)
        client.publish(MQTT_UNITY_TOPIC, json.dumps(unity_payload))

        unity_alerts = build_unity_alert_messages(status_packet)
        for alert_msg in unity_alerts:
            client.publish(MQTT_UNITY_ALERT_TOPIC, json.dumps(alert_msg))

        print("\n📥 Received:", reading)
        print("📊 Stored metrics, alerts, and ventilation actions.")
        print(f"📡 Published ventilation commands : {publish_payload}")
        print(f"🎮 Sent Unity status payload: {unity_payload}")
        if unity_alerts:
            print(f"🚨 Sent Unity alert packets ({len(unity_alerts)}): {unity_alerts}")

    except Exception as e:
        print("❌ Error:", e)


def start_listener():
    print("🚀 MQTT Listener ready...")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()