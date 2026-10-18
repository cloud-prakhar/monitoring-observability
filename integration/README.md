# Integration — Prometheus + Grafana Together

> **Why this section matters:** Running each tool on its own is easy. The interesting
> (and often confusing) part is connecting them. This section explains *how* Grafana
> talks to Prometheus and *why* the naive approach (`localhost`) fails.

---

## How Grafana talks to Prometheus

When Grafana needs to display a graph, it sends a PromQL query to Prometheus's HTTP API.
The key question is: **what URL does Grafana use to reach Prometheus?**

### The wrong answer: `http://localhost:9090`

```mermaid
flowchart LR
    subgraph GC["❌ Grafana container — its own localhost"]
        G["Grafana"]:::graf -->|"http://localhost:9090"| X["nothing listening on :9090<br/>request fails ✗"]:::bad
    end
    subgraph PC["Prometheus container"]
        P["Prometheus :9090"]:::prom
    end
    style GC fill:#FFEBEE,stroke:#E53935,stroke-width:2px,color:#B71C1C
    classDef bad fill:#E53935,stroke:#B71C1C,color:#fff
    classDef graf fill:#F9A825,stroke:#C17900,color:#000
    classDef prom fill:#E6522C,stroke:#A33B1F,color:#fff
```

Each container has its own `localhost`. Grafana's `localhost` is the Grafana container itself,
and port 9090 does not exist inside the Grafana container, so the request fails.

### The right answer: `http://prometheus:9090`

```mermaid
flowchart LR
    subgraph NET["✅ Docker network: monitoring"]
        G["Grafana container"]:::graf -->|"http://prometheus:9090"| P["Prometheus container"]:::prom
        DNS{{"Docker built-in DNS<br/>prometheus → container IP"}}:::store
        G -.->|"resolve 'prometheus'"| DNS
    end
    style NET fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#1B5E20
    classDef graf fill:#F9A825,stroke:#C17900,color:#000
    classDef prom fill:#E6522C,stroke:#A33B1F,color:#fff
    classDef store fill:#00897B,stroke:#004D40,color:#fff
```

Both containers are on the same Docker network. Docker's built-in DNS resolves `prometheus` to
the Prometheus container's internal IP address, so the request succeeds.

**The rule:** When one container needs to talk to another, use the **service name** (or
container name) as the hostname — never `localhost`.

---

## Where do these networks come from?

You don't usually create Docker networks by hand — Compose creates one for you every time
you run `docker compose up`. Understanding *how it names them* explains the single most common
integration failure.

### Rule 1 — Compose always creates a network, named `<project>_<network>`

The **project name** defaults to the name of the directory the `docker-compose.yml` lives in.
So running `docker compose up` from `integration/` (whose compose file defines a network called
`monitoring`) produces a network named:

```mermaid
flowchart LR
    PJ["<b>integration</b><br/>the project name<br/>(the directory name)"]:::step
    NW["<b>monitoring</b><br/>the network name from<br/>the networks: block"]:::app
    R["<b>integration_monitoring</b><br/>the final network name"]:::good
    PJ -->|"prefix"| R
    NW -->|"_ suffix"| R
    classDef app fill:#1E88E5,stroke:#0D47A1,color:#fff
    classDef good fill:#43A047,stroke:#1B5E20,color:#fff
    classDef step fill:#5C6BC0,stroke:#283593,color:#fff
```

Every service with `networks: - monitoring` is attached to it, and Docker adds a DNS entry on
that network for each service name. That's what makes `http://prometheus:9090` resolvable.

### Rule 2 — No `networks:` block? You get a network called `<project>_default`

If a compose file *doesn't* define any network, Compose still creates one, named
`<project>_default`, and quietly attaches the services to it. A single-service file like
`prometheus-setup/docker-compose.yml` therefore gets its own private `prometheus-setup_default`
network — fine on its own, but isolated from everything else.

### Why running the two standalone stacks separately breaks

```bash
docker compose -f prometheus-setup/docker-compose.yml up   # → network: prometheus-setup_default
docker compose -f grafana-setup/docker-compose.yml   up   # → network: grafana-setup_default
```

```mermaid
flowchart LR
    subgraph A["🏝️ prometheus-setup_default"]
        P["Prometheus"]:::prom
    end
    subgraph B["🏝️ grafana-setup_default"]
        G["Grafana"]:::graf
    end
    G --x|"lookup prometheus ...<br/>server misbehaving"| P
    style A fill:#FBE9E7,stroke:#E6522C,stroke-width:2px,color:#A33B1F
    style B fill:#FFF8E1,stroke:#F9A825,stroke-width:2px,color:#7A5200
    classDef graf fill:#F9A825,stroke:#C17900,color:#000
    classDef prom fill:#E6522C,stroke:#A33B1F,color:#fff
```

Two separate islands — Grafana's DNS has no entry for `prometheus`.

Docker's DNS only resolves a name **within the same network**. Across two `_default` networks
there is no route, so the lookup of `prometheus` fails. (See
[../docs/troubleshooting.md → section 4](../docs/troubleshooting.md#4-grafana-cannot-reach-prometheus--the-localhost-trap).)

**This `integration/` setup fixes it by design:** its one compose file defines both services
*and* a shared `monitoring` network, so both land on `integration_monitoring` together:

```mermaid
flowchart LR
    subgraph NET["🌐 integration_monitoring"]
        G["Grafana"]:::graf -->|"prometheus:9090<br/>(resolved by Docker DNS)"| P["Prometheus"]:::prom
    end
    style NET fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px,stroke-dasharray:6 4,color:#0D47A1
    classDef graf fill:#F9A825,stroke:#C17900,color:#000
    classDef prom fill:#E6522C,stroke:#A33B1F,color:#fff
```

The takeaway: keep services that must talk to each other in **one compose file** (or on one
explicitly-shared network) — never start them from separate directories and expect them to
find each other.

---

## How it all fits together

```mermaid
sequenceDiagram
    actor U as 🖥️ Your browser
    participant G as Grafana :3000
    participant P as Prometheus :9090
    participant V as 💾 promdata volume
    rect rgba(230, 82, 44, 0.15)
    Note over P,V: Scrape flow — every 15s
    P->>P: scrape itself (:9090/metrics)
    P->>V: store time-series data
    end
    rect rgba(249, 168, 37, 0.20)
    Note over U,P: Query flow
    U->>G: HTTP request (open a dashboard)
    G->>P: PromQL query via the monitoring network
    P-->>G: query results
    G-->>U: rendered chart in your browser
    end
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

## Troubleshooting

**`Post "http://prometheus:9090/api/v1/query": ... lookup prometheus on 127.0.0.11:53:
server misbehaving`** — Grafana can't resolve the name `prometheus`. This almost always
means Grafana and Prometheus are on **different Docker networks** (e.g. you started them from
the standalone `../prometheus-setup/` and `../grafana-setup/` dirs, which each create their
own isolated network). Run both from *this* `integration/` directory instead so they share
one network:

```bash
docker compose -f ../prometheus-setup/docker-compose.yml down
docker compose -f ../grafana-setup/docker-compose.yml down
docker compose up -d           # from integration/

# verify both are on the same network and DNS works:
docker ps --format 'table {{.Names}}\t{{.Networks}}'
docker exec grafana wget -qO- http://prometheus:9090/-/healthy   # → Prometheus Server is Healthy.
```

Full write-up (including the `localhost` variant and a quick-patch alternative):
[../docs/troubleshooting.md → section 4](../docs/troubleshooting.md#4-grafana-cannot-reach-prometheus--the-localhost-trap).

---

## After completing this section

**First stop this stack** — it uses the container names `prometheus` and `grafana`, the same
names `infra/` uses, so leaving it running makes the `infra/` start fail with
`Conflict. The container name "/prometheus" is already in use`:

```bash
docker compose down          # from integration/
```

Then head to **[../infra/](../infra/)** to start the shared monitoring stack, then pick a
project from `projects/` (Docker path) or `projects-native/` (native WSL2 path) to build real
applications that expose custom metrics and dashboards.
