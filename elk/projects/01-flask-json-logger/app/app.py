"""
Flask JSON Logger — ELK Project 1

A small Flask app that writes STRUCTURED JSON logs (one JSON object per line) to a log file.
Because the logs are already clean JSON, they can go straight to Elasticsearch via Filebeat —
no Logstash parsing needed. This is "Path A" from the fundamentals.

    app.py  ──writes JSON──▶  /var/log/app/app.log  ──Filebeat──▶  Elasticsearch  ──▶  Kibana

Each log line looks like:
    {"@timestamp": "...", "level": "INFO", "message": "order placed",
     "service": "flask-json-logger", "method": "GET", "path": "/order",
     "status": 200, "latency_ms": 42, "user": "user7", "request_id": "a1b2c3"}

Routes:
  GET /         → health check (logs INFO)
  GET /login    → succeeds ~80% of the time (logs INFO on success, WARNING on failure)
  GET /order    → places an order (logs INFO with an amount + item)
  GET /error    → fails ~50% of the time (logs ERROR with a stack-trace-style message)
  GET /health   → returns app status without logging noise
"""

import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

LOG_FILE = os.environ.get("LOG_FILE", "/var/log/app/app.log")
SERVICE = "flask-json-logger"

# ---------------------------------------------------------------------------
# JSON logging setup
# ---------------------------------------------------------------------------
# We write one JSON object per line. Filebeat reads each line, decodes the JSON,
# and ships the fields to Elasticsearch as a document. No Logstash required.


class JsonFormatter(logging.Formatter):
    """Turns a log record into a single line of JSON with consistent fields."""

    def format(self, record):
        log = {
            # ISO-8601 UTC time. Filebeat is told to use this as the event time (@timestamp).
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": SERVICE,
        }
        # Attach any structured fields passed via logger.info(..., extra={"fields": {...}})
        if hasattr(record, "fields"):
            log.update(record.fields)
        return json.dumps(log)


def build_logger():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logger = logging.getLogger(SERVICE)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    # Also echo to the console so `docker logs` shows activity.
    console = logging.StreamHandler()
    console.setFormatter(JsonFormatter())
    logger.addHandler(console)
    return logger


log = build_logger()
app = Flask(__name__)


def log_event(level, message, **fields):
    """Helper: log a message plus arbitrary structured fields."""
    fields.setdefault("request_id", uuid.uuid4().hex[:6])
    log.log(getattr(logging, level), message, extra={"fields": fields})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    log_event("INFO", "home page served", method="GET", path="/", status=200)
    return jsonify({"service": SERVICE, "status": "ok"})


@app.route("/login")
def login():
    user = f"user{random.randint(1, 20)}"
    start = time.time()
    success = random.random() < 0.8
    latency = round((time.time() - start) * 1000 + random.uniform(5, 60), 1)
    if success:
        log_event("INFO", "login succeeded", method="GET", path="/login",
                  status=200, user=user, latency_ms=latency)
        return jsonify({"user": user, "login": "ok"})
    log_event("WARNING", "login failed: bad password", method="GET", path="/login",
              status=401, user=user, latency_ms=latency)
    return jsonify({"user": user, "login": "failed"}), 401


@app.route("/order")
def order():
    user = f"user{random.randint(1, 20)}"
    item = random.choice(["book", "laptop", "coffee", "headphones", "monitor"])
    amount = round(random.uniform(5, 500), 2)
    latency = round(random.uniform(20, 200), 1)
    log_event("INFO", "order placed", method="GET", path="/order", status=200,
              user=user, item=item, amount=amount, latency_ms=latency)
    return jsonify({"user": user, "item": item, "amount": amount})


@app.route("/error")
def error():
    if random.random() < 0.5:
        log_event("ERROR", "unhandled exception: database connection timeout",
                  method="GET", path="/error", status=500,
                  error="ConnectionTimeout", latency_ms=round(random.uniform(500, 2000), 1))
        return jsonify({"error": "internal server error"}), 500
    log_event("INFO", "request ok", method="GET", path="/error", status=200)
    return jsonify({"status": "ok"})


@app.route("/health")
def health():
    # No logging here — health checks would otherwise flood the logs.
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    log_event("INFO", "application starting", path="/", status=0)
    print(f"{SERVICE} running on http://0.0.0.0:8091  (logs → {LOG_FILE})")
    app.run(host="0.0.0.0", port=8091, debug=False)
