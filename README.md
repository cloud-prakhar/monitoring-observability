# Prometheus + Grafana — Local Learning Lab

A hands-on repository for learning how to set up, integrate, and use Prometheus
and Grafana locally. Everything runs on your machine — no cloud accounts, no subscriptions.

Two setup paths are available: **Docker** (quickest start) or **Native WSL2** (more control,
closer to how production systems work). Pick one and follow it consistently.

---

## Repository structure

```
.
├── docs/
│   ├── wsl-setup.md            # Windows: WSL2 + Docker Desktop one-time setup
│   └── troubleshooting.md      # Error messages and fix commands
│
├── prometheus-setup/           # Learn Prometheus standalone (no Grafana yet)
├── grafana-setup/              # Learn Grafana standalone (no Prometheus yet)
├── integration/                # Wire the two together — explains the networking concepts
│
├── wsl-setup/                  # Native install: Prometheus + Grafana binaries on WSL2
│   ├── 01-install-prometheus.md
│   ├── 02-install-grafana.md
│   └── 03-wire-together.md
│
├── infra/                      # Shared Docker infra for projects 01–03
│
├── projects/                   # Docker projects (use infra/ as monitoring backend)
│   ├── 01-flask-web-api/       # Flask REST API — request rate, latency, error rate
│   ├── 02-job-processor/       # Background job queue — queue depth, throughput, failures
│   └── 03-cache-service/       # In-memory cache — hit rate, key count, TTL evictions
│
└── projects-native/            # Native-only projects (run with python app.py)
    ├── 04-system-monitor/      # Reads /proc — CPU, memory, disk I/O, load average
    └── 05-url-health-checker/  # Polls URLs — availability and response time
```

---

## Choose your monitoring setup

### Path A — Docker (recommended for beginners)

Prometheus and Grafana run in containers managed by `infra/`. Projects join a shared Docker network.

**Prerequisites:** Docker Desktop installed. On Windows, complete `docs/wsl-setup.md` first.

```bash
docker run hello-world   # verify Docker works
docker compose version   # verify Compose v2
```

### Path B — Native WSL2 (no Docker for Prometheus/Grafana)

Prometheus and Grafana run as system processes inside WSL2. Projects run with `python app.py`.

**Prerequisites:** WSL2 with Ubuntu 22.04+. No Docker required for the monitoring layer.

```bash
wsl --version            # verify WSL2 is installed
lsb_release -a           # verify Ubuntu version
```

Follow `wsl-setup/` to install Prometheus and Grafana natively, then use `projects-native/`.

---

## Recommended learning order

### Docker path

```
1. docs/wsl-setup.md              ← Windows only: WSL2 + Docker Desktop

2. prometheus-setup/              ← run Prometheus by hand, then with Compose
3. grafana-setup/                 ← first login, manual data source
4. integration/                   ← understand why container networking needs a shared network

5. infra/README.md                ← start the shared monitoring stack

6. projects/01-flask-web-api/CONNECT.md   ← HTTP metrics, first dashboard
7. projects/02-job-processor/CONNECT.md   ← queue + async metrics, histograms
8. projects/03-cache-service/CONNECT.md   ← hit ratio, gauges, TTL evictions
```

### Native WSL2 path

```
1. wsl-setup/01-install-prometheus.md  ← binary install, systemd service
2. wsl-setup/02-install-grafana.md     ← apt install, start server
3. wsl-setup/03-wire-together.md       ← add datasource, first query

4. projects-native/04-system-monitor/CONNECT.md    ← /proc metrics
5. projects-native/05-url-health-checker/CONNECT.md ← availability monitoring
```

Projects 04–05 are native-only — they run as local Python processes scraped by the
native Prometheus. Projects 01–03 are the Docker track.

In each `prometheus-setup/` and `grafana-setup/` directory, do `01-docker-cli.md` before
`02-docker-compose.md` — the manual commands make the Compose file meaningful instead of magic.

---

## Quick start — Docker path (projects 01–03)

```bash
# 1. Start the shared monitoring infrastructure
cd infra && docker compose up -d && cd ..

# 2. Start all three projects
cd projects/01-flask-web-api && docker compose up -d --build && cd ../..
cd projects/02-job-processor  && docker compose up -d --build && cd ../..
cd projects/03-cache-service  && docker compose up -d --build && cd ../..

# 3. Uncomment all three jobs in infra/prometheus.yml, then reload
curl -X POST http://localhost:9090/-/reload

# 4. Open Grafana
#    http://localhost:3000  (admin / admin)
#    Dashboards → Projects → All Projects Overview
```

## Quick start — Native WSL2 path (projects 04–05)

```bash
# 1. Follow wsl-setup/ to install Prometheus and Grafana natively (one-time)

# 2. Start Project 4
cd projects-native/04-system-monitor/app
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python app.py &

# 3. Start Project 5
cd ../../05-url-health-checker/app
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python app.py &

# 4. Uncomment their jobs in /etc/prometheus/prometheus.yml, then reload
curl -X POST http://localhost:9090/-/reload

# 5. Open Grafana at http://localhost:3000 → import the dashboard JSONs
```

---

## How the projects connect to infra

```
  infra/docker-compose.yml creates:
  ┌────────────────────────────────────────────────────────┐
  │  Docker network: "monitoring"  (name: monitoring)      │
  │                                                        │
  │  ┌────────────┐    scrape    ┌──────────────────────┐  │
  │  │ Prometheus │◀────────────│ flask-web-api  :8081  │  │
  │  │   :9090    │◀────────────│ job-processor  :8082  │  │
  │  └────────────┘◀────────────│ cache-service  :8083  │  │
  │        ▲                    └──────────────────────┘  │
  │        │ query                                        │
  │  ┌─────┴──────┐                                       │
  │  │  Grafana   │                                       │
  │  │   :3000    │                                       │
  │  └────────────┘                                       │
  └────────────────────────────────────────────────────────┘

  Each project's docker-compose.yml joins with:
    networks:
      monitoring:
        external: true
```

The `name: monitoring` line in `infra/docker-compose.yml` is what makes this work.
Without it, the network would be called `infra_monitoring` and the `external: true`
reference in each project would fail to find it.

---

## Ports at a glance

| Service | Port | URL | Setup |
|---------|------|-----|-------|
| Prometheus | 9090 | http://localhost:9090 | Docker (`infra/`) or Native (`wsl-setup/`) |
| Grafana | 3000 | http://localhost:3000 | Docker (`infra/`) or Native (`wsl-setup/`) |
| Flask Web API | 8081 | http://localhost:8081 | Docker (`projects/01-flask-web-api/`) |
| Job Processor | 8082 | http://localhost:8082 | Docker (`projects/02-job-processor/`) |
| Cache Service | 8083 | http://localhost:8083 | Docker (`projects/03-cache-service/`) |
| System Monitor | 8084 | http://localhost:8084 | Native (`projects-native/04-system-monitor/`) |
| URL Health Checker | 8085 | http://localhost:8085 | Native (`projects-native/05-url-health-checker/`) |

**Grafana login:** `admin` / `admin`

---

## Grafana dashboards

| Dashboard | UID | Location | Shows |
|-----------|-----|----------|-------|
| All Projects Overview | `all-projects-overview` | auto-loaded (infra Docker path) | All 3 Docker projects on one screen |
| Flask Web API | `flask-web-api` | `projects/01-flask-web-api/dashboards/` | Request rate, error rate, latency |
| Job Processor | `job-processor` | `projects/02-job-processor/dashboards/` | Queue depth, throughput, failures |
| Cache Service | `cache-service` | `projects/03-cache-service/dashboards/` | Hit rate, key count, evictions |
| System Monitor | `system-monitor` | `projects-native/04-system-monitor/dashboards/` | CPU, memory, disk, load avg |
| URL Health Checker | `url-health-checker` | `projects-native/05-url-health-checker/dashboards/` | Availability, response time |

To import a dashboard: Grafana → Dashboards → New → Import → upload the JSON file.

---

## Key concepts at a glance

| Term | One-line definition |
|------|-------------------|
| **Prometheus** | Pulls metrics from your services every 15s and stores them as time-series |
| **Grafana** | Queries Prometheus and renders charts and dashboards |
| **Scraping** | Prometheus fetching the `/metrics` endpoint of a target |
| **Counter** | A metric that only goes up — use `rate()` to get a per-second rate |
| **Gauge** | A metric that goes up and down — queue depth, active connections, key count |
| **Histogram** | Tracks value distribution across buckets — use `histogram_quantile()` for percentiles |
| **PromQL** | Prometheus Query Language — the query syntax used in dashboards |
| **Docker network** | Virtual bridge allowing containers to reach each other by service name |
| **external: true** | Joins a Docker network that already exists (created by another Compose project) |
| **Provisioning** | Grafana loading data sources and dashboards from config files on startup |

---

## Troubleshooting

See **[docs/troubleshooting.md](docs/troubleshooting.md)** — covers every common error
with exact error messages and specific fix commands.

Quick reference:
- Container won't start → `docker logs <name>`
- Grafana can't reach Prometheus → use `http://prometheus:9090`, not `localhost:9090`
- Target shows DOWN → check it's on the `monitoring` network
- `external network monitoring not found` → start `infra/` first
- Full reset → `docker compose down -v` in each directory
