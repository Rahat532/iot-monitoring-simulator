import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import DEVICE_LAST_SEEN_AGE, INGESTED_MESSAGES
from app.models.schemas import TelemetryIn
from app.services import repository
from app.services.state import MAX_CACHE, latest_cache, ws_manager

log = logging.getLogger(__name__)


async def process_telemetry(
    session: AsyncSession,
    payload: dict,
    source: str,
) -> TelemetryIn:
    telemetry = TelemetryIn.model_validate(payload)
    await repository.write_telemetry(session, telemetry, source)

    INGESTED_MESSAGES.labels(source=source, device_id=telemetry.device_id).inc()
    age_seconds = max(
        0.0,
        (datetime.now(timezone.utc) - telemetry.ts.astimezone(timezone.utc)).total_seconds(),
    )
    DEVICE_LAST_SEEN_AGE.labels(device_id=telemetry.device_id).set(age_seconds)

    normalized = {
        "device_id": telemetry.device_id,
        "ts": telemetry.ts.isoformat(),
        "temperature": telemetry.temperature,
        "humidity": telemetry.humidity,
        "vibration": telemetry.vibration,
        "alarm": telemetry.alarm,
        "severity": telemetry.severity,
        "source": source,
    }

    latest_cache.append(normalized)
    if len(latest_cache) > MAX_CACHE:
        del latest_cache[: len(latest_cache) - MAX_CACHE]

    await ws_manager.broadcast(normalized)
    log.info("ingested telemetry device=%s source=%s", telemetry.device_id, source)
    return telemetry
