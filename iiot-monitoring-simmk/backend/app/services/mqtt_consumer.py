import asyncio
import json
import logging
from datetime import timezone

from paho.mqtt import client as mqtt

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.metrics import MQTT_RECONNECTS
from app.models.schemas import DeviceStatusIn
from app.services import repository
from app.services.ingestion import process_telemetry

log = logging.getLogger(__name__)


class MQTTConsumer:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.mqtt_client_id,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

    def start(self) -> None:
        self.client.connect_async(settings.mqtt_host, settings.mqtt_port, keepalive=30)
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        log.info("MQTT connected reason=%s", reason_code)
        client.subscribe(settings.mqtt_telemetry_topic)
        client.subscribe(settings.mqtt_status_topic)

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            MQTT_RECONNECTS.inc()
            log.warning("MQTT disconnected unexpectedly reason=%s", reason_code)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as exc:
            log.error("Invalid MQTT payload topic=%s err=%s", topic, exc)
            return

        future = asyncio.run_coroutine_threadsafe(
            self._dispatch(topic, payload),
            self.loop,
        )
        try:
            future.result(timeout=10)
        except Exception as exc:
            log.error("MQTT dispatch failed topic=%s err=%s", topic, exc)

    async def _dispatch(self, topic: str, payload: dict) -> None:
        async with SessionLocal() as session:
            if topic.endswith("/telemetry"):
                await process_telemetry(session, payload, source="mqtt")
                return

            if topic.endswith("/status"):
                status = DeviceStatusIn.model_validate(payload)
                if status.ts.tzinfo is None:
                    status.ts = status.ts.replace(tzinfo=timezone.utc)
                await repository.write_status(session, status)
                log.info(
                    "device status updated device=%s status=%s",
                    status.device_id,
                    status.status,
                )


mqtt_consumer: MQTTConsumer | None = None
