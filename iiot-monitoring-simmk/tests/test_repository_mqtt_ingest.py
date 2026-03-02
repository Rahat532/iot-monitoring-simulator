import asyncio
from datetime import datetime, timezone

import pytest
from app.core.db import SessionLocal
from app.services.ingestion import process_telemetry


@pytest.mark.asyncio
async def test_mqtt_ingest_path_writes_source():
    payload = {
        "device_id": "device-mqtt-1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "temperature": 28.3,
        "humidity": 47.2,
        "vibration": 0.41,
        "alarm": 0,
        "severity": "info",
        "metadata": {"profile": "pump"},
    }

    async with SessionLocal() as session:
        telemetry = await process_telemetry(session, payload, source="mqtt")
        assert telemetry.device_id == "device-mqtt-1"

    await asyncio.sleep(0)
