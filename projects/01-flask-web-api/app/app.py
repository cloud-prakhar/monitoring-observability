"""
Flask Web API — Project 1
Exposes a small REST API and records Prometheus metrics for every request.

Metrics produced:
  http_requests_total          Counter   — total requests by method, endpoint, status_code
  http_request_duration_seconds Histogram — response time by method, endpoint
  active_requests               Gauge     — requests currently in-flight

Routes:
  GET /           → simple health/hello response
  GET /users      → returns a list of fake users
  GET /users/<id> → returns one fake user (404 if id > 100)
  GET /slow       → sleeps 300ms–1.2s to simulate a slow endpoint
  GET /error      → returns HTTP 500 roughly 40% of the time
  GET /metrics    → Prometheus scrapes this
"""

import random
import time

from flask import Flask, jsonify, request
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Number of requests currently being processed",
)

# ---------------------------------------------------------------------------
# Request instrumentation middleware
# ---------------------------------------------------------------------------

@app.before_request
def start_timer():
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()


@app.after_request
def record_metrics(response):
    # Skip recording metrics for the /metrics endpoint itself to avoid noise.
    if request.path != "/metrics":
        duration = time.time() - request.start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.path,
        ).observe(duration)
    ACTIVE_REQUESTS.dec()
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return jsonify({"service": "flask-web-api", "status": "ok"})


@app.route("/users")
def list_users():
    users = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
             for i in range(1, 6)]
    return jsonify({"users": users, "count": len(users)})


@app.route("/users/<int:user_id>")
def get_user(user_id):
    if user_id > 100:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"})


@app.route("/slow")
def slow_endpoint():
    """Simulates a slow database query or external API call."""
    delay = random.uniform(0.3, 1.2)
    time.sleep(delay)
    return jsonify({"message": "Slow response delivered", "delay_ms": round(delay * 1000)})


@app.route("/error")
def error_endpoint():
    """Returns HTTP 500 about 40% of the time. Use this to generate error-rate metrics."""
    if random.random() < 0.4:
        return jsonify({"error": "Simulated internal server error"}), 500
    return jsonify({"message": "Success"})


@app.route("/metrics")
def metrics():
    """Prometheus scrapes this endpoint every 15 seconds (configured in infra/prometheus.yml)."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Flask Web API running on http://0.0.0.0:8081")
    print("Metrics available at http://0.0.0.0:8081/metrics")
    app.run(host="0.0.0.0", port=8081, debug=False)
