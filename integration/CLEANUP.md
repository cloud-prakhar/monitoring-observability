# Clean Up — Prometheus + Grafana Integration

Removes both containers, both data volumes, and the `monitoring` network created in
[01-docker-cli.md](01-docker-cli.md) or [02-docker-compose.md](02-docker-compose.md).

Pick the section that matches how you started everything.

---

## If you used the Docker CLI (01-docker-cli.md)

```bash
# Stop and remove both containers
docker stop grafana prometheus
docker rm grafana prometheus

# Remove the data volumes
docker volume rm grafdata promdata

# Remove the shared network (must be done AFTER the containers are gone —
# Docker refuses to delete a network that still has containers attached)
docker network rm monitoring
```

---

## If you used Docker Compose (02-docker-compose.md)

Run this from the `integration/` directory:

```bash
docker compose down -v
```

Compose removes the containers, the `-v` flag removes both volumes, and Compose also removes the
`monitoring` network it created — all in one command.

---

## Optional — remove the images

```bash
docker rmi prom/prometheus:v3.12.0 grafana/grafana:13.0.1
```

---

## Verify it's clean

```bash
docker ps -a | grep -E "prometheus|grafana" || echo "no containers"
docker volume ls | grep -E "promdata|grafdata" || echo "no volumes"
docker network ls | grep monitoring || echo "no monitoring network"
```

Expected: all three lines report nothing left behind.
