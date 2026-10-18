# ELK Setup — Install the Stack with Docker

> **What you'll build:** the full ELK Stack running locally —
> **Elasticsearch** (storage/search) on `9200`, **Logstash** (ETL) on `5044`/`9600`, and
> **Kibana** (the UI) on `5601` — all on a shared Docker network called `elk` that the projects
> will join.

> **Read [../01-fundamentals/](../01-fundamentals/README.md) first** if you haven't. This section
> assumes you know what E, L, and K do and what Filebeat is.

---

## Prerequisites

- Docker Desktop installed and running. On Windows, complete [`../../docs/wsl-setup.md`](../../docs/wsl-setup.md) first.
- **At least 4GB of RAM free.** Elasticsearch is a Java app and needs memory. If containers keep
  dying, this is almost always why — see Troubleshooting.

**Verify Docker works:**
```bash
docker run hello-world
docker compose version
```

---

## ⚠️ One required host setting: `vm.max_map_count`

Elasticsearch needs the Linux kernel setting `vm.max_map_count` to be at least `262144`, or it
**crashes on startup** with `max virtual memory areas vm.max_map_count [65530] is too low`. This
is the single most common ELK setup failure.

```bash
# Check the current value (Linux / WSL2):
cat /proc/sys/vm/max_map_count

# Set it for the current session (resets on reboot):
sudo sysctl -w vm.max_map_count=262144

# Make it permanent across reboots:
echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.d/99-elasticsearch.conf
```

> **macOS / Windows Docker Desktop:** the setting applies to Docker's Linux VM, which usually
> already has a high enough value. If Elasticsearch crashes, run the `sysctl` command above inside
> WSL2 (Windows) — see [troubleshooting](../../docs/troubleshooting.md).

---

## Learning path (do these in order)

### Step 1 — The manual way
Follow **[01-docker-cli.md](01-docker-cli.md)**.

You'll start Elasticsearch, Kibana, and Logstash one container at a time with `docker run`, so you
understand what each one is and how they find each other. **Don't skip this** — it's what makes the
Compose file make sense.

### Step 2 — The Compose shortcut
Follow **[02-docker-compose.md](02-docker-compose.md)**.

You'll bring up the entire stack with one `docker compose up -d`, using the
[`docker-compose.yml`](docker-compose.yml) in this folder. This is what you'll actually use day to
day and what the projects expect.

---

## Files in this directory

| File | Purpose |
|------|---------|
| `docker-compose.yml` | The whole ELK stack in one file (creates the `elk` network) |
| `config/logstash.yml` | Logstash global settings |
| `config/pipeline/logstash.conf` | The Logstash ETL pipeline (input → filter → output) |
| `01-docker-cli.md` | Manual `docker run` walkthrough |
| `02-docker-compose.md` | Compose walkthrough + mapping back to the CLI steps |
| `CLEANUP.md` | Tear the whole stack down |

---

## After the stack is up

| Check | URL / command | Expected |
|-------|---------------|----------|
| Elasticsearch alive | http://localhost:9200 | JSON with `"cluster_name" : "elk-lab"` |
| Cluster healthy | `curl localhost:9200/_cluster/health?pretty` | `"status" : "green"` or `"yellow"` |
| Kibana alive | http://localhost:5601 | The Kibana home page (give it ~1 min to start) |
| Logstash alive | http://localhost:9600 | JSON with Logstash version info |

> **Yellow status is fine** on a single node. Elasticsearch wants a backup copy (replica) of each
> index on a *different* node — but there's only one node here, so replicas stay unassigned and the
> status is yellow. It's healthy; it just can't make backups it has nowhere to put.

Once all four checks pass, go run a project:
**[../projects/01-flask-json-logger/](../projects/01-flask-json-logger/README.md)**.

---

## Quick reference — ports

| Service | Port | URL |
|---------|------|-----|
| Elasticsearch | 9200 | http://localhost:9200 |
| Logstash (Beats input) | 5044 | (used by Filebeat, not a web page) |
| Logstash (monitoring) | 9600 | http://localhost:9600 |
| Kibana | 5601 | http://localhost:5601 |

---

## Troubleshooting

**Elasticsearch container exits immediately:**
```bash
docker logs elasticsearch | tail -20
```
- `max virtual memory areas vm.max_map_count [65530] is too low` → run the `sysctl` fix above.
- `Cannot allocate memory` / killed → lower the heap (`ES_JAVA_OPTS=-Xms256m -Xmx256m`) or give
  Docker more RAM in Docker Desktop settings.

**Kibana shows "Kibana server is not ready yet":** it's still starting, or Elasticsearch isn't up.
Wait a minute, then `docker logs kibana | tail -20`. Make sure Elasticsearch is healthy first.

**Port already in use (9200/5601/5044):** something else is using it. Stop that process or change
the host port in `docker-compose.yml` (e.g. `"9201:9200"`).

Full error-to-fix list: [`../../docs/troubleshooting.md`](../../docs/troubleshooting.md).
