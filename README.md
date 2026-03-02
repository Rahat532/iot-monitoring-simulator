# IIoT Monitoring (Simulation + Dashboard)

Simple IIoT monitoring stack with:
- FastAPI backend for telemetry ingestion and streaming
- Python simulator that sends synthetic sensor data
- Streamlit dashboard for live monitoring
- Mosquitto MQTT broker via Docker

## Circuit Diagram

Add your wiring image at `docs/arduino-wiring.png`, then it will render below:

![Arduino Wiring Diagram](docs/arduino-wiring.png)

## Project Structure

```text
project-1/
├── docker-compose.yml
└── iiot-monitoring-simmk/
    ├── backend/app/main.py
    ├── dashboard/app.py
    ├── simulator/main.py
    └── mosquitto/mosquitto.conf
```

## Prerequisites

- Python 3.10+
- Docker Desktop

## Quick Start

### 1) Start Mosquitto broker

```bash
docker compose up -d
```

### 2) Create and activate virtual environment

```bash
cd iiot-monitoring-simmk
python -m venv venv
# PowerShell
.\venv\Scripts\Activate.ps1
# Git Bash
source venv/Scripts/activate
```

### 3) Install Python dependencies

```bash
pip install fastapi uvicorn pydantic httpx streamlit pandas requests
```

### 4) Run backend

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5) Run simulator (new terminal)

```bash
python simulator/main.py
```

### 6) Run dashboard (new terminal)

```bash
streamlit run dashboard/app.py
```

## Service URLs

- Backend health: `http://127.0.0.1:8000/health`
- Latest telemetry: `http://127.0.0.1:8000/telemetry/latest`
- Dashboard: `http://localhost:8501`

## API Endpoints

- `POST /v1/telemetry` - ingest telemetry payload
- `GET /telemetry/latest?limit=200` - fetch latest samples
- `WS /v1/stream` - websocket stream

## Notes

- Current backend stores latest 500 telemetry messages in memory.
- Alarm logic in simulator turns ON when temperature > 35°C or vibration > 0.75.
