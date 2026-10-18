# Clean Up — Flask JSON Logger (ELK Project 1)

Reverses [CONNECT.md](CONNECT.md): stops the app + Filebeat, clears the shared log volume, and
removes the index from Elasticsearch — leaving the shared ELK stack (`02-setup/`) running.

---

## Step 1 — Stop the app and Filebeat

From `elk/projects/01-flask-json-logger/`:

```bash
docker compose down -v
```

The `-v` also removes the `applogs` volume (the shared log file). Expected:
```
 ✔ Container filebeat-json-logger   Removed
 ✔ Container flask-json-logger      Removed
 ✔ Volume   01-flask-json-logger_applogs  Removed
```

---

## Step 2 — Delete the index from Elasticsearch

The logs you shipped still live in Elasticsearch. Remove them:

```bash
curl -X DELETE "http://localhost:9200/flask-logs-*"
```

Expected:
```json
{"acknowledged":true}
```

Verify it's gone:
```bash
curl -s "http://localhost:9200/_cat/indices/flask-logs-*?v" || echo "no flask-logs indexes"
```

---

## Step 3 — Remove the Data View from Kibana (optional)

Open Kibana → **☰ → Stack Management → Data Views** → select **flask-logs** → **Delete**.
(Harmless to leave it; it just shows "no results" once the index is gone.)

---

## Step 4 — Remove the built app image (optional)

```bash
docker rmi 01-flask-json-logger-flask-json-logger 2>/dev/null || docker image prune -f
```

---

## Verify it's clean

```bash
docker ps -a | grep -E 'flask-json-logger|filebeat-json-logger' || echo "no project containers"
```

Expected: `no project containers`. The ELK stack keeps running for other projects.
