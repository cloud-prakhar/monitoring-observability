"""
Web Access Log Analyzer — ELK Project 2

Simulates a busy web server by continuously writing RAW access-log lines (the standard
"Apache combined" format) to a log file. These lines are just text — they are NOT structured —
so they must pass through Logstash, which parses them into fields. This is "Path B".

    app.py  ──writes raw lines──▶  access.log  ──Filebeat──▶  Logstash (grok ETL)  ──▶  Elasticsearch  ──▶  Kibana

A raw line looks like (one big string, no fields):
    192.168.1.42 - - [10/Oct/2024:14:32:01 +0000] "GET /checkout HTTP/1.1" 500 1024 "https://google.com" "Mozilla/5.0"

Logstash's grok filter (in elk/02-setup/config/pipeline/logstash.conf) turns that into:
    clientip=192.168.1.42  verb=GET  request=/checkout  response=500  bytes=1024  agent="Mozilla/5.0"

Routes:
  GET /        → status/info about the generator
  GET /stats   → how many lines have been written
  GET /hit     → manually write ONE random access-log line (handy for testing)

A background thread also writes a steady stream of random traffic so Kibana always has data.
"""

import os
import random
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify

LOG_FILE = os.environ.get("LOG_FILE", "/var/log/web/access.log")
SERVICE = "web-access-log-analyzer"

app = Flask(__name__)
_lines_written = 0
_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Fake-traffic ingredients
# ---------------------------------------------------------------------------
PATHS = [
    "/", "/home", "/products", "/products/42", "/cart", "/checkout",
    "/login", "/search?q=shoes", "/api/orders", "/static/app.css", "/favicon.ico",
]
METHODS = ["GET", "GET", "GET", "GET", "POST", "PUT", "DELETE"]   # weighted toward GET
# Status codes weighted toward success, with a realistic sprinkle of errors.
STATUSES = [200, 200, 200, 200, 200, 301, 304, 404, 404, 500, 503]
REFERRERS = ["https://google.com", "https://twitter.com", "-", "https://example.com/blog"]
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "curl/8.4.0",
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
]


def random_ip():
    return f"{random.randint(11, 220)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def make_log_line():
    """Build one Apache 'combined' format access-log line as a raw string."""
    now = datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S +0000")
    ip = random_ip()
    method = random.choice(METHODS)
    path = random.choice(PATHS)
    status = random.choice(STATUSES)
    size = random.randint(120, 5000)
    referrer = random.choice(REFERRERS)
    agent = random.choice(AGENTS)
    return (
        f'{ip} - - [{now}] "{method} {path} HTTP/1.1" '
        f'{status} {size} "{referrer}" "{agent}"'
    )


def write_line(line):
    global _lines_written
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    with _lock:
        _lines_written += 1


def traffic_generator():
    """Background thread: write a random access-log line every ~0.5–2 seconds."""
    while True:
        write_line(make_log_line())
        time.sleep(random.uniform(0.5, 2.0))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return jsonify({
        "service": SERVICE,
        "status": "ok",
        "writing_to": LOG_FILE,
        "note": "raw access logs are being generated; Logstash parses them into fields",
    })


@app.route("/stats")
def stats():
    with _lock:
        return jsonify({"lines_written": _lines_written, "log_file": LOG_FILE})


@app.route("/hit")
def hit():
    line = make_log_line()
    write_line(line)
    return jsonify({"wrote": line})


if __name__ == "__main__":
    threading.Thread(target=traffic_generator, daemon=True).start()
    print(f"{SERVICE} running on http://0.0.0.0:8092  (raw logs → {LOG_FILE})")
    app.run(host="0.0.0.0", port=8092, debug=False)
