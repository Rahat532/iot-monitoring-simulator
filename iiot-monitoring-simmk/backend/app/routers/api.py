from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.schemas import DeviceOut, TelemetryIn
from app.services import repository
from app.services.ingestion import process_telemetry
from app.services.state import latest_cache

router = APIRouter()


@router.post("/v1/telemetry")
async def ingest_telemetry(
    payload: TelemetryIn,
    session: AsyncSession = Depends(get_session),
):
    telemetry = await process_telemetry(session, payload.model_dump(), source="rest")
    return {"ok": True, "device_id": telemetry.device_id}


@router.get("/telemetry/latest")
async def telemetry_latest(
    device_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    rows = await repository.get_latest(session, device_id=device_id, limit=limit)
    if rows:
        return [
            {
                "device_id": row.device_id,
                "ts": row.ts,
                "temperature": row.temperature,
                "humidity": row.humidity,
                "vibration": row.vibration,
                "alarm": row.alarm,
                "severity": row.severity,
                "source": row.source,
            }
            for row in rows
        ]

    # fallback for startup before DB data exists
    data = latest_cache[-limit:]
    if device_id:
        data = [row for row in data if row["device_id"] == device_id]
    return data


@router.get("/telemetry/range")
async def telemetry_range(
    device_id: str | None = None,
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    session: AsyncSession = Depends(get_session),
):
    end = to_ts or datetime.now(timezone.utc)
    start = from_ts or (end - timedelta(minutes=60))
    rows = await repository.get_range(session, device_id=device_id, start=start, end=end)
    return [
        {
            "device_id": row.device_id,
            "ts": row.ts,
            "temperature": row.temperature,
            "humidity": row.humidity,
            "vibration": row.vibration,
            "alarm": row.alarm,
            "severity": row.severity,
            "source": row.source,
        }
        for row in rows
    ]


@router.get("/alarms")
async def alarms(
    device_id: str | None = None,
    severity: str | None = None,
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    session: AsyncSession = Depends(get_session),
):
    end = to_ts or datetime.now(timezone.utc)
    start = from_ts or (end - timedelta(minutes=60))
    rows = await repository.get_alarms(
        session,
        device_id=device_id,
        start=start,
        end=end,
        severity=severity,
    )
    return [
        {
            "device_id": row.device_id,
            "ts": row.ts,
            "severity": row.severity,
            "message": row.message,
            "temperature": row.temperature,
            "humidity": row.humidity,
            "vibration": row.vibration,
        }
        for row in rows
    ]


@router.get("/devices", response_model=list[DeviceOut])
async def devices(session: AsyncSession = Depends(get_session)):
    rows = await repository.list_devices(session)
    return [
        DeviceOut(
            device_id=row.device_id,
            last_seen=row.last_seen,
            status=row.status,
            profile=row.profile,
        )
        for row in rows
    ]
