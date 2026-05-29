# 02 — Run Grafana with Docker Compose

> **Read `01-docker-cli.md` first.** This file assumes you already ran Grafana
> manually. Now we collapse everything into a single file and command.

---

## How the Compose file maps to `01-docker-cli.md`

| Manual command / flag | Compose equivalent |
|---|---|
| `docker volume create grafdata` | `volumes: grafdata:` at the bottom of the file |
| `docker run -d` | service listed under `services:` |
| `--name grafana` | the service key name (`grafana:`) |
| `-p 3000:3000` | `ports: - "3000:3000"` |
| `-v grafdata:/var/lib/grafana` | `volumes: - grafdata:/var/lib/grafana` |
| `-e GF_SECURITY_ADMIN_USER=admin` | `environment: - GF_SECURITY_ADMIN_USER=admin` |
| `-e GF_SECURITY_ADMIN_PASSWORD=admin` | `environment: - GF_SECURITY_ADMIN_PASSWORD=admin` |
| `grafana/grafana:10.4.2` | `image: grafana/grafana:10.4.2` |
| (run the command) | `docker compose up -d` |

Open `docker-compose.yml` alongside this file and trace each line to the table above.

---

## Step 1 — Clean up any old container

If you followed `01-docker-cli.md` and have not cleaned up yet:

```bash
docker rm -f grafana
```

The named volume (`grafdata`) can stay — Compose will reuse it.

---

## Step 2 — Start Grafana with Compose

Make sure you are in the `grafana-setup/` directory.

```bash
docker compose up -d
```

**Expected output:**
```
[+] Running 2/2
 ✔ Volume "grafana-setup_grafdata"  Created
 ✔ Container grafana                Started
```

---

## Step 3 — Check status

```bash
docker compose ps
```

**Expected output:**
```
NAME      IMAGE                   COMMAND   SERVICE   STATUS    PORTS
grafana   grafana/grafana:10.4.2  ...       grafana   running   0.0.0.0:3000->3000/tcp
```

---

## Step 4 — View logs

```bash
docker compose logs grafana
```

Follow logs live:
```bash
docker compose logs -f grafana
```

Press Ctrl+C to stop following.

---

## Step 5 — Verify

Open **http://localhost:3000** and log in with `admin` / `admin`.

Same result as the manual run — Compose produces the identical container.

---

## Step 6 — Stop and clean up

```bash
# Stop containers, keep volumes
docker compose down

# Stop AND delete volumes (fresh start)
docker compose down -v
```

| Compose command | Manual equivalent |
|---|---|
| `docker compose down` | `docker stop grafana && docker rm grafana` |
| `docker compose down -v` | `docker stop grafana && docker rm grafana && docker volume rm grafdata` |

---

## Why Compose?

One file, one command, version-controlled, repeatable. When you add Prometheus in
`../integration/`, you simply add a second service block — no extra terminal commands needed.

---

**Next step:** Head to **`../integration/`** to wire Prometheus and Grafana together on a
shared Docker network.
