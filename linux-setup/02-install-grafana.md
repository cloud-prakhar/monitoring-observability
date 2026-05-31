# Install Grafana Natively on Linux

Grafana is installed from its official package repository. The package installs the binary,
default config, a dedicated `grafana` system user, and a ready-made systemd unit.

This step branches by distro family. Use **Step 2a** for Debian/Ubuntu (APT) or **Step 2b** for
RHEL/Fedora (DNF). Everything after Step 3 is identical.

---

## Prerequisites

Complete [01-install-prometheus.md](01-install-prometheus.md) first. Grafana connects to
Prometheus as a data source, so Prometheus should be running before you configure Grafana.

---

## Step 1 — Install prerequisite tools

```bash
# Debian/Ubuntu:
sudo apt-get update
sudo apt-get install -y apt-transport-https software-properties-common wget gpg

# RHEL/Fedora:
sudo dnf install -y wget
```

---

## Step 2a — Add the Grafana repository (Debian / Ubuntu, APT)

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
  Candidate: 13.x.x
```

Then jump to **Step 3**.

---

## Step 2b — Add the Grafana repository (RHEL / Fedora, DNF)

```bash
sudo tee /etc/yum.repos.d/grafana.repo > /dev/null << 'EOF'
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF
```

Verify the repo is visible:
```bash
sudo dnf --refresh info grafana | head -8
```

---

## Step 3 — Install Grafana

```bash
# Debian/Ubuntu:
sudo apt-get install -y grafana

# RHEL/Fedora:
sudo dnf install -y grafana
```

Expected output (last few lines):
```
Setting up grafana (13.x.x) ...        # apt
# or
Installed: grafana-13.x.x...           # dnf
```

Verify the binary is installed:
```bash
grafana-server --version
```

Expected output:
```
Version 13.x.x (commit: xxxxxxx, branch: HEAD)
```

---

## Step 4 — Start Grafana with systemd

Unlike Prometheus, you do **not** create a user or a service file here — the Grafana package
already did both during install. It created a dedicated `grafana` system user (same
least-privilege reason as the `prometheus` user: Grafana should never run as `root`) and installed
a ready-made `grafana-server.service` unit. You just enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

**Why `enable` *and* `start`?** `enable` registers the service to launch automatically on every
boot; `start` launches it right now. Running both means Grafana is up immediately and stays up
after future reboots.

Check status:
```bash
sudo systemctl status grafana-server
```

Expected output:
```
● grafana-server.service - Grafana instance
     Loaded: loaded (/usr/lib/systemd/system/grafana-server.service; enabled; ...)
     Active: active (running) since ...
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

The main config is at `/etc/grafana/grafana.ini`. The defaults work for local development.
Common settings you might change:

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
sudo systemctl restart grafana-server
```

---

## Data directory

Grafana stores its database (SQLite), dashboards, and plugins in `/var/lib/grafana/`. This
directory persists across restarts.

To start completely fresh (wipes all dashboards and settings):
```bash
sudo systemctl stop grafana-server
sudo rm -rf /var/lib/grafana/grafana.db
sudo systemctl start grafana-server
```

---

## Troubleshooting

**`E: Package 'grafana' has no installation candidate`** (APT)
The repository was not added correctly. Re-run Step 2a, then `sudo apt-get update` again.

**`No match for argument: grafana`** (DNF)
The repo file is missing or malformed. Re-run Step 2b, then `sudo dnf --refresh info grafana`.

**Port 3000 already in use**
```bash
sudo ss -tlnp | grep 3000
```
Change the Grafana port in `/etc/grafana/grafana.ini` under `[server] → http_port`.

**Grafana shows a blank page on first load**
Wait 10–15 seconds and refresh. The SQLite database initializes on first boot.

**Cannot log in with admin/admin**
The password was changed during a previous session. Reset it:
```bash
sudo grafana-cli admin reset-admin-password newpassword
sudo systemctl restart grafana-server
```
