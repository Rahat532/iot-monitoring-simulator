import json
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from paho.mqtt import client as mqtt

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000/v1/telemetry")
MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "true").lower() == "true"
HTTP_FALLBACK = os.getenv("HTTP_FALLBACK", "true").lower() == "true"

DEVICE_IDS = [
    x.strip()
    for x in os.getenv("DEVICE_IDS", "device-001,device-002,device-003").split(",")
    if x.strip()
]

DEFAULT_RATE = float(os.getenv("SIM_SAMPLE_RATE", "1.0"))
FAULT_MODE = os.getenv("FAULT_MODE", "none")


@dataclass
class DeviceProfile:
    profile: str
    temp_base: float
    hum_base: float
    vib_base: float
    sample_rate: float


PROFILES: list[DeviceProfile] = [
    DeviceProfile("press", 24.0, 52.0, 0.12, DEFAULT_RATE),
    DeviceProfile("pump", 27.5, 49.0, 0.22, DEFAULT_RATE),
    DeviceProfile("motor", 30.0, 45.0, 0.30, DEFAULT_RATE),
]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def with_faults(temp: float, hum: float, vib: float, mode: str) -> tuple[float, float, float, str]:
    severity = "info"
    if mode == "dropout" and random.random() < 0.15:
        raise TimeoutError("simulated sensor dropout")
    if mode == "spike" and random.random() < 0.25:
        temp += random.uniform(8, 18)
        vib += random.uniform(0.2, 0.5)
        severity = "critical"
    if mode == "stuck":
        temp = round(temp)
        hum = round(hum)
        vib = round(vib, 1)
        severity = "warning"
    if mode == "vibration_burst" and random.random() < 0.35:
        vib += random.uniform(0.4, 0.7)
        severity = "critical"
    return temp, hum, vib, severity


def generate(device_id: str, profile: DeviceProfile) -> dict:
    temp = profile.temp_base + random.gauss(0, 0.35)
    vib = clamp(profile.vib_base + random.gauss(0, 0.03), 0, 1.5)
    hum = clamp(profile.hum_base - (temp - 25) * 0.8 + random.gauss(0, 0.8), 10, 90)
    temp, hum, vib, severity = with_faults(temp, hum, vib, FAULT_MODE)
    alarm = 1 if (temp > 35.0 or vib > 0.75) else 0

    if alarm == 1 and severity == "info":
        severity = "warning"

    return {
        "device_id": device_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "temperature": round(temp, 2),
        "humidity": round(hum, 2),
        "vibration": round(vib, 3),
        "alarm": alarm,
        "severity": severity,
        "metadata": {"profile": profile.profile},
    }


def build_status(device_id: str, profile: DeviceProfile) -> dict:
    return {
        "device_id": device_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "online",
        "profile": profile.profile,
        "metadata": {"fault_mode": FAULT_MODE},
    }


def mqtt_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iiot-simulator")
    client.reconnect_delay_set(min_delay=1, max_delay=15)
    client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()
    return client


def main() -> None:
    mqttc = mqtt_client() if MQTT_ENABLED else None
    schedule = {
        did: {"next": 0.0, "profile": PROFILES[i % len(PROFILES)]}
        for i, did in enumerate(DEVICE_IDS)
    }

    with httpx.Client(timeout=5.0) as http_client:
        while True:
            now = time.monotonic()

            for device_id, state in schedule.items():
                profile: DeviceProfile = state["profile"]
                if now < state["next"]:
                    continue

                state["next"] = now + max(0.2, profile.sample_rate)

                try:
                    payload = generate(device_id, profile)
                except TimeoutError:
                    continue

                status_payload = build_status(device_id, profile)

                if mqttc is not None:
                    mqttc.publish(f"iiot/{device_id}/telemetry", json.dumps(payload), qos=1)
                    mqttc.publish(f"iiot/{device_id}/status", json.dumps(status_payload), qos=1)

                if HTTP_FALLBACK:
                    try:
                        http_client.post(BACKEND_URL, json=payload)
                    except Exception:
                        pass

                print("sent", payload)

            time.sleep(0.1)


if __name__ == "__main__":
    main()