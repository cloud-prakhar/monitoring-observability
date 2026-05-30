# Clean Up — Cache Service (Project 3)

Reverses everything from [CONNECT.md](CONNECT.md): stops the app container, removes its image,
takes the scrape job back out of Prometheus, and removes the dashboard — leaving the shared infra
(`infra/`) untouched and clean for the next project.

---

## Step 1 — Stop and remove the app container

Run from the `projects/03-cache-service/` directory:

```bash
docker compose down
```

Expected output:
```
 ✔ Container cache-service  Removed
```

> The cache is in-memory only, so removing the container also clears all cached keys — there is no
> separate volume to wipe.

---

## Step 2 — Remove the scrape job from Prometheus

Re-comment (or delete) the `cache-service` block in `infra/prometheus.yml`:

```yaml
  # - job_name: "cache-service"
  #   static_configs:
  #     - targets: ["cache-service:8083"]
```

Then reload Prometheus:

```bash
curl -X POST http://localhost:9090/-/reload
```

Verify the target is gone:

```bash
curl -s http://localhost:9090/api/v1/targets | grep cache-service || echo "target removed"
```

Expected: `target removed`.

---

## Step 3 — Remove the dashboard from Grafana

- **If you imported it by hand:** Grafana → the **Cache Service** dashboard → **settings (gear)** →
  **Delete**.
- **If it was auto-provisioned by `infra/`:** it only disappears when you tear down `infra/`
  (see `infra/CLEANUP.md`). Expected and harmless.

---

## Step 4 — Optional: remove the built image

```bash
docker rmi 03-cache-service-cache-service 2>/dev/null || docker image prune -f
```

---

## Verify it's clean

```bash
docker ps -a | grep cache-service || echo "no cache-service container"
```

Expected: `no cache-service container`. The shared `infra/` stack keeps running for other projects.
