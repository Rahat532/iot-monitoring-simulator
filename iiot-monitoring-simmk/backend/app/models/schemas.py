from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TelemetryIn(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    ts: datetime
    temperature: float
    humidity: float
    vibration: float
    alarm: int = Field(..., ge=0, le=1)
    severity: str = "info"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceStatusIn(BaseModel):
    device_id: str
    ts: datetime
    status: str = "online"
    profile: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TelemetryOut(BaseModel):
    device_id: str
    ts: datetime
    temperature: float
    humidity: float
    vibration: float
    alarm: int
    severity: str
    source: str


class AlarmOut(BaseModel):
    device_id: str
    ts: datetime
    severity: str
    message: str
    temperature: float | None = None
    humidity: float | None = None
    vibration: float | None = None


class DeviceOut(BaseModel):
    device_id: str
    last_seen: datetime
    status: str
    profile: str
