# Install Grafana Natively on macOS

Grafana installs via Homebrew. The package drops the binary, a default config, and a launchd
service definition into the Homebrew prefix.

---

## Prerequisites

Complete [01-install-prometheus.md](01-install-prometheus.md) first. Grafana connects to
Prometheus as a data source, so Prometheus should be running before you configure Grafana.

Set the prefix shortcut again if you opened a new terminal:
```bash
BREW="$(brew --prefix)"
```

---

## Step 1 — Install Grafana

```bash
brew install grafana
```

Expected output (last few lines):
```
==> Pouring grafana--13.0.1...
🍺  /opt/homebrew/Cellar/grafana/13.0.1: ...
```

Verify the binary is installed:
```bash
grafana server --version
```

Expected output:
```
Version 13.x.x (commit: xxxxxxx, branch: HEAD)
```

> Older Grafana builds used `grafana-server --version`. Recent Homebrew builds use the
> `grafana server` subcommand. If one form errors, try the other.

---

## Step 2 — Where Grafana keeps its files

Homebrew installs Grafana into the prefix, with the same config/data split as Prometheus:

- **Config:** `$(brew --prefix)/etc/grafana/grafana.ini`
- **Data (SQLite DB, dashboards, plugins):** `$(brew --prefix)/var/lib/grafana/`
- **Logs:** `$(brew --prefix)/var/log/grafana/`

As with Prometheus, there is **no dedicated service user** on macOS — under `brew services`
Grafana runs as your user, which already owns these paths. (On Linux the package creates a
locked-down `grafana` user for least-privilege; Homebrew's local-dev model skips that.)

---

## Step 3a — Start Grafana with brew services (recommended)

**Why `brew services`?** It registers a launchd job (macOS's service manager) so Grafana starts
automatically on login and restarts if it crashes — the same reason the Linux guide uses systemd.

```bash
brew services start grafana
```

Check status:
```bash
brew services list
```

Expected output includes:
```
grafana  started  <your-user>  ~/Library/LaunchAgents/homebrew.mxcl.grafana.plist
```

---

## Step 3b — Start Grafana manually (alternative)

```bash
grafana server \
  --config="$BREW/etc/grafana/grafana.ini" \
  --homepath="$BREW/share/grafana" \
  > "$BREW/var/log/grafana/grafana.log" 2>&1 &

echo "Grafana PID: $!"
```

To stop it:
```bash
kill $(pgrep -f "grafana server")
```

---

## Step 4 — Verify Grafana is running

Grafana takes 10–15 seconds to initialize its database on first launch.

```bash
curl -s http://localhost:3000/api/health | python3 -m json.tool
```

Expected output:
```json
{
    "commit": "xxxxxxx",
    "database": "ok",
    "version": "13.x.x"
}
```

Open **http://localhost:3000** in your browser.

Default credentials:
- Username: `admin`
- Password: `admin`

Grafana will immediately prompt you to change the password. Set something you will remember,
or skip for now.

---

## Grafana configuration file

The main config is at `$(brew --prefix)/etc/grafana/grafana.ini`. The defaults work for local
development. Common settings you might change:

```ini
# Change the default port (if 3000 is in use):
[server]
http_port = 3001

# Disable login form (open access for local dev):
[auth.anonymous]
enabled = true
org_role = Viewer
```

After changing the config, restart the service:
```bash
# brew services:
brew services restart grafana

# manual:
kill $(pgrep -f "grafana server")
# then re-run the command from Step 3b
```

---

## Data directory

Grafana stores its database (SQLite), dashboards, and plugins in
`$(brew --prefix)/var/lib/grafana/`. This directory persists across restarts.

To start completely fresh (wipes all dashboards and settings):
```bash
brew services stop grafana
rm -f "$BREW/var/lib/grafana/grafana.db"
brew services start grafana
```

---

## Troubleshooting

**`grafana: command not found`**
Homebrew's bin directory is not on your `PATH`. Run `eval "$(brew shellenv)"` or restart your terminal.

**Port 3000 already in use**
```bash
lsof -nP -iTCP:3000 -sTCP:LISTEN
```
Change the Grafana port in `grafana.ini` under `[server] → http_port`.

**Grafana shows a blank page on first load**
Wait 10–15 seconds and refresh. The SQLite database initializes on first boot.

**Cannot log in with admin/admin**
The password was changed during a previous session. Reset it:
```bash
grafana cli --homepath "$BREW/share/grafana" admin reset-admin-password newpassword
brew services restart grafana
```
