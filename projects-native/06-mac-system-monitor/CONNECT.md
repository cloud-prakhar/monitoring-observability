# Connecting Mac System Monitor to Prometheus and Grafana

This project exposes macOS CPU, memory, load, disk, network, and battery metrics via
[`psutil`](https://github.com/giampaolo/psutil). It runs **natively on macOS** as a local
Python process.

> **Prerequisite:** Follow `mac-setup/` first so Prometheus and Grafana are installed and
> running natively on macOS (via Homebrew). For Linux use Project 7; for WSL2 use Projects 4–5.

---

## Step 1 — Install Python dependencies

macOS ships with a system Python, but use a virtual environment so this project's packages
never touch it:

```bash
cd projects-native/06-mac-system-monitor/app

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> If `python3` is missing, install it with `brew install python` first.

## Step 2 — Start the app

```bash
python app.py
```

Expected output:
```
Mac System Monitor running on http://0.0.0.0:8086
Snapshot: http://0.0.0.0:8086/snapshot
Metrics:  http://0.0.0.0:8086/metrics
```

Leave this terminal open, or run it in the background:
```bash
nohup python app.py > app.log 2>&1 &
echo "App PID: $!"
```

## Step 3 — Verify the app is collecting data

```bash
curl http://localhost:8086/snapshot
```

Expected output:
```json
{
  "os": "macos",
  "cpu_usage_percent": 6.4,
  "memory_total_gb": 17.18,
  "memory_used_gb": 9.85,
  "memory_usage_percent": 57.3,
  "load_average": {"1m": 1.82, "5m": 2.04, "15m": 1.95},
  "battery_percent": 88.0,
  "uptime_seconds": 123456
}
```

> `battery_percent` is `null` on a Mac mini / Mac Studio / VM with no battery — that's expected.

Check the raw metrics endpoint:
```bash
curl http://localhost:8086/metrics | grep host_cpu
```

You should see lines like `host_cpu_usage_percent 6.4`.

## Step 4 — Add the scrape job to Prometheus

Edit the native macOS Prometheus config (the path comes from Homebrew — see `mac-setup/`):

```bash
PROM_ETC="$(brew --prefix)/etc"
nano "$PROM_ETC/prometheus.yml"
```

Add this job under `scrape_configs:` (or uncomment the Project 6 block if it is already there):
```yaml
  - job_name: "mac-system-monitor"
    static_configs:
      - targets: ["localhost:8086"]
```

Save the file, then reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

> The reload endpoint only works if Prometheus was started with `--web.enable-lifecycle`
> (see `mac-setup/01-install-prometheus.md`). If you started it with `brew services` and
> reload returns `404`, run `brew services restart prometheus` instead.

## Step 5 — Verify the target is UP

```bash
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import sys, json
d = json.load(sys.stdin)
for t in d['data']['activeTargets']:
    print(t['labels']['job'], '->', t['health'])
"
```

Expected output includes:
```
mac-system-monitor -> up
```

Or open **http://localhost:9090/targets** in the browser.

---

## Step 6 — Open the Grafana dashboard

1. Open **http://localhost:3000** → log in with `admin` / `admin`
2. Go to **Dashboards** → **New** → **Import**
3. Upload `projects-native/06-mac-system-monitor/dashboards/mac-system-monitor.json`
4. Select **Prometheus** as the data source → **Import**

The dashboard shows 8 panels: CPU usage, memory usage, load average, battery, CPU over time,
memory over time, network throughput, and disk I/O rates.

---

## Metrics reference

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `host_cpu_usage_percent` | Gauge | — | Overall CPU busy % (0–100) |
| `host_cpu_core_usage_percent` | Gauge | core | Per-core CPU busy % |
| `host_memory_total_bytes` | Gauge | — | Total installed RAM |
| `host_memory_used_bytes` | Gauge | — | RAM in use |
| `host_memory_usage_percent` | Gauge | — | RAM used as percentage |
| `host_swap_total_bytes` | Gauge | — | Total swap space |
| `host_swap_used_bytes` | Gauge | — | Swap currently in use |
| `host_load_average` | Gauge | interval | 1m / 5m / 15m load avg |
| `host_disk_usage_percent` | Gauge | mount | Filesystem space used % |
| `host_disk_read_bytes_total` | Gauge | — | Cumulative bytes read |
| `host_disk_write_bytes_total` | Gauge | — | Cumulative bytes written |
| `host_net_bytes_sent_total` | Gauge | nic | Cumulative bytes sent |
| `host_net_bytes_recv_total` | Gauge | nic | Cumulative bytes received |
| `host_battery_percent` | Gauge | — | Battery charge % (laptops) |
| `host_battery_plugged` | Gauge | — | 1 on AC, 0 on battery |
| `host_uptime_seconds` | Gauge | — | Seconds since last boot |

**Useful PromQL queries:**

```promql
# Current CPU usage
host_cpu_usage_percent{job="mac-system-monitor"}

# Memory used as a percentage
host_memory_usage_percent{job="mac-system-monitor"}

# Network receive rate per interface (bytes/second)
rate(host_net_bytes_recv_total{job="mac-system-monitor"}[1m])

# Disk write rate (bytes/second)
rate(host_disk_write_bytes_total{job="mac-system-monitor"}[1m])
```

---

## Clean up

> For a complete teardown (venv, scrape job, and dashboard too), see
> **[CLEANUP.md](CLEANUP.md)**. Quick version:

```bash
# Stop the app
kill $(pgrep -f "python app.py")

# Remove the scrape job from $(brew --prefix)/etc/prometheus.yml, then reload:
curl -X POST http://localhost:9090/-/reload
```
