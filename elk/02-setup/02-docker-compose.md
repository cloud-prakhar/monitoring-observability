# 02 — Run ELK with Docker Compose

> You ran the three containers by hand in [`01-docker-cli.md`](01-docker-cli.md). That's a lot of
> long commands to remember and re-type. **Compose** puts the whole stack in one file so you start
> it with a single command — and it's what the projects expect.

---

## Prerequisites

- You finished [`01-docker-cli.md`](01-docker-cli.md) and **removed** those containers
  (`docker rm -f elasticsearch kibana logstash`).
- You've set `vm.max_map_count` (see [README.md](README.md)).
- You are in the `elk/02-setup/` directory.

---

## Step 1 — Look at the Compose file

Open [`docker-compose.yml`](docker-compose.yml). It describes the same three containers you started
by hand, plus the volume and network. **Every CLI flag maps to a line in this file:**

| `docker run` flag (CLI) | Compose equivalent |
|-------------------------|--------------------|
| `--name elasticsearch` | `container_name: elasticsearch` |
| `--net elk` | `networks: [elk]` |
| `-p 9200:9200` | `ports: ["9200:9200"]` |
| `-e "discovery.type=single-node"` | `environment: [discovery.type=single-node]` |
| `-v esdata:/usr/share/...` | `volumes: [esdata:/usr/share/...]` |
| `-v $(pwd)/config/...` | `volumes: [./config/...:...:ro]` |
| `docker network create elk` | the `networks: elk:` block at the bottom |
| `docker volume create esdata` | the `volumes: esdata:` block at the bottom |

One extra thing Compose adds that's painful to do by hand: a **healthcheck** on Elasticsearch plus
`depends_on: condition: service_healthy`, so Logstash and Kibana **wait** until Elasticsearch is
actually ready before they start. No more guessing with `sleep`.

---

## Step 2 — Start the whole stack

```bash
docker compose up -d
```

**Expected output:**
```
[+] Running 4/4
 ✔ Network elk              Created
 ✔ Container elasticsearch  Healthy
 ✔ Container logstash       Started
 ✔ Container kibana         Started
```

> The first run downloads ~2GB of images — be patient. Later runs are instant.

---

## Step 3 — Watch it come up

```bash
docker compose ps
```

Wait until `elasticsearch` shows `(healthy)`. Then verify each piece:

```bash
curl http://localhost:9200/_cluster/health?pretty   # status: green or yellow
curl http://localhost:9600                           # Logstash version JSON
```

Open **http://localhost:5601** — give Kibana ~1 minute, then you'll see the home page.

> **Yellow cluster status is normal** on one node (it just can't place replica copies — there's
> nowhere to put them). It's healthy.

---

## Step 4 — You're done — go ship some logs

The stack is up and the `elk` network exists. Head to the first project:

```bash
cd ../projects/01-flask-json-logger
```

Follow its [README.md](../projects/01-flask-json-logger/README.md) and
[CONNECT.md](../projects/01-flask-json-logger/CONNECT.md).

---

## Everyday commands

| Goal | Command |
|------|---------|
| Start the stack | `docker compose up -d` |
| Stop it (keep logs) | `docker compose down` |
| Stop and wipe all logs | `docker compose down -v` |
| See status | `docker compose ps` |
| Tail Logstash logs | `docker logs -f logstash` |
| Restart after editing the pipeline | `docker compose restart logstash` |

> **Editing the Logstash pipeline?** After changing `config/pipeline/logstash.conf`, run
> `docker compose restart logstash` so it reloads the file. (Same gotcha as restarting Prometheus
> after editing `prometheus.yml` in this repo.)

---

## Clean up

See **[CLEANUP.md](CLEANUP.md)** for a full teardown. Quick version:

```bash
docker compose down -v    # stops everything and deletes the esdata volume
```

---

**Next:** [`../projects/01-flask-json-logger/`](../projects/01-flask-json-logger/README.md) — ship
your first real logs into ELK.
