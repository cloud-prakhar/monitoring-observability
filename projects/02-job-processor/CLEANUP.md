# Clean Up — Job Processor (Project 2)

Reverses everything from [CONNECT.md](CONNECT.md): stops the app container, removes its image,
takes the scrape job back out of Prometheus, and removes the dashboard — leaving the shared infra
(`infra/`) untouched and clean for the next project.

---

## Step 1 — Stop and remove the app container

Run from the `projects/02-job-processor/` directory:

```bash
docker compose down
```

Expected output:
```
 ✔ Container job-processor  Removed
```

---

## Step 2 — Remove the scrape job from Prometheus

Re-comment (or delete) the `job-processor` block in `infra/prometheus.yml`:

```yaml
  # - job_name: "job-processor"
  #   static_configs:
  #     - targets: ["job-processor:8082"]
```

Then reload Prometheus:

```bash
curl -X POST http://localhost:9090/-/reload
```

Verify the target is gone:

```bash
curl -s http://localhost:9090/api/v1/targets | grep job-processor || echo "target removed"
```

Expected: `target removed`.

---

## Step 3 — Remove the dashboard from Grafana

- **If you imported it by hand:** Grafana → the **Job Processor** dashboard → **settings (gear)** →
  **Delete**.
- **If it was auto-provisioned by `infra/`:** it only disappears when you tear down `infra/`
  (see `infra/CLEANUP.md`). Expected and harmless.

---

## Step 4 — Optional: remove the built image

```bash
docker rmi 02-job-processor-job-processor 2>/dev/null || docker image prune -f
```

---

## Verify it's clean

```bash
docker ps -a | grep job-processor || echo "no job-processor container"
```

Expected: `no job-processor container`. The shared `infra/` stack keeps running for other projects.
