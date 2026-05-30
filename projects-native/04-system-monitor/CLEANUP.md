# Clean Up — System Monitor (Project 4)

Reverses everything from [CONNECT.md](CONNECT.md). Follow the same path (Native or Docker) you
used to set it up.

---

## Path A — Native WSL2 cleanup

### A1 — Stop the app

If you started it in the foreground, press `Ctrl+C` in its terminal. If you ran it in the
background with `nohup`:

```bash
kill $(pgrep -f "python app.py")
```

Verify it stopped:

```bash
curl -s http://localhost:8084/metrics || echo "app stopped"
```

Expected: `app stopped`.

### A2 — Remove the Python virtual environment

The venv was created just for this project, so deleting it removes all installed packages cleanly
without touching your system Python:

```bash
rm -rf projects-native/04-system-monitor/app/.venv
rm -f  projects-native/04-system-monitor/app/app.log
```

### A3 — Remove the scrape job from native Prometheus

Re-comment (or delete) the `system-monitor` block in `/etc/prometheus/prometheus.yml` (the
**native** config — note the `localhost:8084` target), then reload:

```bash
sudo nano /etc/prometheus/prometheus.yml
curl -X POST http://localhost:9090/-/reload
```

---

## Path B — Docker cleanup

### B1 — Stop and remove the container

Run from `projects-native/04-system-monitor/`:

```bash
docker compose down
```

> The container only bind-mounts the host `/proc` read-only — nothing is written to the host, so
> there is nothing else to clean up there.

### B2 — Remove the scrape job from infra Prometheus

Re-comment (or delete) the `system-monitor` block in `infra/prometheus.yml` (the **Docker** config
— note the `system-monitor:8084` target), then reload:

```bash
curl -X POST http://localhost:9090/-/reload
```

### B3 — Optional: remove the built image

```bash
docker rmi 04-system-monitor-system-monitor 2>/dev/null || docker image prune -f
```

---

## Both paths — remove the dashboard from Grafana

- **If you imported it by hand:** Grafana → the **System Monitor** dashboard → **settings (gear)**
  → **Delete**.
- **If it was auto-provisioned by `infra/`:** it disappears only when you tear down `infra/`
  (see `infra/CLEANUP.md`).

---

## Verify it's clean

```bash
curl -s http://localhost:8084/metrics || echo "system-monitor no longer answering"
curl -s http://localhost:9090/api/v1/targets | grep system-monitor || echo "target removed"
```

Expected: both lines confirm the project is gone.
