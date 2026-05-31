# Install Prometheus Natively on macOS

On macOS the easiest native install is via Homebrew, which downloads the Prometheus binary,
drops a default config in place, and registers a launchd service you can manage with
`brew services`.

---

## Step 1 — Find your Homebrew prefix

```bash
brew --prefix
```

Expected output:
```
/opt/homebrew      # Apple Silicon (M1/M2/M3/M4)
```
or
```
/usr/local         # Intel Macs
```

Every path below uses `$(brew --prefix)` so it works on both. To save typing, set a shortcut
for this session:

```bash
BREW="$(brew --prefix)"
echo "Homebrew prefix: $BREW"
```

---

## Step 2 — Install Prometheus

```bash
brew install prometheus
```

Expected output (last few lines):
```
==> Pouring prometheus--3.12.0...
🍺  /opt/homebrew/Cellar/prometheus/3.12.0: ...
```

Verify:
```bash
prometheus --version
```

Expected output:
```
prometheus, version 3.12.0 (branch: HEAD, ...)
```

> **Note (Prometheus 3.x):** version 3.x removed the bundled web console templates and the
> `--web.console.libraries` / `--web.console.templates` flags. The redesigned built-in UI
> replaces them. If you are following an older 2.x guide, ignore any step that mentions those
> flags — they will crash 3.x on startup.

---

## Step 3 — Locate the config and data directories

Homebrew sets these up for you. **Why two locations?** macOS (like Linux) keeps *config*
separate from *runtime data*, so you can wipe metrics without touching your config:

- **Config:** `$(brew --prefix)/etc/prometheus.yml` — the scrape configuration.
- **Data:** `$(brew --prefix)/var/prometheus/` — the time-series database.

```bash
ls -la "$BREW/etc/prometheus.yml"
ls -d  "$BREW/var/prometheus" 2>/dev/null || echo "(data dir is created on first run)"
```

Unlike the Linux native install, you do **not** create a dedicated service user here — under
`brew services` the process runs as **your** macOS user, which already owns these Homebrew
paths. That keeps the local-dev setup simple (no `sudo`, no `chown`).

---

## Step 4 — Write the lab configuration

Replace the default config with one that scrapes Prometheus itself and has a commented-out
block for the macOS project (Project 6). Commented jobs do nothing until you uncomment them.

```bash
tee "$BREW/etc/prometheus.yml" > /dev/null << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:

  # Prometheus scrapes itself — always on.
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # ---------------------------------------------------------------------------
  # Project 6 — Mac System Monitor (port 8086)
  # Uncomment after starting the app: python projects-native/06-mac-system-monitor/app/app.py
  # ---------------------------------------------------------------------------
  # - job_name: "mac-system-monitor"
  #   static_configs:
  #     - targets: ["localhost:8086"]

EOF
```

Verify the file was written:
```bash
cat "$BREW/etc/prometheus.yml"
```

---

## Step 5 — Run Prometheus (manual test first)

Before setting up the background service, run it in the foreground to confirm it starts.
The `--web.enable-lifecycle` flag turns on the `POST /-/reload` endpoint we use later to load
config changes without a full restart:

```bash
prometheus \
  --config.file="$BREW/etc/prometheus.yml" \
  --storage.tsdb.path="$BREW/var/prometheus" \
  --web.enable-lifecycle
```

Expected output (last few lines):
```
ts=... level=info msg="Server is ready to receive web requests."
```

Open **http://localhost:9090** in your browser — you should see the Prometheus UI.
Go to **http://localhost:9090/targets** — the `prometheus` job should show **UP**.

Press `Ctrl+C` to stop it once you have confirmed it works.

---

## Step 6 — Run Prometheus as a background service

You have two options. **6a (brew services)** is the simplest and auto-starts on login.
**6b (manual)** keeps the `--web.enable-lifecycle` reload endpoint, which is handy while you
toggle project scrape jobs on and off in this lab.

### Step 6a — brew services (auto-start on login)

**Why `brew services`?** Running Prometheus by hand (Step 5) stops the moment you close the
terminal or reboot. `brew services` registers a **launchd** job (macOS's service manager, the
counterpart to Linux's systemd) so Prometheus starts automatically when you log in and restarts
if it crashes.

```bash
brew services start prometheus
```

Check status:
```bash
brew services list
```

Expected output includes:
```
prometheus  started  <your-user>  ~/Library/LaunchAgents/homebrew.mxcl.prometheus.plist
```

> **Heads-up about reload:** the Homebrew launchd job starts Prometheus **without**
> `--web.enable-lifecycle`, so `curl -X POST .../-/reload` will return `404`. With `brew
> services` you instead apply config changes by restarting:
> ```bash
> brew services restart prometheus
> ```
> If you want the live `/-/reload` endpoint, use Step 6b instead.

### Step 6b — Manual background run (keeps the reload endpoint)

```bash
nohup prometheus \
  --config.file="$BREW/etc/prometheus.yml" \
  --storage.tsdb.path="$BREW/var/prometheus" \
  --web.enable-lifecycle \
  > "$BREW/var/log/prometheus.log" 2>&1 &

echo "Prometheus PID: $!"
```

To stop it later:
```bash
kill $(pgrep -f "prometheus --config.file")
```

> With `nohup`, the process keeps running after you close the terminal, but it does **not**
> restart on reboot. Re-run the command after a restart, or use Step 6a for auto-start.

---

## Step 7 — Verify

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

After editing `$(brew --prefix)/etc/prometheus.yml` (for example, to uncomment Project 6):

```bash
# If you used Step 6b (manual run with --web.enable-lifecycle):
curl -X POST http://localhost:9090/-/reload

# If you used Step 6a (brew services):
brew services restart prometheus
```

---

## Troubleshooting

**`prometheus: command not found`**
Homebrew's bin directory is not on your `PATH`. Run `eval "$(brew shellenv)"`, or restart your
terminal, then try again.

**Port 9090 already in use**
```bash
lsof -nP -iTCP:9090 -sTCP:LISTEN
```
Kill the process using that port, or change the Prometheus port with `--web.listen-address=":9091"`.

**Config reload returns 404**
You started Prometheus with `brew services`, which omits `--web.enable-lifecycle`. Either run
`brew services restart prometheus`, or switch to the manual run in Step 6b.

**`brew services` says "Unknown command"**
Run `brew tap homebrew/services` once, then retry.

**Prometheus 3.x fails to start with `opening console templates ... no such file or directory`**
You are passing `--web.console.templates` / `--web.console.libraries` flags left over from a
2.x guide. Version 3.x no longer ships those directories. Remove both flags (this guide omits them).
