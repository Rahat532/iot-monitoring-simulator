from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backend")

app = FastAPI(title="IIoT Monitoring Backend", version="0.1.0")

class Telemetry(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    ts: datetime
    temperature: float
    humidity: float
    vibration: float
    alarm: int = Field(..., ge=0, le=1)

# store latest N messages (MVP)
LATEST: List[Telemetry] = []
MAX_STORE = 500

class WSManager:
    def __init__(self):
        self.clients: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.append(ws)
        log.info("WS connected. total=%d", len(self.clients))

    def disconnect(self, ws: WebSocket):
        if ws in self.clients:
            self.clients.remove(ws)
        log.info("WS disconnected. total=%d", len(self.clients))

    async def broadcast(self, msg: dict):
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = WSManager()

@app.get("/health")
def health():
    return {"status": "ok", "utc": datetime.now(timezone.utc).isoformat()}

@app.get("/telemetry/latest")
def latest(limit: int = 50):
    limit = max(1, min(limit, 200))
    return [t.model_dump() for t in LATEST[-limit:]]

@app.post("/v1/telemetry")
async def ingest(t: Telemetry):
    LATEST.append(t)
    if len(LATEST) > MAX_STORE:
        del LATEST[: len(LATEST) - MAX_STORE]

    log.info(
        "ingest device=%s temp=%.2f hum=%.2f vib=%.3f alarm=%d",
        t.device_id, t.temperature, t.humidity, t.vibration, t.alarm
    )

    await ws_manager.broadcast(t.model_dump())
    return {"ok": True}

@app.websocket("/v1/stream")
async def stream(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            # keep alive, but don't require client messages
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)