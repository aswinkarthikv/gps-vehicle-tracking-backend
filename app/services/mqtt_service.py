import json
import logging
import threading
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.vehicle import Vehicle
from app.models.gps_data import GPSData

logger = logging.getLogger("mqtt_service")
logging.basicConfig(level=logging.INFO)

class MQTTSubscriber:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self._thread = None

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT Broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
            # Subscribe to vehicle telemetry topics
            topic = f"{settings.MQTT_TOPIC_PREFIX}/#"
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.warning(f"Failed to connect to MQTT Broker, return code: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            logger.info(f"Received MQTT Telemetry on [{msg.topic}]: {data}")

            vehicle_id = data.get("vehicle_id")
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            speed = data.get("speed", 0.0)
            heading = data.get("heading", 0.0)
            ts_str = data.get("timestamp")

            if vehicle_id is None or latitude is None or longitude is None:
                logger.warning(f"Malformed MQTT GPS payload: {data}")
                return

            ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)

            # Persist to database
            db = SessionLocal()
            try:
                vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
                if vehicle:
                    vehicle.current_latitude = latitude
                    vehicle.current_longitude = longitude
                    vehicle.current_speed = speed
                    vehicle.current_heading = heading
                    vehicle.last_updated = ts
                    vehicle.status = "IN_TRANSIT" if speed > 2.0 else "IDLE"

                    gps_log = GPSData(
                        vehicle_id=vehicle.id,
                        latitude=latitude,
                        longitude=longitude,
                        speed=speed,
                        heading=heading,
                        timestamp=ts
                    )
                    db.add(gps_log)
                    db.commit()
                    logger.info(f"Updated Vehicle #{vehicle_id} position via MQTT: ({latitude}, {longitude})")
                else:
                    logger.warning(f"Vehicle #{vehicle_id} not found in DB")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    def start(self):
        if not settings.MQTT_ENABLED:
            logger.info("MQTT is disabled in configuration.")
            return

        try:
            # Paho MQTT v2 client setup
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=settings.MQTT_CLIENT_ID
            )
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message

            self.client.connect_async(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
            logger.info(f"MQTT background loop started for broker {settings.MQTT_BROKER_HOST}")
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")

    def stop(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Client disconnected.")

mqtt_subscriber = MQTTSubscriber()
