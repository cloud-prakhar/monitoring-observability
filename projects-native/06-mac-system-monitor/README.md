# Project 6 — Mac System Monitor

A Python/Flask app that exposes real-time **macOS** system metrics as a Prometheus
endpoint. Runs natively on macOS as a local Python process and is scraped by the
**native** Prometheus you install in `mac-setup/`.

It does the same job as Project 4 (System Monitor) but on macOS — where the trick
Project 4 relies on does not exist.

---

## Why a separate project for macOS?

Project 4 reads the Linux **`/proc`** filesystem directly (`/proc/stat`, `/proc/meminfo`, …).
**macOS has no `/proc`.** The kernel exposes the same information through the `sysctl`
and Mach APIs instead. Rather than learn a second set of low-level files, this project
uses [`psutil`](https://github.com/giampaolo/psutil) — a library that wraps every OS's
native API behind one identical Python interface.

The lesson: **a portable library lets you write one collector that runs everywhere.**
The exact same `app.py` powers Project 7 (Linux) unchanged.

```
Project 4  →  raw /proc parsing        →  Linux only
Project 6  →  psutil (this project)     →  macOS  (same code as Project 7)
Project 7  →  psutil                    →  Linux  (same code as Project 6)
```

---

## What it does

Every 5 seconds a background thread asks `psutil` for the current readings and updates
all gauges:

```
psutil.cpu_percent(percpu=True)   → overall + per-core CPU usage
psutil.virtual_memory()           → total / used / percent RAM
psutil.swap_memory()              → swap total / used
psutil.getloadavg()               → 1m / 5m / 15m load averages
psutil.disk_usage(mount)          → filesystem used % per mount
psutil.disk_io_counters()         → cumulative bytes read / written
psutil.net_io_counters(pernic)    → cumulative bytes sent / received per NIC
psutil.sensors_battery()          → battery % and AC-power status (laptops)
psutil.boot_time()                → uptime
```

Routes:
```
GET /          → {"service": "mac-system-monitor", "status": "ok"}
GET /snapshot  → current readings as human-readable JSON
GET /metrics   → Prometheus scrapes this
```

---

## Metrics produced

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `host_cpu_usage_percent` | Gauge | — | Overall CPU busy % (0–100) |
| `host_cpu_core_usage_percent` | Gauge | core | Per-core CPU busy % |
| `host_memory_total_bytes` | Gauge | — | Total installed RAM |
| `host_memory_used_bytes` | Gauge | — | RAM in use |
| `host_memory_usage_percent` | Gauge | — | RAM used as percentage |
| `host_swap_total_bytes` | Gauge | — | Total swap space |
| `host_swap_used_bytes` | Gauge | — | Swap currently in use |
| `host_load_average` | Gauge | interval | Load avg (`1m`, `5m`, `15m`) |
| `host_disk_usage_percent` | Gauge | mount | Filesystem space used % |
| `host_disk_read_bytes_total` | Gauge | — | Cumulative bytes read since boot |
| `host_disk_write_bytes_total` | Gauge | — | Cumulative bytes written since boot |
| `host_net_bytes_sent_total` | Gauge | nic | Cumulative bytes sent per interface |
| `host_net_bytes_recv_total` | Gauge | nic | Cumulative bytes received per interface |
| `host_battery_percent` | Gauge | — | Battery charge % (laptops only) |
| `host_battery_plugged` | Gauge | — | 1 on AC power, 0 on battery |
| `host_uptime_seconds` | Gauge | — | Seconds since last boot |
| `host_info` | Gauge | os | Always 1 — carries the `os="macos"` label |

**Why all Gauges?**
Every value here is either an instantaneous reading (CPU %, memory %) or a cumulative
kernel counter (disk/network bytes). A Gauge fits both: it can go up or down, and for the
`_total` counters you apply `rate()` in PromQL to turn the running total into a per-second
throughput.

---

## Quick start

```bash
cd projects-native/06-mac-system-monitor/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Verify:
```bash
curl http://localhost:8086/snapshot
curl http://localhost:8086/metrics | grep host_cpu
```

Follow **[CONNECT.md](CONNECT.md)** to wire the running app into Prometheus and Grafana.

---

## Try these PromQL queries

```promql
# Current CPU load
host_cpu_usage_percent{job="mac-system-monitor"}

# Memory used (bytes)
host_memory_used_bytes{job="mac-system-monitor"}

# Network receive throughput per interface (bytes/second)
rate(host_net_bytes_recv_total{job="mac-system-monitor"}[1m])

# All three load averages on one graph
host_load_average{job="mac-system-monitor"}
```

---

## Files

| File | Purpose |
|------|---------|
| `app/app.py` | Flask app that reads metrics via `psutil` |
| `app/requirements.txt` | `flask`, `prometheus-client`, `psutil` |
| `CONNECT.md` | Step-by-step wiring guide (native macOS) |
| `CLEANUP.md` | Return machine to a clean state |
| `dashboards/mac-system-monitor.json` | Importable Grafana dashboard (8 panels) |

---

## Port

| Service | Port | URL |
|---------|------|-----|
| Mac System Monitor | 8086 | http://localhost:8086 |
| Snapshot | 8086 | http://localhost:8086/snapshot |
| Metrics | 8086 | http://localhost:8086/metrics |
