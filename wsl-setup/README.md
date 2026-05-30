# Native Prometheus + Grafana on WSL2

This directory installs Prometheus and Grafana **directly inside WSL2** as system processes — no Docker required. This gives you full control over the binaries, config files, and service lifecycle.

---

## Docker vs Native — pick your path

| | Docker (`infra/`) | Native (this directory) |
|---|---|---|
| **Setup time** | ~2 min | ~10 min |
| **Restart after reboot** | `docker compose up -d` | systemctl or manual command |
| **Config file location** | `infra/prometheus.yml` | `/etc/prometheus/prometheus.yml` |
| **Grafana data** | Docker named volume | `/var/lib/grafana/` |
| **Good for** | Quick start, projects 01–03 | Learning the binary, projects 04–05, production-like setup |
| **Scrape target syntax** | `container-name:port` | `localhost:port` |

Both paths end up with the same result: Prometheus on port 9090, Grafana on port 3000.

---

## Setup order

1. **[Install Prometheus](01-install-prometheus.md)** — download binary, configure, run as a service
2. **[Install Grafana](02-install-grafana.md)** — install via apt, start the server
3. **[Wire them together](03-wire-together.md)** — add Prometheus as a Grafana data source

Once done, follow `projects-native/04-system-monitor/CONNECT.md` and
`projects-native/05-url-health-checker/CONNECT.md` to connect the Python projects.

When you're finished and want your machine back to a clean state, run
**[04-cleanup.md](04-cleanup.md)** — it fully uninstalls both services, users, binaries, config,
and data.

---

## Prerequisites

- WSL2 with Ubuntu 22.04 or 24.04 (run `lsb_release -a` to check)
- At least 512 MB free RAM
- Internet access for the first download/install

These instructions assume the `x86_64` (Intel/AMD) architecture, which is standard for WSL2 on Windows.
