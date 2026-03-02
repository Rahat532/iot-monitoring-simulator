import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "IIoT Monitoring Backend")
    app_version: str = os.getenv("APP_VERSION", "0.2.0")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://iiot:iiot@timescaledb:5432/iiot",
    )

    mqtt_enabled: bool = os.getenv("MQTT_ENABLED", "true").lower() == "true"
    mqtt_host: str = os.getenv("MQTT_HOST", "mosquitto")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_client_id: str = os.getenv("MQTT_CLIENT_ID", "iiot-backend")
    mqtt_telemetry_topic: str = os.getenv("MQTT_TELEMETRY_TOPIC", "iiot/+/telemetry")
    mqtt_status_topic: str = os.getenv("MQTT_STATUS_TOPIC", "iiot/+/status")


settings = Settings()
