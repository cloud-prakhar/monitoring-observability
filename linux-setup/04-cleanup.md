# Clean Up the Native Linux Setup

This reverses everything from [01-install-prometheus.md](01-install-prometheus.md) and
[02-install-grafana.md](02-install-grafana.md): it stops the services, removes the binaries,
config, data, and the dedicated service users, leaving the host in the state it was in before
you started.

> **When to use this:** you finished the projects and want a clean machine, you want to
> re-install from scratch, or something went wrong and you'd rather start over.

> **Order matters:** stop the services *first*, then delete their files. Deleting files out from
> under a running service leaves zombie processes and confusing errors.

---

## Part 1 — Remove Prometheus

### Step 1 — Stop and disable the service

```bash
sudo systemctl stop prometheus
sudo systemctl disable prometheus
```

`stop` halts it now; `disable` removes the "start on boot" link so it does not come back after a
reboot.

### Step 2 — Remove the systemd service file

```bash
sudo rm -f /etc/systemd/system/prometheus.service
sudo systemctl daemon-reload
```

`daemon-reload` tells systemd to forget the unit you just deleted.

### Step 3 — Remove the binaries

```bash
sudo rm -f /usr/local/bin/prometheus /usr/local/bin/promtool
```

### Step 4 — Remove config and data

```bash
sudo rm -rf /etc/prometheus /var/lib/prometheus
```

> This deletes all collected metrics. That is the point of a clean state — there is nothing to
> back up in a learning setup.

### Step 5 — Remove the dedicated service user

The install guide created a locked-down `prometheus` user to run the service. With the service
gone, that user serves no purpose, so remove it:

```bash
sudo userdel prometheus
```

> A "user does not exist" message here is fine — it just means the user was already removed.

### Step 6 — Verify Prometheus is gone

```bash
which prometheus || echo "prometheus removed"
curl -s http://localhost:9090/-/healthy || echo "port 9090 no longer answering"
```

Expected: both lines confirm removal.

---

## Part 2 — Remove Grafana

Grafana was installed from a package repository, so the package manager removes it cleanly.

### Step 1 — Stop and disable the service

```bash
sudo systemctl stop grafana-server
sudo systemctl disable grafana-server
```

### Step 2 — Purge the package

```bash
# Debian/Ubuntu:
sudo apt-get purge -y grafana
sudo apt-get autoremove -y

# RHEL/Fedora:
sudo dnf remove -y grafana
```

`purge` (APT) also deletes the package's config files; `autoremove` cleans up dependencies pulled
in only for Grafana. (DNF's `remove` covers both in one step.)

### Step 3 — Remove leftover data and the dedicated user

Package removal intentionally leaves your data directory in case you wanted to keep dashboards.
For a fully clean state, remove it too:

```bash
sudo rm -rf /var/lib/grafana /etc/grafana /var/log/grafana
sudo userdel grafana 2>/dev/null || true
```

> The package created the `grafana` system user; `userdel` removes it. The `|| true` keeps the
> command from erroring if the user is already gone.

### Step 4 — Remove the repository and signing key

So future package-index updates don't keep contacting Grafana's servers:

```bash
# Debian/Ubuntu:
sudo rm -f /etc/apt/sources.list.d/grafana.list
sudo rm -f /etc/apt/keyrings/grafana.gpg
sudo apt-get update

# RHEL/Fedora:
sudo rm -f /etc/yum.repos.d/grafana.repo
sudo dnf clean all
```

### Step 5 — Verify Grafana is gone

```bash
which grafana-server || echo "grafana removed"
curl -s http://localhost:3000/api/health || echo "port 3000 no longer answering"
```

Expected: both lines confirm removal.

---

## Done

Prometheus and Grafana are fully removed from the Linux host. To start over, follow
[01-install-prometheus.md](01-install-prometheus.md) again from Step 1.
