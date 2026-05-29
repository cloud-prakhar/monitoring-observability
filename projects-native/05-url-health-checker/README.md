# Project 5 — URL Health Checker

A Python/Flask app that polls a list of URLs every 30 seconds and tracks their
availability and response time as Prometheus metrics. Works like a lightweight version
of Prometheus Blackbox Exporter.

This project teaches you how to build an outside-in monitoring view: instead of
instrumenting code from within the app, you observe services from the outside by
probing their HTTP endpoints.

---

## What it does

A background thread loops through all registered URLs, makes an HTTP GET, and records
what happened. The target list is dynamic — you can add or remove URLs at runtime
via the API without restarting the app.

Routes:
```
GET    /         → {"service": "url-health-checker", "status": "ok"}
GET    /targets  → list all monitored URLs
POST   /targets  → add a URL to monitor  body: {"url": "http://..."}
DELETE /targets  → remove a URL          body: {"url": "http://..."}
GET    /status   → current up/down status of every URL (includes last response code and latency)
GET    /metrics  → Prometheus scrapes this
```

Default targets (monitors all 5 services in this repo):
```
http://localhost:9090/-/healthy   → Prometheus
http://localhost:3000/api/health  → Grafana
http://localhost:8081/            → Project 1 — Flask Web API
http://localhost:8082/stats       → Project 2 — Job Processor
http://localhost:8083/stats       → Project 3 — Cache Service
http://localhost:8084/            → Project 4 — System Monitor
```

---

## Metrics produced

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `url_up` | Gauge | url | `1` if last check was HTTP 2xx/3xx, `0` if failed or timed out |
| `url_status_code` | Gauge | url | Last HTTP status code (`0` = connection error or timeout) |
| `url_response_seconds` | Histogram | url | Response time per URL per check |
| `url_checks_total` | Counter | url, result | Total checks (result = `success` or `error`) |

**Why this metric design?**
- `url_up` as a Gauge is the key signal — an alert rule `url_up == 0` fires when any URL goes down
- `url_response_seconds` as a Histogram lets you compute percentiles across the 30-second polling window
- `url_checks_total` with a `result` label makes it easy to plot success rate vs error rate side by side

---

## Quick start

### Native WSL2 path

```bash
cd projects-native/05-url-health-checker/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Wait 30 seconds for the first polling cycle, then check:
```bash
curl -s http://localhost:8085/status | python3 -m json.tool
```

### Docker path

```bash
# Requires infra to be running first:
cd infra && docker compose up -d && cd ..

cd projects-native/05-url-health-checker
docker compose up -d --build
```

> **Note on Docker networking:** this project uses `network_mode: host` so the container
> can reach `localhost:8081–8084`. The Prometheus scrape target is `localhost:8085`,
> not `url-health-checker:8085`. See `CONNECT.md` for details.

Follow **[CONNECT.md](CONNECT.md)** to wire the running app into Prometheus and Grafana.

---

## Add a URL at runtime

```bash
# Add any URL
curl -X POST http://localhost:8085/targets \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Remove it
curl -X DELETE http://localhost:8085/targets \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## Try these PromQL queries

Once Prometheus is scraping this app:

```promql
# Which URLs are currently down?
url_up{job="url-health-checker"} == 0

# Count of UP endpoints
sum(url_up{job="url-health-checker"})

# Median response time per URL
histogram_quantile(0.50,
  sum by (url, le) (rate(url_response_seconds_bucket{job="url-health-checker"}[5m]))
)

# Check error rate (connection failures + timeouts)
sum by (url) (rate(url_checks_total{job="url-health-checker", result="error"}[5m]))
```

---

## Files

| File | Purpose |
|------|---------|
| `app/app.py` | Flask app: URL poller thread + dynamic target registry + metrics |
| `app/requirements.txt` | `flask`, `prometheus-client`, `requests` |
| `app/Dockerfile` | Container image for the Docker path |
| `docker-compose.yml` | Docker path: `network_mode: host` for localhost resolution |
| `CONNECT.md` | Step-by-step wiring guide — Path A (native) and Path B (Docker) |
| `dashboards/url-health-checker.json` | Importable Grafana dashboard (8 panels) |

---

## Port

| Service | Port | URL |
|---------|------|-----|
| URL Health Checker | 8085 | http://localhost:8085 |
| Status page | 8085 | http://localhost:8085/status |
| Metrics | 8085 | http://localhost:8085/metrics |
