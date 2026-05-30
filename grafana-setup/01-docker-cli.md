# 01 — Run Grafana with Plain Docker Commands

> **Do this first.** We run Grafana manually so you understand every piece.
> After this, `02-docker-compose.md` shows you the shortcut (Compose).
>
> **Goal:** Grafana running at `http://localhost:3000`, logged in, with a manual
> data source added.

---

## Prerequisites

- Docker is installed and running (`docker --version` should print a version number).
- You are in the `grafana-setup/` directory.

---

## Step 1 — Create a named volume for Grafana data

Grafana stores its dashboards, user accounts, and settings on disk. Without a volume,
all of that is lost when the container is removed.

```bash
docker volume create grafdata
```

**Expected output:**
```
grafdata
```

> **Why a named volume (not a host directory)?**
> The Grafana container runs as a non-root user (UID 472). If you mount a regular
> directory from your machine, Docker may create it as root and Grafana won't be
> able to write to it. Named volumes are managed by Docker and avoid this entirely.

---

## Step 2 — Run Grafana

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -v grafdata:/var/lib/grafana \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:13.0.1
```

**What each flag does:**

| Flag | Meaning |
|------|---------|
| `-d` | Detached mode — runs in the background |
| `--name grafana` | Friendly container name |
| `-p 3000:3000` | Maps port 3000 on your machine to port 3000 inside the container |
| `-v grafdata:/var/lib/grafana` | Mounts the named volume at Grafana's data directory |
| `-e GF_SECURITY_ADMIN_USER=admin` | Sets the admin username via environment variable |
| `-e GF_SECURITY_ADMIN_PASSWORD=admin` | Sets the initial admin password |
| `grafana/grafana:13.0.1` | Official Grafana OSS image, pinned version |

**Expected output:** A long container ID hash.

---

## Step 3 — Check that Grafana started

```bash
docker ps
```

**Expected output** (abbreviated):
```
CONTAINER ID   IMAGE                  COMMAND     PORTS                    NAMES
b9e4a1d3c2f6   grafana/grafana:13.0.1  ...        0.0.0.0:3000->3000/tcp   grafana
```

---

## Step 4 — View the logs

```bash
docker logs grafana
```

**Expected output** (look for this line near the end):
```
logger=http.server t=... msg="HTTP Server Listen" address=[::]:3000 ...
```

---

## Step 5 — Log in to Grafana

1. Open **http://localhost:3000** in your browser.
2. You will see the Grafana login page.
3. Enter username `admin` and password `admin`.
4. Grafana will immediately ask you to change the password.
   - Set a new password (or click "Skip" to use `admin` for now — that is fine for local learning).

**Verify:** You should see the Grafana home dashboard — a dark/light page with a grid icon
and a "Welcome to Grafana" message.

---

## Step 6 — Explore the UI (2-minute tour)

The main menu is on the left sidebar:

| Icon / Label | What it is |
|---|---|
| Home (grid) | Jump to the home dashboard |
| Dashboards | Create and organize dashboards |
| Explore | Ad-hoc querying — type a query and see a graph immediately |
| Alerting | Set up alerts when metrics cross thresholds |
| Connections | Add data sources (databases, Prometheus, etc.) |
| Administration | Manage users and plugins |

---

## Step 7 — Manually add a data source

> **What is a data source?** It tells Grafana where to fetch data. In our case,
> the data source will be Prometheus. For now, we will just explore the UI — we do
> not have Prometheus running yet. The actual connection happens in `../integration/`.

1. In the left sidebar, click **Connections** → **Data sources**.
2. Click **Add new data source**.
3. You will see a list of supported data sources — Prometheus is near the top.
4. Click **Prometheus**.
5. In the "Prometheus server URL" field, you would type `http://prometheus:9090`
   (the service name, not `localhost` — this is explained in detail in `../integration/`).
6. **Do not save yet** — Prometheus isn't running. Just explore the form.
7. Press Escape or navigate away.

Understanding that this screen exists is important: when you get to integration,
provisioning will fill this in automatically.

---

## Step 8 — Stop and remove the container (cleanup)

```bash
# Stop the container
docker stop grafana

# Remove the container (named volume 'grafdata' is preserved)
docker rm grafana
```

To also delete the volume:
```bash
docker volume rm grafdata
```

---

## Troubleshooting

**Container is not in `docker ps`:**
```bash
docker ps -a
docker logs grafana
```

**Port 3000 already in use:**
```bash
sudo lsof -i :3000      # Linux / WSL2
netstat -ano | findstr 3000   # Windows PowerShell
```
Either stop the other process or change the host port: `-p 3001:3000`.

**Blank page or "502 Bad Gateway":**
Grafana may still be starting. Wait 5–10 seconds and refresh.

---

**Next:** Read `02-docker-compose.md` to see how this entire setup collapses into one command.
