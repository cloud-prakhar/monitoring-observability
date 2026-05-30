# 02 — Run Prometheus with Docker Compose

> **Read `01-docker-cli.md` first.** This file assumes you already ran Prometheus
> manually and understand what each flag does. Now we collapse all of that into a
> single file and a single command.

---

## What is Docker Compose?

Docker Compose is a tool that lets you describe your containers, ports, volumes, and
networks in a YAML file (`docker-compose.yml`), then start everything with one command.
It is not magic — it runs the exact same Docker commands you ran by hand, just
automatically and repeatably.

> **v2 vs v1:** We use `docker compose` (space, two words) — the modern v2 built into
> Docker Desktop. The older `docker-compose` (hyphen) is v1 and is no longer maintained.
> The commands are similar but use the new form throughout this repo.

---

## How the Compose file maps to `01-docker-cli.md`

Every flag you typed in `docker run` has a direct equivalent in `docker-compose.yml`.

| Manual command / flag | Compose equivalent |
|---|---|
| `docker volume create promdata` | `volumes: promdata:` at the bottom of the file |
| `docker run -d` | service listed under `services:` (always detached) |
| `--name prometheus` | the service key name (`prometheus:`) |
| `-p 9090:9090` | `ports: - "9090:9090"` |
| `-v $(pwd)/prometheus.yml:/etc/...` | `volumes: - ./prometheus.yml:/etc/...:ro` |
| `-v promdata:/prometheus` | `volumes: - promdata:/prometheus` |
| `prom/prometheus:v3.12.0` | `image: prom/prometheus:v3.12.0` |
| `--config.file=...` (and other args) | `command:` list |
| (run the command) | `docker compose up -d` |

Open `docker-compose.yml` alongside this file and match each line to the table above.

---

## Step 1 — Make sure no old container is running

If you followed `01-docker-cli.md` and haven't cleaned up yet:

```bash
docker rm -f prometheus
```

The named volume (`promdata`) can stay — Compose will reuse it.

---

## Step 2 — Start Prometheus with Compose

Make sure you are in the `prometheus-setup/` directory (where `docker-compose.yml` lives).

```bash
docker compose up -d
```

**What this does:**
1. Reads `docker-compose.yml` in the current directory
2. Creates any volumes/networks defined in the file if they don't exist
3. Pulls the image if not already cached
4. Starts the container in detached mode (`-d`)

**Expected output:**
```
[+] Running 2/2
 ✔ Volume "prometheus-setup_promdata"  Created
 ✔ Container prometheus                Started
```

> **Note:** Compose prefixes volume names with the project name (the directory name by default),
> so the volume is actually called `prometheus-setup_promdata`. That is normal.

---

## Step 3 — Check status

```bash
docker compose ps
```

**Expected output:**
```
NAME         IMAGE                    COMMAND     SERVICE      STATUS    PORTS
prometheus   prom/prometheus:v3.12.0  ...         prometheus   running   0.0.0.0:9090->9090/tcp
```

---

## Step 4 — View logs

```bash
docker compose logs prometheus
```

Or follow logs live (Ctrl+C to stop):

```bash
docker compose logs -f prometheus
```

---

## Step 5 — Verify in the browser

Open **http://localhost:9090** — same as before.

Run the `up` query. You should see the same result as in step 01.

---

## Step 6 — Stop and clean up

```bash
# Stop containers but keep volumes (your data is preserved)
docker compose down

# Stop AND delete volumes (wipes all Prometheus data — fresh start)
docker compose down -v
```

**How these map to the manual commands:**

| Compose command | Manual equivalent |
|---|---|
| `docker compose down` | `docker stop prometheus && docker rm prometheus` |
| `docker compose down -v` | `docker stop prometheus && docker rm prometheus && docker volume rm promdata` |

---

## Why use Compose?

- **Repeatable**: anyone on your team can run `docker compose up -d` and get the same setup.
- **Version-controlled**: the config lives in a file you can commit to git.
- **One command instead of many**: no memorizing long `docker run` flags.
- **Scales**: when you add Grafana in the `integration/` section, you just add a second service block.

---

**Next step:** Try `../grafana-setup/` to set up Grafana on its own, then head to `../integration/` to wire the two together.
