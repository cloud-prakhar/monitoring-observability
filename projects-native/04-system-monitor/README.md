# Project 4 — System Monitor

A Python/Flask app that reads the Linux `/proc` filesystem and exposes real-time system
metrics as Prometheus endpoints. Runs natively in WSL2 without Docker, or in a container
using Docker.

This project teaches you how real monitoring agents work — they read kernel-exposed files
and translate them into metrics. Node Exporter (the standard Prometheus system metrics
agent) does the same thing at production scale.

---

## What it does

Every 5 seconds a background thread reads four `/proc` files and updates all gauges:

```
/proc/stat      → CPU usage per core (user/system/idle/iowait jiffies)
/proc/meminfo   → total RAM, available RAM, swap usage
/proc/loadavg   → 1-minute, 5-minute, 15-minute load averages
/proc/diskstats → cumulative sectors read/written per block device
/proc/uptime    → seconds since last boot
```

Routes:
```
GET /          → {"service": "system-monitor", "status": "ok"}
GET /snapshot  → current readings as human-readable JSON
GET /metrics   → Prometheus scrapes this
```

---

## Metrics produced

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `system_cpu_usage_percent` | Gauge | — | Overall CPU busy % (0–100) |
| `system_cpu_core_usage_percent` | Gauge | core | Per-core CPU busy % |
| `system_memory_total_bytes` | Gauge | — | Total installed RAM |
| `system_memory_available_bytes` | Gauge | — | Free + reclaimable RAM |
| `system_memory_usage_percent` | Gauge | — | RAM used as percentage |
| `system_swap_total_bytes` | Gauge | — | Total swap space |
| `system_swap_used_bytes` | Gauge | — | Swap currently in use |
| `system_load_average` | Gauge | interval | Load avg (`1m`, `5m`, `15m`) |
| `system_disk_read_bytes_total` | Gauge | device | Cumulative bytes read since boot |
| `system_disk_write_bytes_total` | Gauge | device | Cumulative bytes written since boot |
| `system_uptime_seconds` | Gauge | — | Seconds since last boot |

**Why all Gauges?**
All of these are instantaneous readings or cumulative totals from the kernel — not events
you count. A Gauge is the right type when the value can go up or down (CPU %, memory %)
or when you're reporting a raw kernel counter (disk bytes — you use `rate()` in PromQL
to convert it to a per-second throughput).

---

## Quick start

### Native WSL2 path

```bash
cd projects-native/04-system-monitor/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Verify:
```bash
curl http://localhost:8084/snapshot
curl http://localhost:8084/metrics | grep system_cpu
```

### Docker path

```bash
# Requires infra to be running first:
cd infra && docker compose up -d && cd ..

cd projects-native/04-system-monitor
docker compose up -d --build
```

Follow **[CONNECT.md](CONNECT.md)** to wire the running app into Prometheus and Grafana.

---

## Try these PromQL queries

Once Prometheus is scraping this app:

```promql
# Current CPU load
system_cpu_usage_percent{job="system-monitor"}

# Memory used (bytes)
system_memory_total_bytes - system_memory_available_bytes

# Disk read throughput (bytes/second)
rate(system_disk_read_bytes_total{job="system-monitor"}[1m])

# All three load averages on one graph
system_load_average{job="system-monitor"}
```

---

## Files

| File | Purpose |
|------|---------|
| `app/app.py` | Flask app that reads `/proc` and exposes metrics |
| `app/requirements.txt` | `flask`, `prometheus-client` |
| `app/Dockerfile` | Container image for the Docker path |
| `docker-compose.yml` | Docker path: bind-mounts host `/proc`, joins `monitoring` network |
| `CONNECT.md` | Step-by-step wiring guide — Path A (native) and Path B (Docker) |
| `dashboards/system-monitor.json` | Importable Grafana dashboard (8 panels) |

---

## Port

| Service | Port | URL |
|---------|------|-----|
| System Monitor | 8084 | http://localhost:8084 |
| Snapshot | 8084 | http://localhost:8084/snapshot |
| Metrics | 8084 | http://localhost:8084/metrics |
