# Clean Up — Web Access Log Analyzer (ELK Project 2)

Reverses [CONNECT.md](CONNECT.md): stops the app + Filebeat, clears the shared log volume, and
removes the index from Elasticsearch — leaving the shared ELK stack (`02-setup/`) running.

---

## Step 1 — Stop the app and Filebeat

From `elk/projects/02-web-access-log-analyzer/`:

```bash
docker compose down -v
```

The `-v` also removes the `weblogs` volume. Expected:
```
 ✔ Container filebeat-web-access        Removed
 ✔ Container web-access-log-analyzer    Removed
 ✔ Volume   02-web-access-log-analyzer_weblogs  Removed
```

---

## Step 2 — Delete the index from Elasticsearch

```bash
curl -X DELETE "http://localhost:9200/web-access-*"
```

Expected:
```json
{"acknowledged":true}
```

Verify:
```bash
curl -s "http://localhost:9200/_cat/indices/web-access-*?v" || echo "no web-access indexes"
```

---

## Step 3 — Remove the Data View from Kibana (optional)

Kibana → **☰ → Stack Management → Data Views** → **web-access** → **Delete**.

---

## Step 4 — Remove the built app image (optional)

```bash
docker rmi 02-web-access-log-analyzer-web-access-log-analyzer 2>/dev/null || docker image prune -f
```

---

## A note on Logstash

The Logstash pipeline lives in `02-setup/` and is shared infrastructure — leave it running. It does
no harm with no logs flowing in. It's torn down with the whole stack via `02-setup/CLEANUP.md`.

---

## Verify it's clean

```bash
docker ps -a | grep -E 'web-access-log-analyzer|filebeat-web-access' || echo "no project containers"
```

Expected: `no project containers`.
