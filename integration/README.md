# Integration — Prometheus + Grafana Together

> **Why this section matters:** Running each tool on its own is easy. The interesting
> (and often confusing) part is connecting them. This section explains *how* Grafana
> talks to Prometheus and *why* the naive approach (`localhost`) fails.

---

## How Grafana talks to Prometheus

When Grafana needs to display a graph, it sends a PromQL query to Prometheus's HTTP API.
The key question is: **what URL does Grafana use to reach Prometheus?**

### The wrong answer: `http://localhost:9090`

```
❌ Wrong:

  ┌──────────────┐           ┌──────────────┐
  │   Grafana    │──localhost─│  Prometheus  │
  │  container   │    :9090   │  container   │
  └──────────────┘     ✗     └──────────────┘

  Each container has its own localhost.
  Grafana's localhost = the Grafana container itself.
  Port 9090 does not exist inside the Grafana container.
  Request fails.
```

### The right answer: `http://prometheus:9090`

```
✅ Correct:

  ┌────────────────────────────────────────────────────┐
  │              Docker network: monitoring            │
  │                                                    │
  │  ┌──────────────┐   prometheus:9090  ┌──────────┐ │
  │  │   Grafana    │ ─────────────────▶ │Prometheus│ │
  │  │  container   │                    │container │ │
  │  └──────────────┘                    └──────────┘ │
  │                                                    │
  └────────────────────────────────────────────────────┘

  Both containers are on the same Docker network.
  Docker's built-in DNS resolves "prometheus" to the
  Prometheus container's internal IP address.
  Request succeeds.
```

**The rule:** When one container needs to talk to another, use the **service name** (or
container name) as the hostname — never `localhost`.

---

## How it all fits together

```
Scrape flow:
  Prometheus ──scrapes──▶ itself (:9090/metrics) every 15s
  Prometheus ──stores──▶  time-series data in promdata volume

Query flow:
  Your browser ──HTTP──▶ Grafana (:3000)
  Grafana ──PromQL──▶ Prometheus (:9090) via monitoring network
  Grafana ──renders──▶ chart in your browser
```

---

## What you will build

Prometheus and Grafana running together, auto-configured via provisioning:
- Prometheus registered as a Grafana data source automatically (no manual clicks)
- A starter "Prometheus Overview" dashboard loaded automatically

---

## Prerequisites

- Completed `../prometheus-setup/` and `../grafana-setup/`
- No containers named `prometheus` or `grafana` are running
- You are in the `integration/` directory

---

## Learning path (do these in order)

### Step 1 — The manual way
Read and follow **[01-docker-cli.md](01-docker-cli.md)**.

You will create a Docker network by hand, run both containers on it, test the connection
from inside the Grafana container, and verify the pre-loaded dashboard.

### Step 2 — The Compose shortcut
Read and follow **[02-docker-compose.md](02-docker-compose.md)**.

You will see how the network, volumes, services, and `depends_on` map back to the manual
commands, and start the entire stack with `docker compose up -d`.

---

## Files in this directory

| Path | Purpose |
|------|---------|
| `prometheus.yml` | Prometheus config (same structure, with Grafana scrape commented out) |
| `grafana/provisioning/datasources/prometheus.yml` | Auto-registers Prometheus as Grafana data source |
| `grafana/provisioning/dashboards/dashboard.yml` | Tells Grafana where to load dashboard JSON files |
| `grafana/dashboards/prometheus-overview.json` | Pre-built starter dashboard |
| `01-docker-cli.md` | Manual walkthrough |
| `docker-compose.yml` | Compose file (both services + network) |
| `02-docker-compose.md` | Compose walkthrough + mapping table |

---

## Key concepts introduced here

| Concept | One-line definition |
|---------|-------------------|
| Docker network | A virtual bridge that lets containers reach each other by name |
| Service name DNS | Docker resolves container/service names to IPs on the same network |
| Provisioning | Grafana auto-loading data sources and dashboards from config files on startup |
| `depends_on` | Compose start-order hint (does not guarantee readiness) |
| `--network` flag | Attaches a container to a named network |

---

## Quick reference

| Service | Port | URL |
|---------|------|-----|
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |

**Grafana login:** `admin` / `admin`

---

## After completing this section

Head to **[../infra/](../infra/)** to start the shared monitoring stack, then pick a project
from `projects/` (Docker path) or `projects-native/` (native WSL2 path) to build real
applications that expose custom metrics and dashboards.
