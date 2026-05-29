# Project 3 — Cache Service

An in-memory key-value cache with TTL support, built in Python/Flask.
Think of it as a stripped-down Redis. A background thread evicts expired keys
automatically. This project produces the most varied metric types of the three.

---

## What it does

```
  POST /cache         → store a value (with optional ttl in seconds)
  GET  /cache/<key>   → read a value → hit / miss / expired
  DELETE /cache/<key> → remove a value
  GET  /stats         → total key count
  GET  /metrics       → Prometheus scrapes this
```

**TTL expiry flow:**
1. You store `{"key": "x", "value": "y", "ttl": 10}` — key expires in 10 seconds
2. The background eviction thread wakes every 5 seconds and removes expired keys
3. `cache_keys_total` drops; `cache_evictions_total` increments
4. A GET for that key returns a miss

---

## Metrics produced

| Metric | Type | Labels | What it measures |
|--------|------|--------|-----------------|
| `cache_hits_total` | Counter | — | GETs that returned a valid key |
| `cache_misses_total` | Counter | — | GETs that found nothing or an expired key |
| `cache_operations_total` | Counter | operation | set, get_hit, get_miss, get_expired, delete, delete_miss, evict |
| `cache_keys_total` | Gauge | — | Keys currently in the cache |
| `cache_evictions_total` | Counter | — | Keys removed by the TTL thread |
| `cache_operation_duration_seconds` | Histogram | operation | Latency per operation type |

**Why the `operation` label matters:**
The `cache_operations_total` counter has a label so you can split it in PromQL:
```promql
sum by (operation) (rate(cache_operations_total{job="cache-service"}[1m]))
```
This shows you exactly which types of operations are happening — sets, hits, misses, evictions — all on one graph.

---

## Quick start

```bash
# 1. Start shared infra
cd infra && docker compose up -d && cd ..

# 2. Start this project
cd projects/03-cache-service
docker compose up -d --build

# 3. Test the cache
curl -X POST http://localhost:8083/cache \
  -H "Content-Type: application/json" \
  -d '{"key": "hello", "value": "world", "ttl": 30}'

curl http://localhost:8083/cache/hello

# 4. Connect to Prometheus + Grafana
# Follow CONNECT.md
```

---

## Files

| File | Purpose |
|------|---------|
| `app/app.py` | Flask cache app + background eviction thread + metrics |
| `app/requirements.txt` | Python dependencies |
| `app/Dockerfile` | Container image |
| `docker-compose.yml` | Runs the app on the `monitoring` network |
| `CONNECT.md` | Step-by-step integration guide |
| `dashboards/cache-service.json` | Grafana dashboard for this project |

---

## Port

| Service | Port | URL |
|---------|------|-----|
| Cache Service API | 8083 | http://localhost:8083 |
| Metrics | 8083 | http://localhost:8083/metrics |
