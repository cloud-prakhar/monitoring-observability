# 01 — Run Prometheus + Grafana Together (Manual)

> **Do this first.** We run both containers by hand so you understand the network
> plumbing that makes them talk to each other.
>
> **Goal:** Grafana at `http://localhost:3000` showing Prometheus metrics from
> `http://localhost:9090`, connected via a shared Docker network.

---

## The #1 Beginner Confusion — `localhost` vs Service Name

Before running any commands, read this carefully. It explains the most common
integration mistake.

```
WRONG mental model:
                                 ┌──────────────┐
  Your browser → localhost:3000  │   Grafana    │ → http://localhost:9090 ✗
                                 └──────────────┘
                                        ≠
                                 ┌──────────────┐
                                 │  Prometheus  │
                                 └──────────────┘

RIGHT mental model:
                                 ┌──────────────────────────────────────────┐
                                 │           Docker network: monitoring     │
                                 │                                          │
  Your browser → localhost:3000  │  ┌──────────┐       ┌─────────────┐    │
                                 │  │  Grafana │──────▶│  Prometheus │    │
                                 │  │          │ :9090  │             │    │
                                 │  └──────────┘       └─────────────┘    │
                                 │                                          │
                                 └──────────────────────────────────────────┘
```

**Why `localhost` fails between containers:**

Each container has its own network namespace — its own private `localhost`.
When Grafana asks for `http://localhost:9090`, it is asking for port 9090 on
*itself*, not on the Prometheus container. Prometheus is not there, so the
request fails.

**The fix:** Put both containers on the same Docker **network**. Docker gives each
container a hostname matching its name (or service name). Grafana can then reach
Prometheus at `http://prometheus:9090` — Docker's DNS resolves `prometheus` to the
correct container IP.

This is exactly what we do in the steps below.

---

## Prerequisites

- You have completed `../prometheus-setup/` and `../grafana-setup/` (or at least read them).
- No containers named `prometheus` or `grafana` are currently running:
  ```bash
  docker rm -f prometheus grafana 2>/dev/null; echo "clean"
  ```

---

## Step 1 — Create a shared Docker network

**What is a Docker network?** A virtual network bridge that lets containers talk to each
other by service name. Without a shared network, containers are isolated.

```bash
docker network create monitoring
```

**Expected output:**
```
a7b3c4d5e6f7...  (a network ID hash)
```

**Verify:**
```bash
docker network ls
```
You should see `monitoring` in the list with driver `bridge`.

---

## Step 2 — Create named volumes

```bash
docker volume create promdata
docker volume create grafdata
```

---

## Step 3 — Run Prometheus on the monitoring network

```bash
docker run -d \
  --name prometheus \
  --network monitoring \
  -p 9090:9090 \
  -v "$(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
  -v promdata:/prometheus \
  prom/prometheus:v2.51.0 \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/usr/share/prometheus/console_libraries \
  --web.console.templates=/usr/share/prometheus/consoles
```

New flag vs the standalone setup:

| Flag | Meaning |
|------|---------|
| `--network monitoring` | Attaches this container to the `monitoring` network we just created |

---

## Step 4 — Run Grafana on the same monitoring network

```bash
docker run -d \
  --name grafana \
  --network monitoring \
  -p 3000:3000 \
  -v grafdata:/var/lib/grafana \
  -v "$(pwd)/grafana/provisioning/datasources:/etc/grafana/provisioning/datasources:ro" \
  -v "$(pwd)/grafana/provisioning/dashboards:/etc/grafana/provisioning/dashboards:ro" \
  -v "$(pwd)/grafana/dashboards:/var/lib/grafana/dashboards:ro" \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:10.4.2
```

New flags vs the standalone setup:

| Flag | Meaning |
|------|---------|
| `--network monitoring` | Same network as Prometheus — they can now reach each other by name |
| `-v .../datasources:...` | Mounts provisioning config that auto-registers Prometheus as a data source |
| `-v .../dashboards:...` | Mounts the dashboard provider config |
| `-v .../grafana/dashboards:...` | Mounts the dashboard JSON files |

---

## Step 5 — Verify both containers are running

```bash
docker ps
```

**Expected output:**
```
CONTAINER ID   IMAGE                       PORTS                    NAMES
xxxxxxxxxxxx   grafana/grafana:10.4.2      0.0.0.0:3000->3000/tcp   grafana
yyyyyyyyyyyy   prom/prometheus:v2.51.0     0.0.0.0:9090->9090/tcp   prometheus
```

---

## Step 6 — Test the network connection from inside Grafana

This confirms Grafana can actually reach Prometheus:

```bash
docker exec grafana wget -qO- http://prometheus:9090/-/healthy
```

**Expected output:**
```
Prometheus Server is Healthy.
```

This works because `grafana` and `prometheus` are on the same `monitoring` network.
Docker DNS resolved `prometheus` to the container's internal IP.

---

## Step 7 — Open Grafana and verify the data source

1. Open **http://localhost:3000** and log in (`admin` / `admin`).
2. Go to **Connections → Data sources**.
3. You should see **Prometheus** already listed — the provisioning file registered it automatically.
4. Click on **Prometheus**, scroll down, and click **Save & test**.
5. You should see a green **"Successfully queried the Prometheus API"** message.

---

## Step 8 — View the pre-loaded dashboard

1. In the left sidebar, click **Dashboards**.
2. You should see a folder called **Provisioned** containing **Prometheus Overview**.
3. Click it — you should see live charts for scrape duration, memory, and samples ingested.

---

## Step 9 — Clean up

```bash
# Stop and remove both containers
docker stop grafana prometheus
docker rm grafana prometheus

# Remove the network
docker network rm monitoring

# (Optional) Remove volumes
docker volume rm promdata grafdata
```

---

**Next:** Read `02-docker-compose.md` to see how this entire multi-container setup
collapses into one file and one command.
