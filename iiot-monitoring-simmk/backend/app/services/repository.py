from datetime import datetime, timezone

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import AlarmRecord, DeviceRecord, TelemetryRecord
from app.models.schemas import DeviceStatusIn, TelemetryIn


async def upsert_device(
    session: AsyncSession,
    *,
    device_id: str,
    ts: datetime,
    status: str,
    profile: str,
    metadata: dict,
) -> None:
    db_device = await session.get(DeviceRecord, device_id)
    if db_device is None:
        db_device = DeviceRecord(
            device_id=device_id,
            last_seen=ts,
            status=status,
            profile=profile,
            metadata_json=metadata,
        )
        session.add(db_device)
        return

    db_device.last_seen = ts
    db_device.status = status
    db_device.profile = profile
    db_device.metadata_json = metadata


async def write_status(session: AsyncSession, status: DeviceStatusIn) -> None:
    await upsert_device(
        session,
        device_id=status.device_id,
        ts=status.ts,
        status=status.status,
        profile=status.profile,
        metadata=status.metadata,
    )
    await session.commit()


async def write_telemetry(session: AsyncSession, telemetry: TelemetryIn, source: str) -> None:
    record = TelemetryRecord(
        device_id=telemetry.device_id,
        ts=telemetry.ts,
        temperature=telemetry.temperature,
        humidity=telemetry.humidity,
        vibration=telemetry.vibration,
        alarm=telemetry.alarm,
        severity=telemetry.severity,
        source=source,
        metadata_json=telemetry.metadata,
    )
    session.add(record)

    await upsert_device(
        session,
        device_id=telemetry.device_id,
        ts=telemetry.ts,
        status="online",
        profile=telemetry.metadata.get("profile", "default"),
        metadata=telemetry.metadata,
    )

    if telemetry.alarm == 1:
        session.add(
            AlarmRecord(
                device_id=telemetry.device_id,
                ts=telemetry.ts,
                severity=telemetry.severity,
                message="Threshold exceeded",
                temperature=telemetry.temperature,
                humidity=telemetry.humidity,
                vibration=telemetry.vibration,
            )
        )

    await session.commit()


async def get_latest(
    session: AsyncSession,
    *,
    device_id: str | None,
    limit: int,
) -> list[TelemetryRecord]:
    clauses = []
    if device_id:
        clauses.append(TelemetryRecord.device_id == device_id)

    stmt = select(TelemetryRecord)
    if clauses:
        stmt = stmt.where(and_(*clauses))
    stmt = stmt.order_by(desc(TelemetryRecord.ts)).limit(limit)

    rows = (await session.execute(stmt)).scalars().all()
    return list(reversed(rows))


async def get_range(
    session: AsyncSession,
    *,
    device_id: str | None,
    start: datetime,
    end: datetime,
) -> list[TelemetryRecord]:
    clauses = [TelemetryRecord.ts >= start, TelemetryRecord.ts <= end]
    if device_id:
        clauses.append(TelemetryRecord.device_id == device_id)

    stmt = (
        select(TelemetryRecord)
        .where(and_(*clauses))
        .order_by(TelemetryRecord.ts.asc())
    )
    return (await session.execute(stmt)).scalars().all()


async def get_alarms(
    session: AsyncSession,
    *,
    device_id: str | None,
    start: datetime,
    end: datetime,
    severity: str | None,
) -> list[AlarmRecord]:
    clauses = [AlarmRecord.ts >= start, AlarmRecord.ts <= end]
    if device_id:
        clauses.append(AlarmRecord.device_id == device_id)
    if severity:
        clauses.append(AlarmRecord.severity == severity)

    stmt = select(AlarmRecord).where(and_(*clauses)).order_by(desc(AlarmRecord.ts))
    return (await session.execute(stmt)).scalars().all()


async def list_devices(session: AsyncSession) -> list[DeviceRecord]:
    stmt = select(DeviceRecord).order_by(desc(DeviceRecord.last_seen))
    return (await session.execute(stmt)).scalars().all()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
