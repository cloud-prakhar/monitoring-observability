# Connecting URL Health Checker to Prometheus and Grafana

This project polls a list of URLs every 30 seconds and records availability and response time as Prometheus metrics. It works like a lightweight Blackbox Exporter.

By default it monitors: Prometheus, Grafana, and Projects 1–4 on their standard ports. You can add any URL at runtime without restarting.

Choose the path that matches your setup.

---

## Path A — Native WSL2 (no Docker)

Use this path if you followed `wsl-setup/` and have Prometheus + Grafana installed as system processes.

### A1 — Install Python dependencies

```bash
cd projects-native/05-url-health-checker/app

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### A2 — Start the app

```bash
python app.py
```

Expected output:
```
URL Health Checker running on http://0.0.0.0:8085
Monitoring 6 default URLs
Status:  http://0.0.0.0:8085/status
Metrics: http://0.0.0.0:8085/metrics
```

Run in background:
```bash
nohup python app.py > app.log 2>&1 &
echo "App PID: $!"
```

### A3 — Verify checks are running

Wait 30 seconds for the first poll cycle, then:
```bash
curl -s http://localhost:8085/status | python3 -m json.tool
```

Expected output:
```json
{
  "total": 6,
  "up": 2,
  "down": 4,
  "details": {
    "http://localhost:9090/-/healthy": {"up": 1, "status_code": 200, "response_ms": 8},
    "http://localhost:3000/api/health": {"up": 1, "status_code": 200, "response_ms": 12},
    "http://localhost:8081/": {"up": 0, "status_code": 0, "error": "Connection refused"},
    ...
  }
}
```

URLs for projects that are not running will show `"up": 0` — that is expected. Start those projects to make them go green.

### A4 — Add the scrape job to Prometheus

```bash
sudo nano /etc/prometheus/prometheus.yml
```

Uncomment the Project 5 block:
```yaml
# Before:
  # - job_name: "url-health-checker"
  #   static_configs:
  #     - targets: ["localhost:8085"]

# After:
  - job_name: "url-health-checker"
    static_configs:
      - targets: ["localhost:8085"]
```

Reload:
```bash
curl -X POST http://localhost:9090/-/reload
```

### A5 — Verify the target is UP

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
url-health-checker -> up
```

---

## Path B — Docker (connect to shared infra)

> **Important:** The URL Health Checker monitors `localhost:8081-8085`. When running in Docker, `localhost` inside the container is the container itself, not the host machine. The `docker-compose.yml` for this project uses `network_mode: host` to work around this — the container shares the host network stack and `localhost` resolves correctly.

### B1 — Ensure infra is running

```bash
cd infra && docker compose up -d
```

### B2 — Start the container

```bash
cd projects-native/05-url-health-checker
docker compose up -d --build
```

Because `network_mode: host` is set, the container is not joined to the `monitoring` Docker network. Prometheus scrapes it via `localhost:8085` instead of a container name.

Verify:
```bash
curl http://localhost:8085/status
```

### B3 — Add the scrape job to infra Prometheus

Edit `infra/prometheus.yml` and add:
```yaml
  - job_name: "url-health-checker"
    static_configs:
      - targets: ["localhost:8085"]
```

Note: use `localhost`, not `url-health-checker`, because the container uses host networking.

Reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

---

## Add or remove monitored URLs at runtime

You can change the target list without restarting the app.

**Add a URL:**
```bash
curl -X POST http://localhost:8085/targets \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Remove a URL:**
```bash
curl -X DELETE http://localhost:8085/targets \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**List current targets:**
```bash
curl http://localhost:8085/targets
```

---

## Open the Grafana dashboard

1. Open **http://localhost:3000** → log in with `admin` / `admin`
2. Go to **Dashboards** → **New** → **Import**
3. Upload `projects-native/05-url-health-checker/dashboards/url-health-checker.json`
4. Select **Prometheus** as the data source → **Import**

The dashboard shows: total URLs monitored, count up/down, median response time, check error rate, per-URL up/down timeline, per-URL response times, HTTP status codes, and check errors.

---

## Metrics reference

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `url_up` | Gauge | url | 1 if last check was 2xx/3xx, 0 if failed |
| `url_status_code` | Gauge | url | Last HTTP status code (0 = connection error) |
| `url_response_seconds` | Histogram | url | Response time per URL |
| `url_checks_total` | Counter | url, result | Total checks (result = success / error) |

**Useful PromQL queries:**

```promql
# Which URLs are currently down?
url_up{job="url-health-checker"} == 0

# Count of UP URLs
sum(url_up{job="url-health-checker"})

# Median response time per URL
histogram_quantile(0.50, sum by (url, le) (rate(url_response_seconds_bucket{job="url-health-checker"}[5m])))

# p95 response time across all URLs
histogram_quantile(0.95, sum by (le) (rate(url_response_seconds_bucket{job="url-health-checker"}[5m])))

# Check error rate (connection failures / timeouts)
sum by (url) (rate(url_checks_total{job="url-health-checker", result="error"}[5m]))
```

---

## Clean up

> For a complete teardown (venv, image, scrape job, and dashboard too), see
> **[CLEANUP.md](CLEANUP.md)**. Quick version:

**Native:**
```bash
kill $(pgrep -f "python app.py")
# Remove scrape job from /etc/prometheus/prometheus.yml and reload:
curl -X POST http://localhost:9090/-/reload
```

**Docker:**
```bash
cd projects-native/05-url-health-checker
docker compose down
```
