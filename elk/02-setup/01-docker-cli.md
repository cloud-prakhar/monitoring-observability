# 01 — Run ELK with Plain Docker Commands

> **Do this first.** We start each piece of ELK by hand so you understand what it is and how the
> three find each other. After this, [`02-docker-compose.md`](02-docker-compose.md) collapses it
> all into one command.
>
> **Goal:** Elasticsearch, Kibana, and Logstash all running and talking to each other.

---

## Prerequisites

- Docker is running (`docker --version` prints a version).
- You've set `vm.max_map_count` (see [README.md](README.md) — Elasticsearch crashes without it).
- You are in the `elk/02-setup/` directory.

---

## Step 1 — Create a network so the containers can talk

All three containers must be on the same network to reach each other **by name**. We create that
network ourselves (Compose will do this automatically later).

```bash
docker network create elk
```

**Verify:**
```bash
docker network ls | grep elk
```
You should see `elk` in the list.

> **Why a network?** Without a shared network, containers can't find each other. With one, Kibana
> can reach Elasticsearch at `http://elasticsearch:9200` using its container name as a hostname —
> the same idea as `http://prometheus:9090` in the Grafana part of this repo.

---

## Step 2 — Create a volume for Elasticsearch data

```bash
docker volume create esdata
```

**Why?** Elasticsearch stores your indexed logs here. Without a named volume, every log you index
is lost when the container is removed.

---

## Step 3 — Start Elasticsearch (the database)

```bash
docker run -d \
  --name elasticsearch \
  --net elk \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -e "cluster.name=elk-lab" \
  -v esdata:/usr/share/elasticsearch/data \
  docker.elastic.co/elasticsearch/elasticsearch:8.17.0
```

**What each flag does:**

| Flag | Meaning |
|------|---------|
| `-d` | Detached — run in the background |
| `--name elasticsearch` | Name it so other containers can reach it as `elasticsearch` |
| `--net elk` | Join the `elk` network |
| `-p 9200:9200` | Expose the REST API to your laptop |
| `-e discovery.type=single-node` | Run alone, don't look for a cluster |
| `-e xpack.security.enabled=false` | No passwords/TLS — **local learning only** |
| `-e ES_JAVA_OPTS=-Xms512m -Xmx512m` | Give the JVM 512MB heap |
| `-v esdata:/usr/share/elasticsearch/data` | Persist indexed logs in the volume |

**Wait ~30 seconds, then verify:**
```bash
curl http://localhost:9200
```

**Expected output** (abbreviated):
```json
{
  "name" : "...",
  "cluster_name" : "elk-lab",
  "version" : { "number" : "8.17.0", ... },
  "tagline" : "You Know, for Search"
}
```

If you get "connection refused", it's still starting (or crashed — check `docker logs elasticsearch`).

---

## Step 4 — Start Kibana (the UI)

```bash
docker run -d \
  --name kibana \
  --net elk \
  -p 5601:5601 \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  docker.elastic.co/kibana/kibana:8.17.0
```

> Note `ELASTICSEARCH_HOSTS=http://elasticsearch:9200` uses the **container name**, not
> `localhost`. Inside the `elk` network, `elasticsearch` resolves to that container.

**Verify** — open **http://localhost:5601** in your browser. Kibana takes ~1 minute to start;
if you see "Kibana server is not ready yet", wait and refresh. Eventually you get the home page.

---

## Step 5 — Start Logstash (the ETL pipeline)

Logstash needs our two config files mounted in. Run this from `elk/02-setup/`:

```bash
docker run -d \
  --name logstash \
  --net elk \
  -p 5044:5044 \
  -p 9600:9600 \
  -e "LS_JAVA_OPTS=-Xms256m -Xmx256m" \
  -v "$(pwd)/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro" \
  -v "$(pwd)/config/pipeline:/usr/share/logstash/pipeline:ro" \
  docker.elastic.co/logstash/logstash:8.17.0
```

| Flag | Meaning |
|------|---------|
| `-p 5044:5044` | The Beats input — Filebeat will connect here |
| `-p 9600:9600` | Logstash's monitoring/health API |
| `-v .../logstash.yml` | Mount global settings |
| `-v .../pipeline` | Mount the ETL pipeline (`logstash.conf`) |

**Verify:**
```bash
curl http://localhost:9600
```
**Expected:** JSON containing `"version"` and `"status":"green"`. Logstash takes ~30–60s to boot;
watch it with `docker logs -f logstash` until you see `Pipeline started`.

---

## Step 6 — Confirm all three are running

```bash
docker ps
```

You should see `elasticsearch`, `kibana`, and `logstash` all listed.

```
NAMES           PORTS
elasticsearch   0.0.0.0:9200->9200/tcp
kibana          0.0.0.0:5601->5601/tcp
logstash        0.0.0.0:5044->5044/tcp, 0.0.0.0:9600->9600/tcp
```

**You now have a working ELK Stack.** 🎉

---

## Step 7 — Clean up (before moving to Compose)

Compose will try to create containers with the same names, so remove these first:

```bash
docker rm -f elasticsearch kibana logstash
```

Leave the `esdata` volume and `elk` network — Compose can reuse them. (To wipe everything:
`docker volume rm esdata && docker network rm elk`.)

---

## Troubleshooting

**A container isn't in `docker ps`:**
```bash
docker ps -a              # shows stopped containers
docker logs <name>        # see why it exited
```

**Elasticsearch exited** → almost always `vm.max_map_count` (see [README.md](README.md)) or not
enough RAM. Check `docker logs elasticsearch | tail -20`.

**Kibana "not ready yet"** → Elasticsearch isn't up, or Kibana is still booting. Wait, refresh.

---

**Next:** [`02-docker-compose.md`](02-docker-compose.md) — the same three containers in one file,
one command.
