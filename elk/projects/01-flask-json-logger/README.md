# ELK Project 1 — Flask JSON Logger

A small Flask app that writes **structured JSON logs**. Because the logs are already clean JSON,
they go **straight to Elasticsearch** via Filebeat — no Logstash needed. This is the simplest ELK
pipeline and the best place to start.

```
flask-json-logger  ──writes JSON──▶  app.log  ──Filebeat──▶  Elasticsearch  ──▶  Kibana
                                                  (Path A — no Logstash)
```

> **New to ELK?** Read [`../../01-fundamentals/`](../../01-fundamentals/README.md) and bring the
> stack up with [`../../02-setup/`](../../02-setup/README.md) first.

---

## What it does

Exposes a few routes. Every request writes a JSON log line to `/var/log/app/app.log` (a Docker
volume shared with Filebeat).

```
GET /        → home page          (logs INFO)
GET /login   → 80% succeed         (logs INFO on success, WARNING on failure)
GET /order   → places an order     (logs INFO with item + amount)
GET /error   → 50% fail            (logs ERROR with an error type)
GET /health  → health check        (no logging — avoids noise)
```

A sample log line:

```json
{"@timestamp":"2024-10-10T14:32:01.123+00:00","level":"INFO","message":"order placed",
 "service":"flask-json-logger","method":"GET","path":"/order","status":200,
 "user":"user7","item":"laptop","amount":342.50,"latency_ms":88.1,"request_id":"a1b2c3"}
```

**Why JSON logs?** Each field (`level`, `user`, `status`, `amount`…) becomes a searchable field in
Elasticsearch automatically. No parsing required — that's why this project skips Logstash. (Project
2 shows the opposite case: raw text logs that *do* need Logstash.)

---

## What you'll learn

- How an app writes structured logs to a file
- How **Filebeat** tails that file and ships it
- The **Path A** pipeline: Filebeat → Elasticsearch directly (no Logstash)
- How to view logs in **Kibana** and create a Data View

---

## Quick start

```bash
# 1. Make sure the ELK stack is running
cd ../../02-setup && docker compose up -d && cd ../projects/01-flask-json-logger

# 2. Start this project (app + filebeat)
docker compose up -d --build

# 3. Generate some logs
curl http://localhost:8091/
curl http://localhost:8091/login
curl http://localhost:8091/order
curl http://localhost:8091/error

# 4. View them in Kibana → follow CONNECT.md
```

---

## Files

| File | Purpose |
|------|---------|
| `app/app.py` | Flask app that writes JSON logs |
| `app/requirements.txt` | Python dependency (`flask`) |
| `app/Dockerfile` | Container image for the app |
| `filebeat/filebeat.yml` | Filebeat config — tails the log file, ships to Elasticsearch |
| `docker-compose.yml` | Runs the app + Filebeat on the `elk` network, sharing a log volume |
| `CONNECT.md` | Step-by-step: ship logs, verify in Elasticsearch, view in Kibana |
| `CLEANUP.md` | Tear this project down |

---

## Port

| Service | Port | URL |
|---------|------|-----|
| Flask JSON Logger | 8091 | http://localhost:8091 |

Logs land in Elasticsearch indexes named `flask-logs-YYYY.MM.dd`.
