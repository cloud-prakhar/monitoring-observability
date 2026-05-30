# Install Prometheus Natively on WSL2

Prometheus is distributed as a single binary. There is no package manager step — you download, extract, configure, and run it.

---

## Step 1 — Check your architecture

```bash
uname -m
```

Expected output:
```
x86_64
```

If you see `aarch64` (ARM), replace `linux-amd64` with `linux-arm64` in the download URL below.

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

> **Note (Prometheus 3.x):** Starting with Prometheus 3.0, the web console templates
> (`consoles/` and `console_libraries/`) are **no longer bundled** in the tarball. The
> redesigned built-in UI replaces them, so you no longer copy those directories or pass
> the `--web.console.*` flags. If you are following an older 2.x guide, ignore those steps.

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

## Step 4 — Create config directories

```bash
sudo mkdir -p /etc/prometheus /var/lib/prometheus
```

> On Prometheus 2.x you also copied `consoles/` and `console_libraries/` here. Prometheus
> 3.x no longer ships them, so there is nothing to copy — the directories above are all you need.

---

## Step 5 — Create the Prometheus configuration file

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
  # Project 4 — System Monitor (port 8084)
  # Uncomment after starting the app: python projects-native/04-system-monitor/app/app.py
  # ---------------------------------------------------------------------------
  # - job_name: "system-monitor"
  #   static_configs:
  #     - targets: ["localhost:8084"]

  # ---------------------------------------------------------------------------
  # Project 5 — URL Health Checker (port 8085)
  # Uncomment after starting the app: python projects-native/05-url-health-checker/app/app.py
  # ---------------------------------------------------------------------------
  # - job_name: "url-health-checker"
  #   static_configs:
  #     - targets: ["localhost:8085"]

EOF
```

Verify the file was written:
```bash
cat /etc/prometheus/prometheus.yml
```

---

## Step 6 — Run Prometheus (manual test first)

Before setting up a service, run it in the foreground to make sure it starts correctly:

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

## Step 7 — Check if systemd is available in your WSL2

WSL2 on Windows 11 (build 22621+) ships with systemd enabled by default. Older installs do not.

```bash
ps --no-headers -o comm 1
```

- Output is `systemd` → proceed to **Step 8a** (systemd service)
- Output is `init` → skip to **Step 8b** (run manually)

---

## Step 8a — Create a systemd service (recommended if systemd is available)

Create a dedicated system user for Prometheus:
```bash
sudo useradd --no-create-home --shell /bin/false prometheus
sudo chown -R prometheus:prometheus /var/lib/prometheus /etc/prometheus
```

Create the service unit file:
```bash
sudo tee /etc/systemd/system/prometheus.service > /dev/null << 'EOF'
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
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

## Step 8b — Run manually (if systemd is not available)

Run Prometheus in the background with `nohup`:

```bash
nohup prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --web.enable-lifecycle \
  > /var/log/prometheus.log 2>&1 &

echo "Prometheus PID: $!"
```

To stop it later:
```bash
kill $(pgrep prometheus)
```

> **Note:** With `nohup`, the process stops when you close the WSL2 terminal session. Run it again in a new session if needed.

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

---

## Troubleshooting

**`prometheus: command not found`**
The binary was not moved to `/usr/local/bin`. Re-run Step 3.

**Permission denied on `/var/lib/prometheus`**
```bash
sudo chown -R $(whoami):$(whoami) /var/lib/prometheus
```

**Port 9090 already in use**
```bash
sudo ss -tlnp | grep 9090
```
Kill the process using that port or change the Prometheus port with `--web.listen-address=":9091"`.

**Config reload returns 403**
The `--web.enable-lifecycle` flag is not in the startup command. Check the service file or the manual command and add it.

**Prometheus 3.x fails to start with `opening console templates ... no such file or directory`**
You are passing `--web.console.templates` / `--web.console.libraries` flags left over from a
Prometheus 2.x guide. Version 3.x no longer ships those directories, so the flags point at
nothing and startup aborts. Remove both flags from your startup command or systemd unit (this
guide already omits them).
