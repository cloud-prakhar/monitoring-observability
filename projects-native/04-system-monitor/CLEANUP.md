# Clean Up — System Monitor (Project 4)

Reverses everything from [CONNECT.md](CONNECT.md). This is a native WSL2 project.

---

## 1. Stop the app

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

## 2. Remove the Python virtual environment

The venv was created just for this project, so deleting it removes all installed packages
cleanly without touching your system Python:

```bash
rm -rf projects-native/04-system-monitor/app/.venv
rm -f  projects-native/04-system-monitor/app/app.log
```

## 3. Remove the scrape job from Prometheus

Re-comment (or delete) the `system-monitor` block in `/etc/prometheus/prometheus.yml`
(target `localhost:8084`), then reload:

```bash
sudo nano /etc/prometheus/prometheus.yml
curl -X POST http://localhost:9090/-/reload
```

## 4. Remove the dashboard from Grafana

Grafana → the **System Monitor** dashboard → **settings (gear)** → **Delete**.

---

## Verify it's clean

```bash
curl -s http://localhost:8084/metrics || echo "system-monitor no longer answering"
curl -s http://localhost:9090/api/v1/targets | grep system-monitor || echo "target removed"
```

Expected: both lines confirm the project is gone.
