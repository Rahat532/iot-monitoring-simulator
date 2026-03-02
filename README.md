# IIoT Monitoring (Simulation + Dashboard)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white) ![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-660066?logo=eclipsemosquitto&logoColor=white)

This project simulates industrial IoT devices sending telemetry (temperature, humidity, vibration) into a backend service.
The backend exposes API + WebSocket endpoints and a Streamlit dashboard visualizes live metrics and alarm states.
It is an end-to-end local flow from simulated devices to monitoring UI, ready to extend with MQTT ingestion and persistent storage.

## Architecture (Simple)

```text
                 +---------------------------+
                 |   Docker: Mosquitto MQTT |
                 |   tcp://localhost:1883    |
                 +-------------+-------------+
                               |
                               | (planned / optional MQTT ingest)
                               v
+-------------------+      +-----------------------+      +----------------------+
| Simulator (Python)| ---> | FastAPI Backend       | ---> | Streamlit Dashboard  |
| synthetic sensors | HTTP | /v1/telemetry         | HTTP | live charts + alarms |
| every 1s          | POST | /telemetry/latest     | JSON | localhost:8501       |
+-------------------+      | /v1/stream (WebSocket)|      +----------------------+
                           +-----------------------+
                                      |
                                      v
                           In-memory time-series buffer
                           (latest 500 points, MVP)
```

## Circuit Diagram

![Arduino UNO with LED, resistor, and temperature sensor circuit diagram](image.png)

## Dashboard / Output Screenshot

![Dashboard or output screenshot](docs/Terrific%20Gogo-Blad%20(1).png)

## Protocol & Data Flow

- Current ingest path: simulator sends JSON via HTTP `POST /v1/telemetry` every second.
- Dashboard path: Streamlit polls `GET /telemetry/latest` and can consume `WS /v1/stream` for push updates.
- MQTT path: Mosquitto is already provisioned with Docker and can be wired as an additional ingest channel.
- Time-series storage: current MVP keeps recent telemetry in memory; a TSDB (e.g., InfluxDB/TimescaleDB) is the next step.
- Alerts: alarm flag is computed in simulator (`temp > 35°C` or `vibration > 0.75`) and visualized in dashboard.

## Project Structure

```text
project-1/
├── docker-compose.yml
├── image.png
├── README.md
└── iiot-monitoring-simmk/
    ├── requirements.txt
    ├── backend/app/main.py
    ├── dashboard/app.py
    ├── simulator/main.py
    └── mosquitto/mosquitto.conf
```

## Prerequisites

- Python 3.10+
- Docker Desktop

## How to Run

1) Start Mosquitto with Docker Compose

```bash
docker compose up -d
```

2) Set up Python environment and install dependencies

```bash
cd iiot-monitoring-simmk
python -m venv venv
# PowerShell
.\venv\Scripts\Activate.ps1
# Git Bash
source venv/Scripts/activate
pip install -r requirements.txt
```

3) Start backend

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

4) Start simulator (new terminal)

```bash
python simulator/main.py
```

5) Start dashboard (new terminal)

```bash
streamlit run dashboard/app.py
```

## Service URLs

- Backend health: `http://127.0.0.1:8000/health`
- Latest telemetry: `http://127.0.0.1:8000/telemetry/latest`
- Dashboard: `http://localhost:8501`

## GitHub About (copy/paste)

- Description: `IIoT monitoring simulation with Python, FastAPI, Streamlit, Docker, and MQTT-ready architecture.`
- Topics: `iot`, `iiot`, `mqtt`, `fastapi`, `streamlit`, `docker`, `monitoring`, `simulation`, `telemetry`, `dashboard`
