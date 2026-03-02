from datetime import datetime, timedelta, timezone


def telemetry_payload(device_id: str = "device-test-1") -> dict:
    return {
        "device_id": device_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "temperature": 36.1,
        "humidity": 51.2,
        "vibration": 0.81,
        "alarm": 1,
        "severity": "critical",
        "metadata": {"profile": "test"},
    }


def test_ingest_and_query_latest(client):
    resp = client.post("/v1/telemetry", json=telemetry_payload())
    assert resp.status_code == 200

    latest = client.get("/telemetry/latest", params={"device_id": "device-test-1", "limit": 10})
    assert latest.status_code == 200
    data = latest.json()
    assert len(data) >= 1
    assert data[-1]["device_id"] == "device-test-1"


def test_range_alarms_and_devices(client):
    now = datetime.now(timezone.utc)
    earlier = now - timedelta(minutes=5)
    client.post("/v1/telemetry", json=telemetry_payload("device-test-2"))

    r_range = client.get(
        "/telemetry/range",
        params={
            "device_id": "device-test-2",
            "from": earlier.isoformat(),
            "to": now.isoformat(),
        },
    )
    assert r_range.status_code == 200

    r_alarms = client.get(
        "/alarms",
        params={
            "device_id": "device-test-2",
            "from": earlier.isoformat(),
            "to": now.isoformat(),
            "severity": "critical",
        },
    )
    assert r_alarms.status_code == 200

    r_devices = client.get("/devices")
    assert r_devices.status_code == 200
    assert any(d["device_id"] == "device-test-2" for d in r_devices.json())


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
