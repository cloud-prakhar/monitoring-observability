# Clean Up — URL Health Checker (Project 5)

Reverses everything from [CONNECT.md](CONNECT.md). Follow the same path (Native or Docker) you
used to set it up.

---

## Path A — Native WSL2 cleanup

### A1 — Stop the app

Press `Ctrl+C` in its terminal, or if you ran it in the background:

```bash
kill $(pgrep -f "python app.py")
```

Verify it stopped:

```bash
curl -s http://localhost:8085/metrics || echo "app stopped"
```

Expected: `app stopped`.

### A2 — Remove the Python virtual environment

```bash
rm -rf projects-native/05-url-health-checker/app/.venv
rm -f  projects-native/05-url-health-checker/app/app.log
```

### A3 — Remove the scrape job from native Prometheus

Re-comment (or delete) the `url-health-checker` block in `/etc/prometheus/prometheus.yml`, then
reload:

```bash
sudo nano /etc/prometheus/prometheus.yml
curl -X POST http://localhost:9090/-/reload
```

---

## Path B — Docker cleanup

### B1 — Stop and remove the container

Run from `projects-native/05-url-health-checker/`:

```bash
docker compose down
```

> This project uses `network_mode: host`, so it created no project network of its own — `down`
> fully detaches it.

### B2 — Remove the scrape job from Prometheus

The Docker path uses host networking, so the target is `localhost:8085` regardless of where
Prometheus runs. Re-comment (or delete) the `url-health-checker` block in the Prometheus config you
edited (`infra/prometheus.yml` for Docker infra, or `/etc/prometheus/prometheus.yml` for native
Prometheus), then reload:

```bash
curl -X POST http://localhost:9090/-/reload
```

### B3 — Optional: remove the built image

```bash
docker rmi 05-url-health-checker-url-health-checker 2>/dev/null || docker image prune -f
```

---

## Both paths — remove the dashboard from Grafana

- **If you imported it by hand:** Grafana → the **URL Health Checker** dashboard →
  **settings (gear)** → **Delete**.
- **If it was auto-provisioned by `infra/`:** it disappears only when you tear down `infra/`
  (see `infra/CLEANUP.md`).

---

## Verify it's clean

```bash
curl -s http://localhost:8085/metrics || echo "url-health-checker no longer answering"
curl -s http://localhost:9090/api/v1/targets | grep url-health-checker || echo "target removed"
```

Expected: both lines confirm the project is gone.
