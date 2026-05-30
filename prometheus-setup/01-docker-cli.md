# 01 — Run Prometheus with Plain Docker Commands

> **Do this first.** We run Prometheus manually so you understand every piece.
> After this, `02-docker-compose.md` shows you the shortcut (Compose).
>
> **Goal:** Prometheus running at `http://localhost:9090` with persistent storage.

---

## Prerequisites

- Docker is installed and running (`docker --version` should print a version number).
- You are in the `prometheus-setup/` directory.

---

## Step 1 — Create a named volume for Prometheus data

**What is a volume?** A named Docker volume is a storage area managed by Docker.
Prometheus stores its time-series database here. Without a volume, all data is lost
when the container is removed.

```bash
docker volume create promdata
```

**Expected output:**
```
promdata
```

**Verify:**
```bash
docker volume ls
```
You should see `promdata` in the list.

---

## Step 2 — Run Prometheus

This single command starts Prometheus. Each flag is explained below.

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v "$(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
  -v promdata:/prometheus \
  prom/prometheus:v3.12.0 \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus
```

> **Prometheus 3.x note:** Older 2.x guides append `--web.console.libraries` and
> `--web.console.templates` here. Prometheus 3.x removed the bundled web consoles,
> so those flags now point at nothing and the container exits on startup. Leave them out.

**What each flag does:**

| Flag | Meaning |
|------|---------|
| `-d` | Detached mode — runs in the background so your terminal stays free |
| `--name prometheus` | Gives the container a friendly name instead of a random one |
| `-p 9090:9090` | Maps port 9090 on your machine to port 9090 inside the container |
| `-v $(pwd)/prometheus.yml:...` | Mounts the config file from your current directory into the container |
| `:ro` | Read-only — the container can read the config but not modify it |
| `-v promdata:/prometheus` | Mounts the named volume at the path where Prometheus stores data |
| `prom/prometheus:v3.12.0` | The Docker image to use (official Prometheus, pinned version) |
| `--config.file=...` | Tells Prometheus where its config file is (inside the container) |
| `--storage.tsdb.path=...` | Where to write the time-series database |

> **Windows / WSL2 note:** The `$(pwd)` substitution works in WSL2 bash. If you are
> running from PowerShell directly, replace `$(pwd)` with the full Windows path
> using forward slashes: `C:/Users/yourname/path/to/prometheus-setup`.

**Expected output:** A long container ID hash, e.g.:
```
a3f7c2e1b4d5...
```

---

## Step 3 — Check that Prometheus started

```bash
docker ps
```

**Expected output** (abbreviated):
```
CONTAINER ID   IMAGE                       COMMAND                  PORTS                    NAMES
a3f7c2e1b4d5   prom/prometheus:v3.12.0    "/bin/prometheus ..."    0.0.0.0:9090->9090/tcp   prometheus
```

If the container is not in the list, it may have crashed — see the troubleshooting step below.

---

## Step 4 — View the logs

```bash
docker logs prometheus
```

**Expected output** (last few lines should look like):
```
ts=2024-01-01T00:00:00.000Z caller=main.go msg="Server is ready to receive web requests."
```

If you see an error, check `docs/troubleshooting.md`.

---

## Step 5 — Verify in the browser

Open **http://localhost:9090** in your browser.

You should see the Prometheus web UI — a dark/light header with a search bar labeled "Expression".

**Run your first PromQL query:**

1. In the search bar, type `up` and press **Execute** (or Enter).
2. Switch to the **Table** tab.

**Expected result:**
```
up{instance="localhost:9090", job="prometheus"}   1
```

**What does this mean?**
- `up` is a built-in metric — it equals `1` if the target is reachable, `0` if not.
- You're seeing Prometheus reporting that it can reach itself (`localhost:9090`).
- This confirms the scrape job in `prometheus.yml` is working.

---

## Step 6 — Stop and remove the container (cleanup)

When you are done experimenting:

```bash
# Stop the container (data in the volume is preserved)
docker stop prometheus

# Remove the container (the named volume 'promdata' still exists)
docker rm prometheus
```

To also delete the volume (all Prometheus data):
```bash
docker volume rm promdata
```

> **Tip:** You don't need to remove the container before moving to `02-docker-compose.md`.
> Compose will fail if a container named `prometheus` already exists. Run the stop/rm
> commands above first, or just do `docker rm -f prometheus`.

---

## Troubleshooting

**Container is not in `docker ps`:**
```bash
docker ps -a   # shows stopped containers too
docker logs prometheus
```
Look for an error message. Common causes: port 9090 already in use, bad config file path.

**Port 9090 already in use:**
```bash
# Find what's using it:
sudo lsof -i :9090      # Linux / WSL2
netstat -ano | findstr 9090   # Windows PowerShell
```
Either stop the other process or change the host port: `-p 9091:9090`.

**Config file not found:**
Make sure you are running the `docker run` command from the `prometheus-setup/` directory
(where `prometheus.yml` lives). The `$(pwd)` path must resolve to that directory.

---

**Next:** Read `02-docker-compose.md` to see how this entire setup collapses into one file and one command.
