import time
import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import streamlit as st

BACKEND_BASE = os.getenv("BACKEND_BASE", "http://backend:8000")

st.set_page_config(page_title="IIoT Live Dashboard", layout="wide")
st.title("IIoT Monitoring Dashboard")

st.sidebar.header("Controls")
mode = st.sidebar.radio("Mode", ["live", "history"], horizontal=True)
refresh_s = st.sidebar.slider("Refresh (seconds)", 1, 10, 2)
minutes = st.sidebar.slider("History window (minutes)", 5, 240, 30)
severity = st.sidebar.selectbox("Alarm severity", ["all", "info", "warning", "critical"])


def fetch_devices() -> list[str]:
    try:
        data = requests.get(f"{BACKEND_BASE}/devices", timeout=3).json()
    except Exception:
        return []
    return [row["device_id"] for row in data]


device_options = fetch_devices()
selected_device = st.sidebar.selectbox("Device", ["all"] + device_options)
device_param = None if selected_device == "all" else selected_device


def fetch_live() -> pd.DataFrame:
    params = {"limit": 500}
    if device_param:
        params["device_id"] = device_param
    rows = requests.get(f"{BACKEND_BASE}/telemetry/latest", params=params, timeout=4).json()
    return pd.DataFrame(rows)


def fetch_history() -> pd.DataFrame:
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)
    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
    }
    if device_param:
        params["device_id"] = device_param
    rows = requests.get(f"{BACKEND_BASE}/telemetry/range", params=params, timeout=5).json()
    return pd.DataFrame(rows)


def fetch_alarms() -> pd.DataFrame:
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)
    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
    }
    if device_param:
        params["device_id"] = device_param
    if severity != "all":
        params["severity"] = severity
    rows = requests.get(f"{BACKEND_BASE}/alarms", params=params, timeout=5).json()
    return pd.DataFrame(rows)


placeholder = st.empty()

while True:
    try:
        telemetry_df = fetch_live() if mode == "live" else fetch_history()
        alarms_df = fetch_alarms()

        with placeholder.container():
            if telemetry_df.empty:
                st.warning("No telemetry yet. Start docker compose stack and simulator.")
            else:
                telemetry_df["ts"] = pd.to_datetime(telemetry_df["ts"])
                telemetry_df = telemetry_df.sort_values("ts")

                last = telemetry_df.iloc[-1]
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Device", last["device_id"])
                c2.metric("Temperature (°C)", f"{last['temperature']:.2f}")
                c3.metric("Humidity (%)", f"{last['humidity']:.2f}")
                c4.metric("Vibration", f"{last['vibration']:.3f}")
                c5.metric("Alarm", "ON 🔴" if int(last["alarm"]) == 1 else "OFF 🟢")

                st.subheader(f"Telemetry ({mode} mode)")
                st.line_chart(
                    telemetry_df.set_index("ts")[["temperature", "humidity", "vibration"]]
                )

                st.subheader("Alarms")
                if alarms_df.empty:
                    st.info("No alarms in selected window.")
                else:
                    alarms_df["ts"] = pd.to_datetime(alarms_df["ts"])
                    st.dataframe(
                        alarms_df[
                            [
                                "ts",
                                "device_id",
                                "severity",
                                "message",
                                "temperature",
                                "humidity",
                                "vibration",
                            ]
                        ],
                        use_container_width=True,
                    )
    except Exception as exc:
        with placeholder.container():
            st.error(f"Backend not reachable: {exc}")
            st.info("Check backend service health and database connectivity.")

    time.sleep(refresh_s)
    st.rerun()