# Connecting Linux System Monitor to Prometheus and Grafana

This project exposes Linux CPU, memory, load, disk, network, and battery metrics via
[`psutil`](https://github.com/giampaolo/psutil). It runs **natively on Linux** as a local
Python process.

> **Prerequisite:** Follow `linux-setup/` first so Prometheus and Grafana are installed and
> running natively on Linux (binary + systemd). On WSL2 the `wsl-setup/` path works too —
> the config file is at `/etc/prometheus/prometheus.yml` in both cases.

---

## Step 1 — Install Python dependencies

```bash
cd projects-native/07-linux-system-monitor/app

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> If `python3 -m venv` fails, install the venv package: `sudo apt-get install -y python3-venv`
> (Debian/Ubuntu) or `sudo dnf install -y python3` (Fedora/RHEL).

## Step 2 — Start the app

```bash
python app.py
```

Expected output:
```
Linux System Monitor running on http://0.0.0.0:8087
Snapshot: http://0.0.0.0:8087/snapshot
Metrics:  http://0.0.0.0:8087/metrics
```

Leave this terminal open, or run it in the background:
```bash
nohup python app.py > app.log 2>&1 &
echo "App PID: $!"
```

## Step 3 — Verify the app is collecting data

```bash
curl http://localhost:8087/snapshot
```

Expected output:
```json
{
  "os": "linux",
  "cpu_usage_percent": 3.1,
  "memory_total_gb": 15.87,
  "memory_used_gb": 4.62,
  "memory_usage_percent": 29.1,
  "load_average": {"1m": 0.12, "5m": 0.08, "15m": 0.05},
  "battery_percent": null,
  "uptime_seconds": 123456
}
```

> `battery_percent` is `null` on a desktop, server, or VM with no battery — that's expected.

Check the raw metrics endpoint:
```bash
curl http://localhost:8087/metrics | grep host_cpu
```

You should see lines like `host_cpu_usage_percent 3.1`.

## Step 4 — Add the scrape job to Prometheus

Edit the native Prometheus config (path comes from `linux-setup/`):
```bash
sudo nano /etc/prometheus/prometheus.yml
```

Add this job under `scrape_configs:` (or uncomment the Project 7 block if it is already there):
```yaml
  - job_name: "linux-system-monitor"
    static_configs:
      - targets: ["localhost:8087"]
```

Save the file, then reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

> The reload endpoint only works if Prometheus was started with `--web.enable-lifecycle`
> (the `linux-setup/` systemd unit includes it). If reload returns `403`/`404`, add the flag
> or run `sudo systemctl restart prometheus`.

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
linux-system-monitor -> up
```

Or open **http://localhost:9090/targets** in the browser.

---

## Step 6 — Open the Grafana dashboard

1. Open **http://localhost:3000** → log in with `admin` / `admin`
2. Go to **Dashboards** → **New** → **Import**
3. Upload `projects-native/07-linux-system-monitor/dashboards/linux-system-monitor.json`
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
host_cpu_usage_percent{job="linux-system-monitor"}

# Memory used as a percentage
host_memory_usage_percent{job="linux-system-monitor"}

# Network receive rate per interface (bytes/second)
rate(host_net_bytes_recv_total{job="linux-system-monitor"}[1m])

# Disk write rate (bytes/second)
rate(host_disk_write_bytes_total{job="linux-system-monitor"}[1m])
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
