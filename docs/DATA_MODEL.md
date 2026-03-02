# Data Model

## telemetry

- `id` (int, PK)
- `device_id` (string, indexed)
- `ts` (timestamp with timezone, indexed)
- `temperature` (float)
- `humidity` (float)
- `vibration` (float)
- `alarm` (int: 0/1)
- `severity` (string: info/warning/critical)
- `source` (string: mqtt/rest)
- `metadata_json` (json)

## alarms

- `id` (int, PK)
- `device_id` (string, indexed)
- `ts` (timestamp with timezone, indexed)
- `severity` (string)
- `message` (text)
- `temperature`, `humidity`, `vibration` (nullable snapshots)

## devices

- `device_id` (string, PK)
- `last_seen` (timestamp with timezone)
- `status` (online/offline/etc)
- `profile` (string)
- `metadata_json` (json)
