# Clean Up the Native macOS Setup

This reverses everything from [01-install-prometheus.md](01-install-prometheus.md) and
[02-install-grafana.md](02-install-grafana.md): it stops the services, uninstalls the Homebrew
packages, and removes the leftover config and data, leaving your Mac as it was before.

> **When to use this:** you finished the projects and want a clean machine, you want to
> re-install from scratch, or something went wrong and you'd rather start over.

> **Order matters:** stop the services *first*, then uninstall. Deleting files out from under a
> running service leaves zombie processes and confusing errors.

Set the prefix shortcut for this session:
```bash
BREW="$(brew --prefix)"
```

---

## Part 1 — Remove Prometheus

### Step 1 — Stop the service

If you used `brew services` (Step 6a):
```bash
brew services stop prometheus
```

`brew services stop` halts it now **and** removes the launchd auto-start entry, so it does not
come back on next login.

If you ran it manually with `nohup` instead (Step 6b):
```bash
kill $(pgrep -f "prometheus --config.file")
```

### Step 2 — Uninstall the package

```bash
brew uninstall prometheus
```

This removes the binary and the launchd service definition.

### Step 3 — Remove config and data

Homebrew leaves your config and the metrics database behind on uninstall. For a fully clean
state, remove them:

```bash
rm -f  "$BREW/etc/prometheus.yml"
rm -rf "$BREW/var/prometheus"
rm -f  "$BREW/var/log/prometheus.log"
```

> This deletes all collected metrics. That is the point of a clean state — there is nothing to
> back up in a learning setup.

### Step 4 — Verify Prometheus is gone

```bash
which prometheus || echo "prometheus removed"
curl -s http://localhost:9090/-/healthy || echo "port 9090 no longer answering"
```

Expected: both lines confirm removal.

---

## Part 2 — Remove Grafana

### Step 1 — Stop the service

```bash
brew services stop grafana
```

(Or `kill $(pgrep -f "grafana server")` if you started it manually in Step 3b.)

### Step 2 — Uninstall the package

```bash
brew uninstall grafana
```

### Step 3 — Remove config, data, and logs

```bash
rm -rf "$BREW/etc/grafana"
rm -rf "$BREW/var/lib/grafana"
rm -rf "$BREW/var/log/grafana"
```

> `var/lib/grafana` holds the SQLite database with all your dashboards and settings — removing
> it is what makes the state truly clean.

### Step 4 — Verify Grafana is gone

```bash
which grafana || echo "grafana removed"
curl -s http://localhost:3000/api/health || echo "port 3000 no longer answering"
```

Expected: both lines confirm removal.

---

## Optional — clean up Homebrew leftovers

```bash
brew cleanup
brew autoremove
```

`autoremove` drops any dependencies that were pulled in only for Prometheus or Grafana.

---

## Done

Prometheus and Grafana are fully removed from macOS. To start over, follow
[01-install-prometheus.md](01-install-prometheus.md) again from Step 1.
