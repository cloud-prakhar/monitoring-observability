# Connect Prometheus to Grafana (Linux)

At this point you have Prometheus running on port 9090 and Grafana on port 3000. This step
adds Prometheus as a data source inside Grafana so you can run queries and build dashboards.

The wiring is identical on every OS — the Grafana data source points at `http://localhost:9090`
because both run natively on the same host.

---

## Prerequisites

- Prometheus is running: `curl -s http://localhost:9090/-/healthy` returns `Prometheus Server is Healthy.`
- Grafana is running: `curl -s http://localhost:3000/api/health` returns `{"database": "ok", ...}`

---

## Step 1 — Add Prometheus as a data source

**Via the Grafana UI:**

1. Open **http://localhost:3000** and log in (`admin` / `admin`)
2. Click the hamburger menu (☰) → **Connections** → **Data sources**
3. Click **Add data source** → select **Prometheus**
4. Set the URL to:
   ```
   http://localhost:9090
   ```
5. Leave all other settings at their defaults
6. Click **Save & test**

Expected result: a green banner saying **"Successfully queried the Prometheus API."**

**Via the API (alternative — no browser needed):**

```bash
curl -s -u admin:admin \
  -X POST http://localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true
  }' | python3 -m json.tool
```

Expected output includes:
```json
{
    "message": "Datasource added",
    "name": "Prometheus"
}
```

---

## Step 2 — Verify with a test query

1. In Grafana, hamburger menu → **Explore**
2. Make sure the data source dropdown shows **Prometheus**
3. In the query box, type `up` and press Shift+Enter

You should see a result with value `1` for the `prometheus` job. This confirms Grafana can
query Prometheus.

---

## Step 3 — Import a project dashboard (optional)

The native project dashboards are standalone JSON files. To load one:

1. Hamburger menu → **Dashboards** → **New** → **Import**
2. Click **Upload dashboard JSON file**
3. Select one of:
   - `projects-native/04-system-monitor/dashboards/system-monitor.json`
   - `projects-native/05-url-health-checker/dashboards/url-health-checker.json`
   - `projects-native/07-linux-system-monitor/dashboards/linux-system-monitor.json`
4. Select **Prometheus** as the data source → **Import**

Panels show "No data" until the matching project is running and Prometheus is scraping it. Follow
each project's `CONNECT.md` to complete the wiring.

---

## Step 4 — Verify the complete chain

```bash
curl -s 'http://localhost:9090/api/v1/query?query=up' | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d['data']['result']:
    print(r['metric']['job'], '→', r['value'][1])
"
```

Expected output:
```
prometheus → 1
```

Once you start the native projects and uncomment their scrape jobs, the list grows:
```
prometheus → 1
system-monitor → 1
url-health-checker → 1
linux-system-monitor → 1
```

---

## Prometheus config location reminder

For the Linux native setup, the Prometheus config is at `/etc/prometheus/prometheus.yml`.
To add a new scrape target, edit that file and reload:

```bash
sudo nano /etc/prometheus/prometheus.yml
# ... uncomment the project block ...

curl -X POST http://localhost:9090/-/reload
```

This is the same `/-/reload` endpoint used in the Docker setup — `--web.enable-lifecycle` enables
it in both cases.

---

## Summary — what you have now

```
Linux host
├── prometheus  (port 9090)  — scraping itself
│     config: /etc/prometheus/prometheus.yml
│     data:   /var/lib/prometheus/
└── grafana     (port 3000)  — data source: http://localhost:9090
      config: /etc/grafana/grafana.ini
      data:   /var/lib/grafana/
```

Next: start the Python projects in `projects-native/` and follow their `CONNECT.md` to wire them
in. On real Linux you can run projects 04, 05, and 07.
