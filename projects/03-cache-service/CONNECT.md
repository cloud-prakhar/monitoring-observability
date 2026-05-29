# Connecting Cache Service to Prometheus and Grafana

---

## Before you start

Confirm the shared infrastructure is running:

```bash
docker network ls | grep monitoring
```

You should see a line with `monitoring` and driver `bridge`.
If it is missing: `cd infra && docker compose up -d`

---

## Step 1 — Start the Cache Service

From the `projects/03-cache-service/` directory:

```bash
docker compose up -d --build
```

**Verify the service is responding:**
```bash
curl http://localhost:8083/stats
```

Expected output:
```json
{"sample_keys": [], "total_keys": 0}
```

**Store and retrieve a key to confirm it works:**
```bash
# Store a key
curl -s -X POST http://localhost:8083/cache \
  -H "Content-Type: application/json" \
  -d '{"key": "greeting", "value": "hello world"}'

# Read it back
curl -s http://localhost:8083/cache/greeting
```

Expected:
```json
{"key": "greeting", "value": "hello world"}
```

**Check the raw metrics output:**
```bash
curl http://localhost:8083/metrics | grep "^cache_"
```

You should see `cache_hits_total`, `cache_misses_total`, `cache_keys_total`, etc.

---

## Step 2 — Add the scrape job to Prometheus

Open `infra/prometheus.yml` and uncomment the `cache-service` block:

```yaml
# Before:
  # - job_name: "cache-service"
  #   static_configs:
  #     - targets: ["cache-service:8083"]

# After:
  - job_name: "cache-service"
    static_configs:
      - targets: ["cache-service:8083"]
```

---

## Step 3 — Reload Prometheus

```bash
curl -X POST http://localhost:9090/-/reload
```

Check Prometheus logs to confirm it picked up the change:
```bash
docker logs prometheus | tail -3
```

Look for: `msg="Completed loading of configuration file"`

---

## Step 4 — Verify the target is UP

Open **http://localhost:9090/targets**.

`cache-service (1/1 up)` should be listed. If it shows DOWN:

```bash
# Confirm the container is on the monitoring network
docker inspect cache-service --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'

# Test reachability from inside Prometheus
docker exec prometheus wget -qO- http://cache-service:8083/metrics | head -5
```

---

## Step 5 — Generate cache traffic

The cache does nothing useful without reads and writes. Run these to populate metrics.

**Write 15 keys:**
```bash
for i in $(seq 1 15); do
  curl -s -X POST http://localhost:8083/cache \
    -H "Content-Type: application/json" \
    -d "{\"key\": \"key-$i\", \"value\": \"value-$i\"}" > /dev/null
done
echo "15 keys stored"
```

**Read keys — mix of hits and misses:**
```bash
# These will all hit (keys 1–15 exist)
for i in $(seq 1 15); do
  curl -s http://localhost:8083/cache/key-$i > /dev/null
done

# These will all miss (keys 16–25 do not exist)
for i in $(seq 16 25); do
  curl -s http://localhost:8083/cache/key-$i > /dev/null
done
```

**Store keys with a short TTL (they expire in 10 seconds):**
```bash
for i in $(seq 1 5); do
  curl -s -X POST http://localhost:8083/cache \
    -H "Content-Type: application/json" \
    -d "{\"key\": \"temp-$i\", \"value\": \"expires-soon\", \"ttl\": 10}" > /dev/null
done
echo "5 short-lived keys stored — they expire in 10s"
```

Wait 15 seconds, then read them to see cache misses from expiry:
```bash
sleep 15
for i in $(seq 1 5); do
  curl -s http://localhost:8083/cache/temp-$i
  echo ""
done
```

---

## Step 6 — Explore in Prometheus

Open **http://localhost:9090** and try these queries:

| Query | What it shows |
|-------|--------------|
| `cache_keys_total{job="cache-service"}` | Keys currently in the cache |
| `cache_hits_total{job="cache-service"}` | Running total of cache hits |
| `rate(cache_hits_total{job="cache-service"}[1m])` | Hit rate per second |
| `rate(cache_misses_total{job="cache-service"}[1m])` | Miss rate per second |
| `rate(cache_hits_total{job="cache-service"}[1m]) / (rate(cache_hits_total{job="cache-service"}[1m]) + rate(cache_misses_total{job="cache-service"}[1m]))` | Hit ratio (0–1) |
| `rate(cache_evictions_total{job="cache-service"}[1m])` | Evictions per second |
| `sum by (operation) (rate(cache_operations_total{job="cache-service"}[1m]))` | Ops breakdown by type |

**Tip — watch how hit ratio changes:**
1. Fill the cache with 20 keys (hit ratio goes up)
2. Request 20 keys that do not exist (hit ratio drops)
3. Watch the `cache_keys_total` gauge drop as TTL keys expire

---

## Step 7 — Open the Grafana dashboard

**Option A — Combined overview:**
Dashboards → Projects → **All Projects Overview** → "Project 3 — Cache Service" row.

**Option B — Project-specific dashboard:**
Dashboards → New → Import → upload `projects/03-cache-service/dashboards/cache-service.json`

---

## Metrics reference

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `cache_hits_total` | Counter | — | GET requests that found a valid, unexpired key |
| `cache_misses_total` | Counter | — | GET requests that found nothing or an expired key |
| `cache_operations_total` | Counter | operation | Every operation: set, get_hit, get_miss, get_expired, delete, delete_miss, evict |
| `cache_keys_total` | Gauge | — | Keys currently stored |
| `cache_evictions_total` | Counter | — | Keys removed by the background TTL thread |
| `cache_operation_duration_seconds` | Histogram | operation | Latency per operation (set / get / delete) |

---

## Clean up

```bash
docker compose down
```
