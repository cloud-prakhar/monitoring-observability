# Connecting Flask JSON Logger to ELK

Follow these steps in order. Each has a verify step so you know it worked before moving on.

```
flask-json-logger → app.log → Filebeat → Elasticsearch → Kibana
```

---

## Before you start

Make sure the ELK stack is up and healthy:

```bash
cd ../../02-setup
docker compose up -d
docker compose ps          # wait for elasticsearch to be "healthy"
```

Confirm the `elk` network exists (the project joins it):
```bash
docker network ls | grep elk
```
Expected: a line containing `elk`. If it's missing, the ELK stack isn't running — start it first.

---

## Step 1 — Start the app and Filebeat

From `elk/projects/01-flask-json-logger/`:

```bash
docker compose up -d --build
```

**Expected output:**
```
[+] Running 2/2
 ✔ Container flask-json-logger      Started
 ✔ Container filebeat-json-logger   Started
```

**Verify the app responds:**
```bash
curl http://localhost:8091/
```
Expected:
```json
{"service": "flask-json-logger", "status": "ok"}
```

---

## Step 2 — Generate some logs

```bash
for i in $(seq 1 20); do curl -s http://localhost:8091/login > /dev/null; done
for i in $(seq 1 20); do curl -s http://localhost:8091/order > /dev/null; done
for i in $(seq 1 20); do curl -s http://localhost:8091/error > /dev/null; done
```

**Verify the app is writing JSON logs:**
```bash
docker exec flask-json-logger tail -n 3 /var/log/app/app.log
```
You should see JSON lines like `{"@timestamp":...,"level":"INFO","message":"order placed",...}`.

---

## Step 3 — Confirm Filebeat shipped them to Elasticsearch

Filebeat ships within a few seconds. Ask Elasticsearch which indexes exist:

```bash
curl -s "http://localhost:9200/_cat/indices/flask-logs-*?v"
```

**Expected** (a `flask-logs-YYYY.MM.dd` index with a non-zero `docs.count`):
```
health status index                 ... docs.count store.size
yellow open   flask-logs-2024.10.10 ...         60     45kb
```

If no index appears, Filebeat may still be starting — check its logs:
```bash
docker logs filebeat-json-logger | tail -20
```
Look for `Connection to backoff(elasticsearch(http://elasticsearch:9200)) established`.

**Peek at an actual stored document:**
```bash
curl -s "http://localhost:9200/flask-logs-*/_search?size=1&pretty"
```
You'll see your JSON fields (`level`, `user`, `item`, `status`…) inside `_source`.

---

## Step 4 — View the logs in Kibana

Kibana needs a **Data View** (its name for "which indexes to show") before it can display logs.

1. Open **http://localhost:5601**.
2. Go to **☰ Menu → Discover** (under "Analytics").
3. If prompted, click **Create data view**.
   - **Name:** `flask-logs`
   - **Index pattern:** `flask-logs-*`
   - **Timestamp field:** `@timestamp`
   - Click **Save data view to Kibana**.
4. You're now in **Discover**. Set the time picker (top right) to **Last 15 minutes**.

You should see your log lines as a table, with a bar chart of log volume over time on top. 🎉

> **Seeing nothing?** Widen the time range (top-right) to "Last 1 hour", and generate more traffic
> with the `curl` loops from Step 2. Discover only shows logs inside the selected time window.

---

## Step 5 — Explore (this is the payoff)

In the Discover search bar (it uses **KQL** — Kibana Query Language), try:

| Search | Shows |
|--------|-------|
| `level: "ERROR"` | Only error logs |
| `level: "WARNING"` | Failed logins |
| `path: "/order" and amount > 100` | Big orders |
| `user: "user7"` | Everything one user did |
| `message: "login failed"` | All failed login attempts |

Click any field on the left (e.g. `level`) → **Visualize** to instantly chart it (e.g. a pie of
INFO vs WARNING vs ERROR). For more, see [`../../03-queries/`](../../03-queries/README.md).

---

## How it works (recap)

```mermaid
flowchart LR
    A["1 · app.py<br/>writes a JSON line"]:::app
    B["2 · Filebeat<br/>tails that file"]:::beat
    C[("3 · Elasticsearch<br/>index flask-logs-YYYY.MM.dd<br/>fully indexed")]:::es
    D["4 · Kibana<br/>you search and chart<br/>in Discover"]:::kb
    A -->|"/var/log/app/app.log<br/>(shared Docker volume)"| B
    B -->|"ships each line to<br/>elasticsearch:9200"| C
    C -->|"reads the index"| D
    classDef app fill:#1E88E5,stroke:#0D47A1,color:#fff
    classDef beat fill:#0077CC,stroke:#004C80,color:#fff
    classDef es fill:#00BFB3,stroke:#00796B,color:#000
    classDef kb fill:#F04E98,stroke:#AD1457,color:#fff
```

No Logstash anywhere — the logs were already clean JSON, so Filebeat → Elasticsearch was enough.

---

## Clean up

See **[CLEANUP.md](CLEANUP.md)**. Quick version:

```bash
docker compose down -v       # stops the app + filebeat, clears the shared log volume
```

The ELK stack in `02-setup/` keeps running for Project 2.
