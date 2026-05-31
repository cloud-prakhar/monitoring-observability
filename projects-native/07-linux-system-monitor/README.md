# Project 7 — Linux System Monitor

A Python/Flask app that exposes real-time **Linux** system metrics as a Prometheus
endpoint, using the [`psutil`](https://github.com/giampaolo/psutil) library. Runs natively
on Linux as a local Python process and is scraped by the **native** Prometheus you install
in `linux-setup/`.

---

## Project 4 vs Project 7 — two ways to read the same numbers

This project monitors the same machine as Project 4, but takes the opposite approach:

| | Project 4 (System Monitor) | Project 7 (this project) |
|---|---|---|
| **How it reads metrics** | Parses raw `/proc` files by hand | Calls `psutil` functions |
| **Lines of collector code** | ~80 (manual jiffie math, sector math) | ~30 |
| **Runs on macOS?** | No — macOS has no `/proc` | Yes — same code as Project 6 |
| **What it teaches** | How the Linux kernel exposes metrics | How a portable library hides the OS |
| **Closest real tool** | Writing your own exporter | Using an off-the-shelf client library |

Neither is "better" — run both and compare. Raw `/proc` teaches you what's really happening;
`psutil` is what you'd reach for in production when you want one code path for every OS.

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
GET /          → {"service": "linux-system-monitor", "status": "ok"}
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
| `host_info` | Gauge | os | Always 1 — carries the `os="linux"` label |

**Why all Gauges?**
Every value here is either an instantaneous reading (CPU %, memory %) or a cumulative
kernel counter (disk/network bytes). A Gauge fits both: it can go up or down, and for the
`_total` counters you apply `rate()` in PromQL to turn the running total into a per-second
throughput.

---

## Quick start

```bash
cd projects-native/07-linux-system-monitor/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Verify:
```bash
curl http://localhost:8087/snapshot
curl http://localhost:8087/metrics | grep host_cpu
```

Follow **[CONNECT.md](CONNECT.md)** to wire the running app into Prometheus and Grafana.

---

## Try these PromQL queries

```promql
# Current CPU load
host_cpu_usage_percent{job="linux-system-monitor"}

# Memory used (bytes)
host_memory_used_bytes{job="linux-system-monitor"}

# Network receive throughput per interface (bytes/second)
rate(host_net_bytes_recv_total{job="linux-system-monitor"}[1m])

# All three load averages on one graph
host_load_average{job="linux-system-monitor"}
```

---

## Files

| File | Purpose |
|------|---------|
| `app/app.py` | Flask app that reads metrics via `psutil` |
| `app/requirements.txt` | `flask`, `prometheus-client`, `psutil` |
| `CONNECT.md` | Step-by-step wiring guide (native Linux) |
| `CLEANUP.md` | Return machine to a clean state |
| `dashboards/linux-system-monitor.json` | Importable Grafana dashboard (8 panels) |

---

## Port

| Service | Port | URL |
|---------|------|-----|
| Linux System Monitor | 8087 | http://localhost:8087 |
| Snapshot | 8087 | http://localhost:8087/snapshot |
| Metrics | 8087 | http://localhost:8087/metrics |
