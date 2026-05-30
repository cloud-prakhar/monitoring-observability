# Clean Up — Standalone Prometheus

Removes the Prometheus container and its data volume created in
[01-docker-cli.md](01-docker-cli.md) or [02-docker-compose.md](02-docker-compose.md), returning
Docker to a clean state.

Pick the section that matches how you started Prometheus.

---

## If you used the Docker CLI (01-docker-cli.md)

```bash
# Stop and remove the container
docker stop prometheus
docker rm prometheus

# Remove the named data volume (deletes the time-series database)
docker volume rm promdata
```

> `docker rm` deletes the container but **not** the volume — metrics survive a container removal on
> purpose. The separate `docker volume rm` is what actually wipes the data.

---

## If you used Docker Compose (02-docker-compose.md)

Run this from the `prometheus-setup/` directory:

```bash
docker compose down -v
```

`down` stops and removes the container; the `-v` flag also removes the `promdata` volume. Without
`-v`, the volume (and your metrics) would persist.

---

## Optional — remove the image

Only if you want to reclaim the disk space and don't plan to use Prometheus again soon:

```bash
docker rmi prom/prometheus:v3.12.0
```

---

## Verify it's clean

```bash
docker ps -a | grep prometheus || echo "no prometheus container"
docker volume ls | grep promdata || echo "no promdata volume"
```

Expected: both lines report nothing left behind.
