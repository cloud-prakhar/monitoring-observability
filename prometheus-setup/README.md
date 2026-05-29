# Prometheus Setup — Standalone

> **What is Prometheus?**
> Prometheus is an open-source monitoring tool that *pulls* (scrapes) metrics from your
> services at regular intervals and stores them as time-series data. Think of it as a
> database designed specifically for numbers that change over time — CPU usage,
> request counts, error rates. You query this data with a language called PromQL.

> **Why monitoring?**
> Without metrics, you are flying blind. When something goes wrong in production, metrics
> tell you *what* broke and *when* — often before your users notice.

---

## What you will build

A standalone Prometheus instance running locally at **http://localhost:9090**, scraping
its own metrics as a first target.

```
Your browser
     |
     | http://localhost:9090
     v
+------------------+
|   Prometheus     |  <-- scrapes itself at /metrics every 15s
|   container      |
|   port 9090      |
+------------------+
         |
         v
  [promdata volume]   <-- time-series database persisted here
```

---

## Prerequisites

- Docker Desktop installed and running
- If you are on Windows, complete `../docs/wsl-setup.md` first
- You are working from a terminal inside the `prometheus-setup/` directory

**Verify Docker is working:**
```bash
docker run hello-world
```
You should see `Hello from Docker!`.

---

## Learning path (do these in order)

### Step 1 — The manual way
Read and follow **[01-docker-cli.md](01-docker-cli.md)**.

You will run Prometheus by hand using `docker run`, understand every flag, open the
Prometheus UI, and run your first PromQL query.

**Do not skip this.** Understanding the manual commands makes the Compose file meaningful
instead of magic.

### Step 2 — The Compose shortcut
Read and follow **[02-docker-compose.md](02-docker-compose.md)**.

You will see a side-by-side mapping of every `docker run` flag to its Compose equivalent,
then start the same Prometheus with a single `docker compose up -d`.

---

## Files in this directory

| File | Purpose |
|------|---------|
| `prometheus.yml` | Prometheus config — scrape interval and targets, heavily commented |
| `01-docker-cli.md` | Manual Docker commands walkthrough |
| `docker-compose.yml` | Compose file (Prometheus only) |
| `02-docker-compose.md` | Compose walkthrough + mapping table back to step 01 |

---

## Key concepts introduced here

| Concept | One-line definition |
|---------|-------------------|
| Scraping | Prometheus fetching metrics from a target's `/metrics` endpoint |
| `scrape_interval` | How often Prometheus collects metrics |
| `job_name` | A label grouping targets of the same type |
| Named volume | Docker-managed storage that survives container restarts |
| PromQL | Prometheus Query Language — used to query the metrics database |
| `up` metric | Built-in: 1 if target is reachable, 0 if not |

---

## Quick reference — ports

| Service | Port | URL |
|---------|------|-----|
| Prometheus UI | 9090 | http://localhost:9090 |
| Prometheus metrics | 9090 | http://localhost:9090/metrics |

---

## After completing this section

Head to **[../grafana-setup/](../grafana-setup/)** to set up Grafana on its own,
then combine both in **[../integration/](../integration/)**.
