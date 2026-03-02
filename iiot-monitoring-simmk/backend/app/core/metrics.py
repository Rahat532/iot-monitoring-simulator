from fastapi import Response

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
except ModuleNotFoundError:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _MetricNoop:
        def labels(self, **kwargs):
            return self

        def inc(self, value: float = 1.0):
            return None

        def set(self, value: float):
            return None

        def observe(self, value: float):
            return None

    def Counter(*args, **kwargs):
        return _MetricNoop()

    def Gauge(*args, **kwargs):
        return _MetricNoop()

    def Histogram(*args, **kwargs):
        return _MetricNoop()

    def generate_latest() -> bytes:
        return b""

REQUEST_LATENCY = Histogram(
    "iiot_request_latency_seconds",
    "Request latency in seconds",
    ["method", "path", "status"],
)
REQUEST_ERRORS = Counter(
    "iiot_request_errors_total",
    "Total HTTP request errors",
    ["method", "path", "status"],
)
INGESTED_MESSAGES = Counter(
    "iiot_ingested_messages_total",
    "Total ingested telemetry messages",
    ["source", "device_id"],
)
WS_CONNECTED_CLIENTS = Gauge(
    "iiot_websocket_connected_clients",
    "Current connected WebSocket clients",
)
MQTT_RECONNECTS = Counter(
    "iiot_mqtt_reconnects_total",
    "MQTT reconnects",
)
DEVICE_LAST_SEEN_AGE = Gauge(
    "iiot_device_last_seen_age_seconds",
    "Seconds since device last seen",
    ["device_id"],
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
