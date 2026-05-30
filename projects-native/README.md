# Native Projects (04–05)

These projects run **natively in WSL2** as local Python processes — no Docker.
They are scraped by the **native** Prometheus + Grafana you install in `wsl-setup/`.

> Looking for the Docker track? Projects 01–03 in `../projects/` run in containers
> against the shared `infra/` stack.

---

## Prerequisites

1. Complete `../wsl-setup/` so Prometheus and Grafana are installed and running as
   system processes (`systemctl status prometheus grafana-server`).
2. Have Python 3.12+ available (`python3 --version`).

---

## Quick start

Each project follows the same pattern: create a venv, install deps, run `python app.py`,
then wire it into Prometheus by editing `/etc/prometheus/prometheus.yml`.

### Project 4 — System Monitor (port 8084)

```bash
cd projects-native/04-system-monitor/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then follow `04-system-monitor/CONNECT.md` to add the scrape job and import the dashboard.

### Project 5 — URL Health Checker (port 8085)

```bash
cd projects-native/05-url-health-checker/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then follow `05-url-health-checker/CONNECT.md`.

---

## Directory layout

```
projects-native/
├── 04-system-monitor/
│   ├── app/                  — app.py + requirements.txt
│   ├── dashboards/           — Grafana dashboard JSON
│   ├── README.md             — what it does, metrics produced
│   ├── CONNECT.md            — wiring guide (native WSL2)
│   └── CLEANUP.md            — return machine to a clean state
└── 05-url-health-checker/
    ├── app/
    ├── dashboards/
    ├── README.md
    ├── CONNECT.md
    └── CLEANUP.md
```

---

## How they connect

```
  ┌──────────────────────────┐        scrape localhost:8084
  │  native Prometheus :9090  │◀───────  system-monitor (python app.py)
  │  (/etc/prometheus/...)    │◀───────  url-health-checker (python app.py)
  └────────────┬─────────────┘        scrape localhost:8085
               │ query
        ┌──────┴───────┐
        │ native Grafana│  :3000
        └──────────────┘
```

Edit `/etc/prometheus/prometheus.yml`, add the project's job, then reload:
`curl -X POST http://localhost:9090/-/reload`.
