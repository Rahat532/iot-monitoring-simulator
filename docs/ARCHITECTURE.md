# Architecture

```text
+----------------------+         MQTT topics          +-----------------------+
| Simulator (multi-dev)|  iiot/<device>/telemetry    | Mosquitto Broker      |
| fault injection      |----------------------------->| :1883                 |
| HTTP fallback        |---- REST /v1/telemetry ---->|                       |
+----------+-----------+                              +-----------+-----------+
           |                                                          |
           |                                                          | subscribe
           v                                                          v
+----------------------+                                     +----------------------+
| FastAPI Backend      |<------------------------------------| MQTT Consumer        |
| REST + WebSocket     |                                     +----------------------+
| Validation + Normalize|             persist/query
| Metrics /health       |<--------------------------------->+----------------------+
+----------+-----------+                                     | TimescaleDB          |
           |                                                 | telemetry/alarms/dev |
           | REST                                            +----------------------+
           v
+----------------------+
| Streamlit Dashboard  |
| live mode + history  |
+----------------------+

Prometheus scrapes /metrics from backend; Grafana visualizes platform KPIs.
```
