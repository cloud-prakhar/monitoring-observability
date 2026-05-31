# Install Prometheus Natively on Linux

Prometheus ships as a single static binary — no package manager needed. You download, extract,
configure, and run it under a dedicated systemd service.

---

## Step 1 — Check your architecture

```bash
uname -m
```

Expected output:
```
x86_64
```

If you see `aarch64` (ARM — common on AWS Graviton, Raspberry Pi, etc.), replace
`linux-amd64` with `linux-arm64` in the download URL below.

---

## Step 2 — Download and extract Prometheus

```bash
PROM_VERSION="3.12.0"

cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz
```

Expected output (last few lines):
```
Saving to: 'prometheus-3.12.0.linux-amd64.tar.gz'
prometheus-3.12.0.linux-amd64.tar.gz   100%[====================================>]  145.70M  ...
```

Extract it:
```bash
tar xzf prometheus-${PROM_VERSION}.linux-amd64.tar.gz
cd prometheus-${PROM_VERSION}.linux-amd64
ls
```

Expected output:
```
LICENSE  NOTICE  prometheus  prometheus.yml  promtool
```

> **Note (Prometheus 3.x):** version 3.0 removed the bundled web console templates
> (`consoles/` and `console_libraries/`). The redesigned built-in UI replaces them, so you no
> longer copy those directories or pass the `--web.console.*` flags. If you are following an
> older 2.x guide, ignore those steps — the flags crash 3.x on startup.

---

## Step 3 — Install the binaries

```bash
sudo mv prometheus promtool /usr/local/bin/
```

Verify:
```bash
prometheus --version
```

Expected output:
```
prometheus, version 3.12.0 (branch: HEAD, ...)
```

---

## Step 4 — Create config and data directories

```bash
sudo mkdir -p /etc/prometheus /var/lib/prometheus
```

**Why these two directories?** They follow the standard Linux split between *config* and *state*:

- `/etc/prometheus` — holds the configuration file (`prometheus.yml`). `/etc` is the conventional
  home for system-wide config, so this is where Prometheus expects to look.
- `/var/lib/prometheus` — holds the time-series database (the metrics Prometheus collects).
  `/var/lib` is the conventional home for application *data that changes at runtime*, so keeping
  data here (separate from config) means you can wipe metrics without touching your config.

Because we created them with `sudo`, both directories are currently owned by `root`. The manual
test in Step 6 runs Prometheus as **your** user, which needs to write to the data directory — so
give yourself ownership for now (Step 8 hands it to a dedicated service user later):

```bash
sudo chown -R $(whoami):$(whoami) /etc/prometheus /var/lib/prometheus
```

> Without this `chown`, Step 6 fails with `permission denied` the moment Prometheus tries to
> create its database under `/var/lib/prometheus`.

---

## Step 5 — Create the Prometheus configuration file

This config scrapes Prometheus itself and has commented-out blocks for the native Linux projects
(04, 05, and 07). Commented jobs do nothing until you uncomment them.

```bash
sudo tee /etc/prometheus/prometheus.yml > /dev/null << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:

  # Prometheus scrapes itself — always on.
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # ---------------------------------------------------------------------------
  # Project 4 — System Monitor (port 8084) — reads /proc directly
  # Uncomment after starting: python projects-native/04-system-monitor/app/app.py
  # ---------------------------------------------------------------------------
  # - job_name: "system-monitor"
  #   static_configs:
  #     - targets: ["localhost:8084"]

  # ---------------------------------------------------------------------------
  # Project 5 — URL Health Checker (port 8085)
  # Uncomment after starting: python projects-native/05-url-health-checker/app/app.py
  # ---------------------------------------------------------------------------
  # - job_name: "url-health-checker"
  #   static_configs:
  #     - targets: ["localhost:8085"]

  # ---------------------------------------------------------------------------
  # Project 7 — Linux System Monitor (port 8087) — the psutil alternative to Project 4
  # Uncomment after starting: python projects-native/07-linux-system-monitor/app/app.py
  # ---------------------------------------------------------------------------
  # - job_name: "linux-system-monitor"
  #   static_configs:
  #     - targets: ["localhost:8087"]

EOF
```

Verify the file was written:
```bash
cat /etc/prometheus/prometheus.yml
```

---

## Step 6 — Run Prometheus (manual test first)

Before setting up the service, run it in the foreground to make sure it starts correctly. The
`--web.enable-lifecycle` flag turns on the `POST /-/reload` endpoint used later:

```bash
prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --web.enable-lifecycle
```

Expected output (last few lines):
```
ts=... level=info msg="Server is ready to receive web requests."
```

Open **http://localhost:9090** in your browser. You should see the Prometheus UI.
Go to **http://localhost:9090/targets** — the `prometheus` job should show **UP**.

Press `Ctrl+C` to stop it once you have confirmed it works.

---

## Step 7 — Create a dedicated service user

**Why a dedicated `prometheus` user?** This is the *principle of least privilege*. If Prometheus
ran as `root` and was ever compromised (or simply had a bug), it could read or modify anything on
the system. A locked-down account limits the blast radius to only Prometheus' own files. The flags
make that account safe:

- `--no-create-home` — Prometheus never needs a home directory, so don't make one.
- `--shell /bin/false` — nobody can log in as this user; it exists only to run the process.

```bash
sudo useradd --no-create-home --shell /bin/false prometheus
```

Now hand ownership of the config and data directories to that user, so the service (which runs
**as** `prometheus`) can read its config and write its database:

```bash
sudo chown -R prometheus:prometheus /var/lib/prometheus /etc/prometheus
```

---

## Step 8 — Create the systemd service

**Why a systemd service at all?** Running Prometheus by hand (Step 6) stops the moment you close
the terminal or reboot. A systemd service fixes that: it starts Prometheus automatically on boot,
restarts it if it crashes (`Restart=on-failure`), runs it in the background, and gives you one
consistent way to start/stop/inspect it (`systemctl start|stop|status prometheus`).

```bash
sudo tee /etc/systemd/system/prometheus.service > /dev/null << 'EOF'
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --web.enable-lifecycle
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
```

**Why `enable` *and* `start`?** `enable` registers the service to launch automatically on every
boot; `start` launches it right now in this session. Running both means Prometheus is up immediately
and stays up after future reboots.

Check status:
```bash
sudo systemctl status prometheus
```

Expected output:
```
● prometheus.service - Prometheus
     Loaded: loaded (/etc/systemd/system/prometheus.service; enabled; ...)
     Active: active (running) since ...
```

---

## Step 9 — Verify

```bash
curl -s http://localhost:9090/-/healthy
```

Expected output:
```
Prometheus Server is Healthy.
```

```bash
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep -A2 '"job"'
```

You should see the `prometheus` job with `"health": "up"`.

---

## Reload config without restarting

After editing `/etc/prometheus/prometheus.yml` (for example, to uncomment a project's scrape job):

```bash
curl -X POST http://localhost:9090/-/reload
```

Expected: HTTP 200 (empty body). The `--web.enable-lifecycle` flag set above enables this endpoint.
If you prefer, `sudo systemctl restart prometheus` also reloads the config.

---

## Troubleshooting

**`prometheus: command not found`**
The binary was not moved to `/usr/local/bin`. Re-run Step 3. (Confirm `/usr/local/bin` is on your
`PATH`.)

**Permission denied on `/var/lib/prometheus`**
The directory is still owned by root or another user. Re-run the `chown` from Step 7.

**Port 9090 already in use**
```bash
sudo ss -tlnp | grep 9090
```
Kill the process using that port, or change the Prometheus port with `--web.listen-address=":9091"`.

**Config reload returns 403**
The `--web.enable-lifecycle` flag is missing from the service file. Add it to `ExecStart`, then
`sudo systemctl daemon-reload && sudo systemctl restart prometheus`.

**Prometheus 3.x fails to start with `opening console templates ... no such file or directory`**
You are passing `--web.console.templates` / `--web.console.libraries` flags from a 2.x guide.
Version 3.x no longer ships those directories. Remove both flags (this guide already omits them).
