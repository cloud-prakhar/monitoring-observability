# Clean Up — Standalone Grafana

Removes the Grafana container and its data volume created in
[01-docker-cli.md](01-docker-cli.md) or [02-docker-compose.md](02-docker-compose.md), returning
Docker to a clean state.

Pick the section that matches how you started Grafana.

---

## If you used the Docker CLI (01-docker-cli.md)

```bash
# Stop and remove the container
docker stop grafana
docker rm grafana

# Remove the named data volume (deletes dashboards, users, and settings)
docker volume rm grafdata
```

> The `grafdata` volume holds everything you created in the Grafana UI. Removing it is what gives
> you a truly fresh Grafana next time.

---

## If you used Docker Compose (02-docker-compose.md)

Run this from the `grafana-setup/` directory:

```bash
docker compose down -v
```

`down` removes the container; `-v` also removes the `grafdata` volume.

---

## Optional — remove the image

```bash
docker rmi grafana/grafana:13.0.1
```

---

## Verify it's clean

```bash
docker ps -a | grep grafana || echo "no grafana container"
docker volume ls | grep grafdata || echo "no grafdata volume"
```

Expected: both lines report nothing left behind.
