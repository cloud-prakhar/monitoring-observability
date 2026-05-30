# Connecting Flask Web API to Prometheus and Grafana

Follow these steps exactly, in order. Each step has a verify command so you know it worked before moving on.

---

## Before you start

Make sure the shared infrastructure is running:

```bash
cd infra
docker compose up -d
```

Confirm:
```bash
docker network ls | grep monitoring
```

Expected output:
```
xxxxxxxx   monitoring   bridge    local
```

If the `monitoring` network does not exist, the project container will fail to start.

---

## Step 1 — Start the Flask Web API

From the `projects/01-flask-web-api/` directory:

```bash
docker compose up -d --build
```

**Expected output:**
```
[+] Building 12.4s (7/7) FINISHED
 => [flask-web-api] FROM python:3.12-slim
 => [flask-web-api] RUN pip install -r requirements.txt
 => [flask-web-api] COPY app.py .
[+] Running 1/1
 ✔ Container flask-web-api  Started
```

**Verify the app is responding:**
```bash
curl http://localhost:8081/
```

Expected output:
```json
{"service": "flask-web-api", "status": "ok"}
```

**Check the raw metrics:**
```bash
curl http://localhost:8081/metrics
```

You should see lines like `http_requests_total` and `http_request_duration_seconds_bucket`.
If you see this output, the app is ready to be scraped.

---

## Step 2 — Add the scrape job to Prometheus

Open `infra/prometheus.yml` in any text editor. Find this block and uncomment it (remove the `#` from the 3 lines):

```yaml
# Before (commented out):
  # - job_name: "flask-web-api"
  #   static_configs:
  #     - targets: ["flask-web-api:8081"]

# After (uncommented):
  - job_name: "flask-web-api"
    static_configs:
      - targets: ["flask-web-api:8081"]
```

Make sure the indentation matches the `prometheus` job above it (2 spaces before the dash).

---

## Step 3 — Reload Prometheus

Prometheus watches for a reload signal — you do not need to restart it:

```bash
curl -X POST http://localhost:9090/-/reload
```

Expected: HTTP 200 response (empty body). You can also check the Prometheus logs:

```bash
docker logs prometheus | tail -5
```

Look for:
```
msg="Completed loading of configuration file" filename=/etc/prometheus/prometheus.yml
```

---

## Step 4 — Verify the target is UP

Open **http://localhost:9090/targets** in your browser.

You should see two targets:
- `prometheus (1/1 up)` — was already there
- `flask-web-api (1/1 up)` — newly added

If `flask-web-api` shows **DOWN**, check:
```bash
# Is the container running?
docker ps | grep flask-web-api

# Is it on the monitoring network?
docker inspect flask-web-api --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'

# Can Prometheus reach it?
docker exec prometheus wget -qO- http://flask-web-api:8081/metrics | head -3
```

---

## Step 5 — Generate traffic and explore in Prometheus

Send some requests to create metric data:

```bash
# Fast requests
for i in $(seq 1 20); do curl -s http://localhost:8081/ > /dev/null; done

# Requests to different endpoints
for i in $(seq 1 10); do curl -s http://localhost:8081/users > /dev/null; done
for i in $(seq 1 10); do curl -s http://localhost:8081/slow > /dev/null; done

# Requests that sometimes fail (generates error rate metrics)
for i in $(seq 1 15); do curl -s http://localhost:8081/error > /dev/null; done
```

Now open **http://localhost:9090** and try these queries:

| Query | What it shows |
|-------|--------------|
| `http_requests_total{job="flask-web-api"}` | All request counters with labels |
| `rate(http_requests_total{job="flask-web-api"}[1m])` | Requests per second by endpoint |
| `sum by (endpoint) (rate(http_requests_total{job="flask-web-api"}[1m]))` | Rate split by endpoint |
| `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="flask-web-api"}[1m])) by (le))` | p95 response time |
| `rate(http_requests_total{job="flask-web-api", status_code="500"}[1m])` | Error rate |

---

## Step 6 — Open the Grafana dashboard

Open **http://localhost:3000** and log in with `admin` / `admin`.

**Option A — Combined overview (all projects):**
Dashboards → Projects → **All Projects Overview** → look at the "Project 1 — Flask Web API" row.

**Option B — Import the project-specific dashboard:**
1. Dashboards → New → Import
2. Click "Upload dashboard JSON file"
3. Select `projects/01-flask-web-api/dashboards/flask-web-api.json`
4. Click Import

This gives you a full-detail dashboard for just this project.

---

## Metrics reference

| Metric name | Type | Labels | What it measures |
|-------------|------|--------|-----------------|
| `http_requests_total` | Counter | method, endpoint, status_code | Total requests received |
| `http_request_duration_seconds` | Histogram | method, endpoint | Response time distribution |
| `active_requests` | Gauge | — | Requests currently in-flight |

**Useful derived queries:**

```promql
# Requests per second (all endpoints combined):
sum(rate(http_requests_total{job="flask-web-api"}[1m]))

# Error percentage (5xx responses):
100 * sum(rate(http_requests_total{job="flask-web-api", status_code=~"5.."}[1m]))
    / sum(rate(http_requests_total{job="flask-web-api"}[1m]))

# 99th percentile latency:
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket{job="flask-web-api"}[1m])) by (le)
)
```

---

## Clean up

> For a complete teardown (image, scrape job, and dashboard too), see **[CLEANUP.md](CLEANUP.md)**.
> Quick version:

```bash
# Stop the Flask app (infra keeps running):
docker compose down

# Also remove the build image:
docker compose down --rmi local
```

To also disconnect from Prometheus, re-comment the `flask-web-api` job in `infra/prometheus.yml`
and reload: `curl -X POST http://localhost:9090/-/reload`
