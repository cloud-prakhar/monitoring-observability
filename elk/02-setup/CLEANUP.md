# Clean Up — ELK Stack

Tears down the shared ELK Stack. Do this **after** cleaning up any projects that depend on it
(both project CLEANUP files leave `02-setup/` running for other projects).

---

## Step 1 — Stop the stack

Run from the `elk/02-setup/` directory:

```bash
docker compose down
```

Expected output:
```
 ✔ Container kibana         Removed
 ✔ Container logstash       Removed
 ✔ Container elasticsearch  Removed
 ✔ Network elk              Removed
```

This keeps the `esdata` volume — all your indexed logs survive for next time.

---

## Step 2 — Also wipe the indexed logs (optional)

To delete everything Elasticsearch stored and start fresh:

```bash
docker compose down -v
```

The `-v` removes the `esdata` volume. Next `docker compose up -d` gives you an empty Elasticsearch.

---

## Step 3 — Remove the downloaded images (optional)

The ELK images are large (~2GB total). Remove them to reclaim disk space:

```bash
docker rmi docker.elastic.co/elasticsearch/elasticsearch:8.17.0 \
           docker.elastic.co/logstash/logstash:8.17.0 \
           docker.elastic.co/kibana/kibana:8.17.0 \
           docker.elastic.co/beats/filebeat:8.17.0 2>/dev/null || true
```

---

## If you used the manual CLI path (01-docker-cli.md)

Compose won't know about hand-started containers. Remove them directly:

```bash
docker rm -f elasticsearch kibana logstash
docker volume rm esdata 2>/dev/null || true
docker network rm elk 2>/dev/null || true
```

> The `elk` network only removes once **no** containers (including projects) are still attached.
> Stop the projects first.

---

## Verify it's clean

```bash
docker ps -a | grep -E 'elasticsearch|logstash|kibana' || echo "no ELK containers"
docker network ls | grep elk || echo "no elk network"
```

Expected: `no ELK containers` and `no elk network`.
