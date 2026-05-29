# Install Grafana Natively on WSL2

Grafana is installed via the official APT repository. The package installs the binary, default config, and init scripts in the standard Linux locations.

---

## Prerequisites

Complete [01-install-prometheus.md](01-install-prometheus.md) first. Grafana connects to Prometheus as a data source, so Prometheus should be running before you configure Grafana.

---

## Step 1 — Install required tools

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https software-properties-common wget gpg
```

---

## Step 2 — Add the Grafana APT repository

```bash
# Import the GPG signing key
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key \
  | gpg --dearmor \
  | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null

# Add the stable repository
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" \
  | sudo tee /etc/apt/sources.list.d/grafana.list

# Update the package index
sudo apt-get update
```

Verify the repo is listed:
```bash
apt-cache policy grafana | head -5
```

Expected output includes a line like:
```
  Candidate: 10.x.x
```

---

## Step 3 — Install Grafana

```bash
sudo apt-get install -y grafana
```

Expected output (last few lines):
```
Setting up grafana (10.x.x) ...
```

Verify the binary is installed:
```bash
grafana-server --version
```

Expected output:
```
Version 10.x.x (commit: xxxxxxx, branch: HEAD)
```

---

## Step 4a — Start Grafana with systemd (if systemd is available)

Check whether systemd is running (same check as in the Prometheus guide):
```bash
ps --no-headers -o comm 1
```

If the output is `systemd`:
```bash
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

Check status:
```bash
sudo systemctl status grafana-server
```

Expected output:
```
● grafana-server.service - Grafana instance
     Loaded: loaded (/lib/systemd/system/grafana-server.service; enabled; ...)
     Active: active (running) since ...
```

---

## Step 4b — Start Grafana manually (if systemd is not available)

```bash
sudo /usr/sbin/grafana-server \
  --config=/etc/grafana/grafana.ini \
  --homepath=/usr/share/grafana \
  web > /var/log/grafana.log 2>&1 &

echo "Grafana PID: $!"
```

To stop it:
```bash
sudo kill $(pgrep grafana-server)
```

---

## Step 5 — Verify Grafana is running

```bash
curl -s http://localhost:3000/api/health | python3 -m json.tool
```

Expected output:
```json
{
    "commit": "xxxxxxx",
    "database": "ok",
    "version": "10.x.x"
}
```

Open **http://localhost:3000** in your browser.

Default credentials:
- Username: `admin`
- Password: `admin`

Grafana will immediately prompt you to change the password. Set something you will remember, or skip for now.

---

## Grafana configuration file

The main config is at `/etc/grafana/grafana.ini`. The defaults work for local development. Common settings you might change:

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
# systemd:
sudo systemctl restart grafana-server

# manual:
sudo kill $(pgrep grafana-server)
# then re-run the grafana-server command from Step 4b
```

---

## Data directory

Grafana stores its database (SQLite), dashboards, and plugins in `/var/lib/grafana/`. This directory persists across restarts.

To start completely fresh (wipes all dashboards and settings):
```bash
sudo systemctl stop grafana-server
sudo rm -rf /var/lib/grafana/grafana.db
sudo systemctl start grafana-server
```

---

## Troubleshooting

**`E: Package 'grafana' has no installation candidate`**
The repository was not added correctly. Re-run Step 2 and then `sudo apt-get update` again.

**Port 3000 already in use**
```bash
sudo ss -tlnp | grep 3000
```
Change the Grafana port in `/etc/grafana/grafana.ini` under `[server] → http_port`.

**`sudo: grafana-server: command not found`**
The binary is at `/usr/sbin/grafana-server`. Use the full path.

**Grafana shows blank page on first load**
Wait 10–15 seconds and refresh. The SQLite database initializes on first boot.

**Cannot log in with admin/admin**
The password was changed during a previous session. Reset it:
```bash
sudo grafana-cli admin reset-admin-password newpassword
sudo systemctl restart grafana-server
```
