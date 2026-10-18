# ELK Project 2 — Web Access Log Analyzer

Simulates a busy web server by continuously generating **raw access-log lines** (the standard
"Apache combined" format). These lines are plain text — not structured — so they must pass through
**Logstash**, which parses them into searchable fields. This is the **full ELK pipeline**, and the
project that teaches **ETL** and **grok**.

```mermaid
flowchart LR
    APP["web-access-log-analyzer"]:::app -->|"raw text"| LOG["📄 access.log"]:::file
    LOG -->|Filebeat| LS["Logstash (grok ETL)<br/>Path B — Logstash parses"]:::ls
    LS --> ES[("Elasticsearch")]:::es --> KB["Kibana"]:::kb
    classDef app fill:#1E88E5,stroke:#0D47A1,color:#fff
    classDef es fill:#00BFB3,stroke:#00796B,color:#000
    classDef file fill:#78909C,stroke:#37474F,color:#fff
    classDef kb fill:#F04E98,stroke:#AD1457,color:#fff
    classDef ls fill:#FEC514,stroke:#B58900,color:#000
```

> Do **[Project 1](../01-flask-json-logger/README.md)** first — it's the simpler pipeline. This
> one adds the Logstash parsing step.

---

## What it does

A background thread writes a steady stream of fake web traffic to `/var/log/web/access.log`. Each
line is one big string, exactly like a real web server produces:

```
192.168.1.42 - - [10/Oct/2024:14:32:01 +0000] "GET /checkout HTTP/1.1" 500 1024 "https://google.com" "Mozilla/5.0 (X11; Linux x86_64)"
```

That's **useless for searching** as-is — it's one text blob. Logstash's `grok` filter parses it
into fields:

| Field | Value | from the raw line |
|-------|-------|-------------------|
| `clientip` | `192.168.1.42` | the IP at the start |
| `verb` | `GET` | the HTTP method |
| `request` | `/checkout` | the URL |
| `response` | `500` | the status code (as a **number**) |
| `bytes` | `1024` | response size (as a **number**) |
| `agent` | `Mozilla/5.0 …` | the browser/user agent |

Now you can ask real questions: *"how many 500s on /checkout?"*, *"top client IPs?"* — impossible
with the raw blob. **That transformation is the whole point of Logstash.**

Routes (the real "work" happens in the background generator):

```
GET /       → info about the generator
GET /stats  → how many lines have been written so far
GET /hit    → write ONE random access-log line right now (for testing)
```

---

## What you'll learn

- The **full ELK pipeline**: Filebeat → **Logstash** → Elasticsearch → Kibana
- **ETL** in action: Extract (beats input) → Transform (grok filter) → Load (ES output)
- What **grok** is and how `%{COMBINEDAPACHELOG}` parses a whole line in one go
- Why parsing matters: turning text into typed fields you can filter and aggregate

---

## The parsing lives in the shared Logstash config

Unlike Project 1, this project relies on the Logstash pipeline that ships with the stack:
**[`../../02-setup/config/pipeline/logstash.conf`](../../02-setup/config/pipeline/logstash.conf)**.
Open it — it's the `input → filter → output` (ETL) breakdown for exactly these access logs. If you
change the parsing, restart Logstash: `docker compose -f ../../02-setup/docker-compose.yml restart logstash`.

---

## Quick start

```bash
# 1. ELK stack must be running (Logstash included)
cd ../../02-setup && docker compose up -d && cd ../projects/02-web-access-log-analyzer

# 2. Start this project (app + filebeat). Traffic generates automatically.
docker compose up -d --build

# 3. Check it's producing logs
curl http://localhost:8092/stats

# 4. View parsed logs in Kibana → follow CONNECT.md
```

---

## Files

| File | Purpose |
|------|---------|
| `app/app.py` | Generates raw Apache-format access logs (background thread) |
| `app/requirements.txt` | Python dependency (`flask`) |
| `app/Dockerfile` | Container image for the app |
| `filebeat/filebeat.yml` | Filebeat config — tails the log file, ships to **Logstash** |
| `docker-compose.yml` | Runs the app + Filebeat on the `elk` network, sharing a log volume |
| `CONNECT.md` | Step-by-step: ship logs, watch Logstash parse, view in Kibana |
| `CLEANUP.md` | Tear this project down |

---

## Port

| Service | Port | URL |
|---------|------|-----|
| Web Access Log Analyzer | 8092 | http://localhost:8092 |

Parsed logs land in Elasticsearch indexes named `web-access-YYYY.MM.dd`.
