# Monitoring Guide

## Metrics (Backend `/metrics`)

- `iiot_request_latency_seconds` : HTTP request latency histogram
- `iiot_request_errors_total` : HTTP errors by path/status
- `iiot_ingested_messages_total` : telemetry messages by source/device
- `iiot_websocket_connected_clients` : active WebSocket clients
- `iiot_mqtt_reconnects_total` : MQTT reconnect count
- `iiot_device_last_seen_age_seconds` : staleness per device

## Logs

Backend logs are JSON formatted and include `request_id` for request correlation.

Example query idea in log aggregator:
- filter by `request_id`
- filter by `device_id` in message

## Dashboards

Grafana starter dashboard is provisioned from:
- `monitoring/grafana/dashboards/iiot-overview.json`

Includes panels for ingest rate, request errors, websocket clients, reconnects, and latency.
