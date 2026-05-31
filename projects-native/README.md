# Native Projects (04–07)

These projects run **natively** as local Python processes — no Docker.
They are scraped by the **native** Prometheus + Grafana you install in one of the
native setup directories: `wsl-setup/` (Windows + WSL2), `linux-setup/` (bare-metal /
VM Linux), or `mac-setup/` (macOS via Homebrew).

> Looking for the Docker track? Projects 01–03 in `../projects/` run in containers
> against the shared `infra/` stack.

---

## Which project runs where?

| Project | Port | macOS | Linux / WSL2 | How it reads metrics |
|---------|------|:-----:|:------------:|----------------------|
| 04 — System Monitor | 8084 | ✗ (no `/proc`) | ✓ | Raw `/proc` parsing |
| 05 — URL Health Checker | 8085 | ✓ | ✓ | HTTP polling |
| 06 — Mac System Monitor | 8086 | ✓ | (works, but use 07) | `psutil` library |
| 07 — Linux System Monitor | 8087 | (works, but use 06) | ✓ | `psutil` library |

Projects 06 and 07 share the **same `psutil`-based code** — that's the lesson: a portable
library runs unchanged across OSes. Project 04 is the contrast: raw `/proc` parsing that
only works on Linux. Run 04 and 07 side by side to compare the two approaches.

---

## Prerequisites

1. Complete the native setup directory for your OS so Prometheus and Grafana are installed
   and running as system processes:
   - **Windows + WSL2** → `../wsl-setup/` (`systemctl status prometheus grafana-server`)
   - **Linux** → `../linux-setup/` (`systemctl status prometheus grafana-server`)
   - **macOS** → `../mac-setup/` (`brew services list`)
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

### Project 6 — Mac System Monitor (port 8086, macOS)

```bash
cd projects-native/06-mac-system-monitor/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then follow `06-mac-system-monitor/CONNECT.md`.

### Project 7 — Linux System Monitor (port 8087, Linux)

```bash
cd projects-native/07-linux-system-monitor/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then follow `07-linux-system-monitor/CONNECT.md`.

---

## Directory layout

Every project has the same shape: `app/` (app.py + requirements.txt), `dashboards/`
(Grafana dashboard JSON), `README.md`, `CONNECT.md` (wiring guide), and `CLEANUP.md`
(return the machine to a clean state).

```
projects-native/
├── 04-system-monitor/          — Linux only · raw /proc · port 8084
├── 05-url-health-checker/      — any OS · HTTP polling · port 8085
├── 06-mac-system-monitor/      — macOS · psutil · port 8086
└── 07-linux-system-monitor/    — Linux · psutil · port 8087
```

---

## How they connect

```
  ┌──────────────────────────┐        scrape localhost:8084  system-monitor      (Linux)
  │  native Prometheus :9090  │◀───────  localhost:8085  url-health-checker  (any OS)
  │  (config: see below)      │◀───────  localhost:8086  mac-system-monitor  (macOS)
  └────────────┬─────────────┘◀───────  localhost:8087  linux-system-monitor(Linux)
               │ query
        ┌──────┴───────┐
        │ native Grafana│  :3000
        └──────────────┘
```

Edit the Prometheus config, add the project's job, then reload:
`curl -X POST http://localhost:9090/-/reload`.

The config path depends on how you installed Prometheus:
- **Linux / WSL2 native** → `/etc/prometheus/prometheus.yml`
- **macOS (Homebrew)** → `$(brew --prefix)/etc/prometheus.yml` (reload with
  `brew services restart prometheus` if started via `brew services`)
