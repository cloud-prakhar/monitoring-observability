# Clean Up — URL Health Checker (Project 5)

Reverses everything from [CONNECT.md](CONNECT.md). This is a native WSL2 project.

---

## 1. Stop the app

Press `Ctrl+C` in its terminal, or if you ran it in the background:

```bash
kill $(pgrep -f "python app.py")
```

Verify it stopped:

```bash
curl -s http://localhost:8085/metrics || echo "app stopped"
```

Expected: `app stopped`.

## 2. Remove the Python virtual environment

```bash
rm -rf projects-native/05-url-health-checker/app/.venv
rm -f  projects-native/05-url-health-checker/app/app.log
```

## 3. Remove the scrape job from Prometheus

Re-comment (or delete) the `url-health-checker` block in `/etc/prometheus/prometheus.yml`
(target `localhost:8085`), then reload:

```bash
sudo nano /etc/prometheus/prometheus.yml
curl -X POST http://localhost:9090/-/reload
```

## 4. Remove the dashboard from Grafana

Grafana → the **URL Health Checker** dashboard → **settings (gear)** → **Delete**.

---

## Verify it's clean

```bash
curl -s http://localhost:8085/metrics || echo "url-health-checker no longer answering"
curl -s http://localhost:9090/api/v1/targets | grep url-health-checker || echo "target removed"
```

Expected: both lines confirm the project is gone.
