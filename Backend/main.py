from app.db.sensor_db import init_sensor_db
from app.db.metrics_db import init_metrics_db
from app.db.alerts_db import init_alerts_db
from app.mqtt.mqtt_listener import start_listener
from app.db.ventilation_db import init_ventilation_db

if __name__ == "__main__":
    init_sensor_db()
    init_metrics_db()
    init_alerts_db()
    init_ventilation_db()
    start_listener()
