# Grafana Setup — Standalone

> **What is Grafana?**
> Grafana is an open-source visualization tool that turns numbers into charts and
> dashboards. It does not store data itself — instead, it connects to a *data source*
> (like Prometheus) and queries it on demand. Think of Prometheus as the database and
> Grafana as the reporting layer on top of it.

> **Why dashboards?**
> Raw numbers in a database are hard to reason about. A dashboard with a time-series
> graph of your request rate makes trends, spikes, and anomalies obvious at a glance.

---

## What you will build

A standalone Grafana instance running locally at **http://localhost:3000**. You will log
in, explore the UI, and learn how to add a data source manually — preparation for
wiring Grafana to Prometheus in the next section.

```
Your browser
     |
     | http://localhost:3000
     v
+------------------+
|   Grafana        |
|   container      |
|   port 3000      |
+------------------+
         |
         v
  [grafdata volume]   <-- dashboards, users, settings stored here
```

---

## Prerequisites

- Docker Desktop installed and running
- If you are on Windows, complete `../docs/wsl-setup.md` first
- You are working from a terminal inside the `grafana-setup/` directory

---

## Learning path (do these in order)

### Step 1 — The manual way
Read and follow **[01-docker-cli.md](01-docker-cli.md)**.

You will run Grafana by hand, log in for the first time, change your password, and
explore the UI including the data sources screen.

### Step 2 — The Compose shortcut
Read and follow **[02-docker-compose.md](02-docker-compose.md)**.

Side-by-side mapping from `docker run` flags to Compose keys, plus `up`, `ps`, `logs`,
`down`, and `down -v` explained.

---

## Files in this directory

| File | Purpose |
|------|---------|
| `01-docker-cli.md` | Manual Docker commands walkthrough |
| `docker-compose.yml` | Compose file (Grafana only) |
| `02-docker-compose.md` | Compose walkthrough + mapping table |
| `provisioning/` | (Used in integration/) Auto-config for data sources + dashboards |

---

## Key concepts introduced here

| Concept | One-line definition |
|---------|-------------------|
| Data source | A connection Grafana uses to fetch data (e.g. Prometheus) |
| Dashboard | A collection of panels arranged on a page |
| Panel | A single chart or stat display within a dashboard |
| Named volume | Docker-managed storage, avoids permission issues with UID 472 |
| GF_* env vars | Grafana configuration via environment variables |

---

## Quick reference — ports

| Service | Port | URL |
|---------|------|-----|
| Grafana UI | 3000 | http://localhost:3000 |

**Default login:** `admin` / `admin` (change on first login)

---

## After completing this section

Head to **[../integration/](../integration/)** to connect Grafana to Prometheus and
see real metrics on a dashboard.
