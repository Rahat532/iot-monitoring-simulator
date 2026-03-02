import time
import random
from datetime import datetime, timezone
import httpx

BACKEND_URL = "http://localhost:8000/v1/telemetry"
DEVICE_ID = "device-001"

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def generate():
    # baseline
    temp = 24 + random.gauss(0, 0.3)
    vib = clamp(0.10 + random.gauss(0, 0.03), 0, 1)

    # simple humidity relation
    hum = clamp(55 - (temp - 25) * 0.8 + random.gauss(0, 0.8), 20, 90)

    alarm = 1 if (temp > 35.0 or vib > 0.75) else 0

    return {
        "device_id": DEVICE_ID,
        "ts": datetime.now(timezone.utc).isoformat(),
        "temperature": round(temp, 2),
        "humidity": round(hum, 2),
        "vibration": round(vib, 3),
        "alarm": alarm,
    }

def main():
    with httpx.Client(timeout=5.0) as client:
        while True:
            payload = generate()
            r = client.post(BACKEND_URL, json=payload)
            print("sent", payload, "status", r.status_code)
            time.sleep(1)

if __name__ == "__main__":
    main()