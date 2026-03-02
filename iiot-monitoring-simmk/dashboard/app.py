import time
import pandas as pd
import streamlit as st
import requests

BACKEND_LATEST = "http://127.0.0.1:8000/telemetry/latest"

st.set_page_config(page_title="IIoT Live Dashboard", layout="wide")
st.title("IIoT Monitoring Dashboard (Simulated)")

st.sidebar.header("Controls")
limit = st.sidebar.slider("Samples to fetch", 50, 500, 200)
refresh_s = st.sidebar.slider("Refresh (seconds)", 1, 5, 1)

placeholder = st.empty()

while True:
    try:
        data = requests.get(BACKEND_LATEST, params={"limit": limit}, timeout=3).json()
        df = pd.DataFrame(data)

        with placeholder.container():
            if df.empty:
                st.warning("No data yet. Start the simulator.")
            else:
                df["ts"] = pd.to_datetime(df["ts"])
                df = df.sort_values("ts")

                last = df.iloc[-1]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Device", last["device_id"])
                c2.metric("Temperature (°C)", f'{last["temperature"]:.2f}')
                c3.metric("Humidity (%)", f'{last["humidity"]:.2f}')
                c4.metric("Alarm", "ON 🔴" if int(last["alarm"]) == 1 else "OFF 🟢")

                st.subheader("Live Signals")
                st.line_chart(df.set_index("ts")[["temperature", "humidity", "vibration"]])

                st.subheader("Recent Alarms")
                alarms = df[df["alarm"] == 1].tail(20)
                if alarms.empty:
                    st.info("No alarms yet. We’ll add anomaly injection next.")
                else:
                    st.dataframe(
                        alarms[["ts", "device_id", "temperature", "humidity", "vibration", "alarm"]],
                        use_container_width=True
                    )

    except Exception as e:
        with placeholder.container():
            st.error(f"Backend not reachable: {e}")
            st.info("Make sure FastAPI is running on http://127.0.0.1:8000 and simulator is sending data.")

    time.sleep(refresh_s)
    st.rerun()