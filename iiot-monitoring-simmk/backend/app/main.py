import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.logging_config import configure_logging
from app.core.metrics import REQUEST_ERRORS, REQUEST_LATENCY, metrics_response
from app.core.request_context import request_id_var
from app.routers.api import router as api_router
from app.services.mqtt_consumer import MQTTConsumer
from app.services.state import ws_manager

configure_logging(settings.log_level)
log = logging.getLogger(__name__)

mqtt_consumer: MQTTConsumer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_consumer
    await init_db()

    if settings.mqtt_enabled:
        mqtt_consumer = MQTTConsumer(asyncio.get_running_loop())
        mqtt_consumer.start()
        log.info("MQTT consumer started")

    yield

    if mqtt_consumer is not None:
        mqtt_consumer.stop()
        log.info("MQTT consumer stopped")


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(api_router)


@app.middleware("http")
async def add_request_context_and_metrics(request: Request, call_next):
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    request_id_var.set(rid)

    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        REQUEST_ERRORS.labels(
            method=request.method,
            path=request.url.path,
            status="500",
        ).inc()
        raise
    finally:
        request_id_var.set("-")

    elapsed = time.perf_counter() - started
    status = str(response.status_code)
    REQUEST_LATENCY.labels(
        method=request.method,
        path=request.url.path,
        status=status,
    ).observe(elapsed)
    if response.status_code >= 400:
        REQUEST_ERRORS.labels(
            method=request.method,
            path=request.url.path,
            status=status,
        ).inc()

    response.headers["x-request-id"] = rid
    return response


@app.get("/health")
async def health() -> JSONResponse:
    db_ok = True
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    mqtt_ok = mqtt_consumer is not None if settings.mqtt_enabled else True
    overall = "ok" if db_ok and mqtt_ok else "degraded"
    return JSONResponse(
        {
            "status": overall,
            "db": "ok" if db_ok else "error",
            "mqtt": "ok" if mqtt_ok else "error",
            "utc": datetime.now(timezone.utc).isoformat(),
        },
        status_code=200 if overall == "ok" else 503,
    )


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.websocket("/v1/stream")
async def stream(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)