# Runbook

## Start

1. Copy `.env.example` to `.env` and adjust credentials if needed.
2. Run:
   ```bash
   docker compose up --build -d
   ```
3. Verify health:
   - Backend: `http://localhost:8000/health`
   - Dashboard: `http://localhost:8501`
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000`

## Local Start (No Docker)

Run backend, simulator, and dashboard in separate PowerShell terminals.

Backend:

```powershell
cd D:\ICT\project-1\iiot-monitoring-simmk\backend
$env:DATABASE_URL = "sqlite+aiosqlite:///../iiot_local.db"
$env:MQTT_ENABLED = "false"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Simulator:

```powershell
cd D:\ICT\project-1\iiot-monitoring-simmk
$env:BACKEND_URL = "http://127.0.0.1:8000/v1/telemetry"
$env:MQTT_ENABLED = "false"
$env:HTTP_FALLBACK = "true"
python .\simulator\main.py
```

Dashboard:

```powershell
cd D:\ICT\project-1\iiot-monitoring-simmk\dashboard
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Important: do not paste Markdown link syntax in terminals (for example `[app.py](...)`).

## Stop

```bash
docker compose down
```

To remove DB data too:

```bash
docker compose down -v
```

## Troubleshooting

- Backend unhealthy:
  - Check DB readiness and `DATABASE_URL`.
  - Inspect logs: `docker compose logs backend --tail=200`.
- No telemetry:
  - Check simulator logs and `MQTT_ENABLED` + broker health.
  - Verify fallback path: `POST /v1/telemetry`.
- Dashboard empty:
  - Validate backend endpoints `/telemetry/latest`, `/devices`, `/alarms`.
- Grafana empty:
  - Ensure Prometheus target `backend:8000` is UP in `/targets`.
