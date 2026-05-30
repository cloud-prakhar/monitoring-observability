# Connecting System Monitor to Prometheus and Grafana

This project reads `/proc` to expose CPU, memory, load average, disk I/O, and uptime
as Prometheus metrics. It runs **natively in WSL2** as a local Python process.

> **Prerequisite:** Follow `wsl-setup/` first so Prometheus and Grafana are installed
> and running as system processes. (For the Docker track, use projects `01–03` instead —
> those run in containers against the `infra/` stack.)

---

## Step 1 — Install Python dependencies

```bash
cd projects-native/04-system-monitor/app

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 2 — Start the app

```bash
python app.py
```

Expected output:
```
System Monitor running on http://0.0.0.0:8084
Snapshot: http://0.0.0.0:8084/snapshot
Metrics:  http://0.0.0.0:8084/metrics
```

Leave this terminal open, or run it in the background:
```bash
nohup python app.py > app.log 2>&1 &
echo "App PID: $!"
```

## Step 3 — Verify the app is collecting data

```bash
curl http://localhost:8084/snapshot
```

Expected output:
```json
{
  "cpu_usage_percent": 4.2,
  "memory_total_gb": 15.87,
  "memory_available_gb": 11.23,
  "memory_usage_percent": 29.2,
  "load_average": {"1m": 0.12, "5m": 0.08, "15m": 0.05},
  "uptime_seconds": 123456
}
```

Check the raw metrics endpoint:
```bash
curl http://localhost:8084/metrics | grep system_cpu
```

You should see lines like `system_cpu_usage_percent 4.2`.

## Step 4 — Add the scrape job to Prometheus

Edit the native Prometheus config:
```bash
sudo nano /etc/prometheus/prometheus.yml
```

Add this job under `scrape_configs:` (or uncomment the Project 4 block if it is already there):
```yaml
  - job_name: "system-monitor"
    static_configs:
      - targets: ["localhost:8084"]
```

Save the file, then reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

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
system-monitor -> up
```

Or open **http://localhost:9090/targets** in the browser.

---

## Step 6 — Open the Grafana dashboard

1. Open **http://localhost:3000** → log in with `admin` / `admin`
2. Go to **Dashboards** → **New** → **Import**
3. Upload `projects-native/04-system-monitor/dashboards/system-monitor.json`
4. Select **Prometheus** as the data source → **Import**

The dashboard shows 8 panels: CPU usage, memory, load average, uptime, per-core CPU,
memory over time, load avg over time, and disk I/O rates.

---

## Metrics reference

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `system_cpu_usage_percent` | Gauge | — | Overall CPU busy % (0-100) |
| `system_cpu_core_usage_percent` | Gauge | core | Per-core CPU busy % |
| `system_memory_total_bytes` | Gauge | — | Total installed RAM |
| `system_memory_available_bytes` | Gauge | — | Free + reclaimable RAM |
| `system_memory_usage_percent` | Gauge | — | RAM used as percentage |
| `system_swap_total_bytes` | Gauge | — | Total swap space |
| `system_swap_used_bytes` | Gauge | — | Swap currently in use |
| `system_load_average` | Gauge | interval | 1m / 5m / 15m load avg |
| `system_disk_read_bytes_total` | Gauge | device | Cumulative bytes read |
| `system_disk_write_bytes_total` | Gauge | device | Cumulative bytes written |
| `system_uptime_seconds` | Gauge | — | Seconds since last boot |

**Useful PromQL queries:**

```promql
# Current CPU usage
system_cpu_usage_percent{job="system-monitor"}

# Memory used (bytes)
system_memory_total_bytes{job="system-monitor"} - system_memory_available_bytes{job="system-monitor"}

# Disk read rate (bytes/second)
rate(system_disk_read_bytes_total{job="system-monitor"}[1m])

# Load average over time (all three intervals)
system_load_average{job="system-monitor"}
```

---

## Clean up

> For a complete teardown (venv, scrape job, and dashboard too), see
> **[CLEANUP.md](CLEANUP.md)**. Quick version:

```bash
# Stop the app
kill $(pgrep -f "python app.py")

# Remove the scrape job from /etc/prometheus/prometheus.yml, then reload:
curl -X POST http://localhost:9090/-/reload
```
