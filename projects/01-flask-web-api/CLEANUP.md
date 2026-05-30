# Clean Up — Flask Web API (Project 1)

Reverses everything from [CONNECT.md](CONNECT.md): stops the app container, removes its image,
takes the scrape job back out of Prometheus, and removes the dashboard — leaving the shared infra
(`infra/`) untouched and clean for the next project.

---

## Step 1 — Stop and remove the app container

Run from the `projects/01-flask-web-api/` directory:

```bash
docker compose down
```

Expected output:
```
 ✔ Container flask-web-api  Removed
```

This project has no data volume of its own, so there is nothing extra to wipe.

---

## Step 2 — Remove the scrape job from Prometheus

Editing the config is the reverse of CONNECT.md Step "Add the scrape job". Re-comment (or delete)
the `flask-web-api` block in `infra/prometheus.yml`:

```yaml
  # - job_name: "flask-web-api"
  #   static_configs:
  #     - targets: ["flask-web-api:8081"]
```

Then reload Prometheus so it forgets the target:

```bash
curl -X POST http://localhost:9090/-/reload
```

Verify the target is gone:

```bash
curl -s http://localhost:9090/api/v1/targets | grep flask-web-api || echo "target removed"
```

Expected: `target removed`.

---

## Step 3 — Remove the dashboard from Grafana

- **If you imported the dashboard by hand** (CONNECT.md "Import a dashboard"): open Grafana →
  the **Flask Web API** dashboard → dashboard **settings (gear icon)** → **Delete**.
- **If the dashboard was auto-provisioned by `infra/`** (the JSON in `infra/grafana/dashboards/`):
  you cannot delete it from the UI — it reappears on refresh. It goes away only when you tear down
  `infra/` (see `infra/CLEANUP.md`). That is expected and harmless.

---

## Step 4 — Optional: remove the built image

`docker compose` built a local image for this app. Remove it to reclaim disk space:

```bash
docker rmi 01-flask-web-api-flask-web-api 2>/dev/null || docker image prune -f
```

> Compose names the image after the directory and service. If the exact name above doesn't match,
> `docker image prune -f` removes all dangling images instead.

---

## Verify it's clean

```bash
docker ps -a | grep flask-web-api || echo "no flask-web-api container"
```

Expected: `no flask-web-api container`. The shared `infra/` stack keeps running for other projects.
