# Native Python Projects (04 & 05)

Two Python projects designed to run natively in WSL2 — no Docker required for the app itself. Each project can also be containerized if you prefer the Docker path.

| Project | What it does | Port |
|---------|-------------|------|
| [04-system-monitor](04-system-monitor/) | Reads `/proc` and exposes CPU, memory, disk I/O, load avg, uptime | 8084 |
| [05-url-health-checker](05-url-health-checker/) | Polls URLs every 30 s, tracks up/down and response time | 8085 |

---

## Which monitoring setup should I use?

| | Docker (`infra/`) | Native (`wsl-setup/`) |
|---|---|---|
| Projects 01–03 | Yes — designed for Docker | Works with extra steps |
| Projects 04–05 | Works (see CONNECT.md) | Yes — primary path |

If you have not set up Prometheus and Grafana yet, pick one path and stick with it:
- **Docker path** → `cd infra && docker compose up -d`, then follow `infra/README.md`
- **Native path** → follow `wsl-setup/01-install-prometheus.md` then `02-install-grafana.md`

---

## Quick start — Native WSL2

```bash
# Terminal 1 — Project 4
cd projects-native/04-system-monitor/app
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python app.py
```

```bash
# Terminal 2 — Project 5
cd projects-native/05-url-health-checker/app
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python app.py
```

Verify both are running:
```bash
curl http://localhost:8084/snapshot
curl http://localhost:8085/status
```

Then follow each project's `CONNECT.md` to wire them to Prometheus and Grafana.

---

## Quick start — Docker

```bash
# Ensure infra is running first
cd infra && docker compose up -d

# Start System Monitor
cd projects-native/04-system-monitor && docker compose up -d --build

# Start URL Health Checker
cd projects-native/05-url-health-checker && docker compose up -d --build
```

---

## Directory structure

```
projects-native/
├── 04-system-monitor/
│   ├── app/
│   │   ├── app.py            — Flask app reading /proc
│   │   ├── requirements.txt
│   │   └── Dockerfile        — for the Docker path
│   ├── docker-compose.yml    — Docker path only
│   ├── CONNECT.md            — wiring guide (both paths)
│   └── dashboards/
│       └── system-monitor.json
└── 05-url-health-checker/
    ├── app/
    │   ├── app.py            — Flask app polling URLs
    │   ├── requirements.txt
    │   └── Dockerfile
    ├── docker-compose.yml
    ├── CONNECT.md
    └── dashboards/
        └── url-health-checker.json
```
