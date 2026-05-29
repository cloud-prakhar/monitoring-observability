"""
Cache Service — Project 3
An in-memory key-value cache with TTL support (like a stripped-down Redis).
A background thread evicts expired keys automatically.

Metrics produced:
  cache_hits_total            Counter  — GET requests that found a valid key
  cache_misses_total          Counter  — GET requests that found nothing (or expired)
  cache_operations_total      Counter  — every operation, labelled by type
  cache_keys_total            Gauge    — keys currently stored in the cache
  cache_evictions_total       Counter  — keys removed by the TTL eviction thread
  cache_operation_duration_s  Histogram — latency per operation type

Routes:
  GET    /cache/<key>         → read a value (hit or miss)
  POST   /cache               → store a value (with optional TTL in seconds)
  DELETE /cache/<key>         → remove a value
  GET    /stats               → current key count and a sample of keys
  GET    /metrics             → Prometheus scrapes this
"""

import threading
import time
import random

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
# In-memory store: { key: (value, expires_at_or_None) }
# ---------------------------------------------------------------------------

_cache: dict = {}
_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

CACHE_HITS = Counter(
    "cache_hits_total",
    "Cache GET requests that returned a valid value",
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Cache GET requests that found nothing or an expired key",
)

CACHE_OPERATIONS = Counter(
    "cache_operations_total",
    "All cache operations by type",
    ["operation"],           # set | get_hit | get_miss | get_expired | delete | delete_miss | evict
)

CACHE_KEYS = Gauge(
    "cache_keys_total",
    "Number of keys currently held in the cache",
)

CACHE_EVICTIONS = Counter(
    "cache_evictions_total",
    "Keys removed by the background TTL eviction thread",
)

OPERATION_DURATION = Histogram(
    "cache_operation_duration_seconds",
    "Time taken per cache operation",
    ["operation"],           # set | get | delete
    buckets=[0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01],
)

# ---------------------------------------------------------------------------
# Background TTL eviction thread
# ---------------------------------------------------------------------------

def _evict_expired():
    """Runs every 5 seconds, removes keys whose TTL has passed."""
    while True:
        time.sleep(5)
        now = time.time()
        with _lock:
            expired_keys = [k for k, (_, exp) in _cache.items() if exp is not None and exp < now]
            for key in expired_keys:
                del _cache[key]
                CACHE_KEYS.dec()
                CACHE_EVICTIONS.inc()
                CACHE_OPERATIONS.labels(operation="evict").inc()


threading.Thread(target=_evict_expired, daemon=True).start()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/cache/<key>", methods=["GET"])
def get_key(key):
    start = time.time()
    with _lock:
        entry = _cache.get(key)

        if entry is None:
            CACHE_MISSES.inc()
            CACHE_OPERATIONS.labels(operation="get_miss").inc()
            OPERATION_DURATION.labels(operation="get").observe(time.time() - start)
            return jsonify({"error": f"Key '{key}' not found"}), 404

        value, expires_at = entry

        if expires_at is not None and time.time() > expires_at:
            del _cache[key]
            CACHE_KEYS.dec()
            CACHE_MISSES.inc()
            CACHE_EVICTIONS.inc()
            CACHE_OPERATIONS.labels(operation="get_expired").inc()
            OPERATION_DURATION.labels(operation="get").observe(time.time() - start)
            return jsonify({"error": f"Key '{key}' has expired"}), 404

        CACHE_HITS.inc()
        CACHE_OPERATIONS.labels(operation="get_hit").inc()
        OPERATION_DURATION.labels(operation="get").observe(time.time() - start)
        return jsonify({"key": key, "value": value})


@app.route("/cache", methods=["POST"])
def set_key():
    start = time.time()
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    value = data.get("value")
    ttl = data.get("ttl")           # optional: seconds until expiry, e.g. 30

    if not key or value is None:
        return jsonify({"error": "'key' and 'value' are required"}), 400

    expires_at = time.time() + float(ttl) if ttl else None

    with _lock:
        is_new_key = key not in _cache
        _cache[key] = (value, expires_at)
        if is_new_key:
            CACHE_KEYS.inc()

    CACHE_OPERATIONS.labels(operation="set").inc()
    OPERATION_DURATION.labels(operation="set").observe(time.time() - start)
    return jsonify({"key": key, "stored": True, "ttl_seconds": ttl})


@app.route("/cache/<key>", methods=["DELETE"])
def delete_key(key):
    start = time.time()
    with _lock:
        if key in _cache:
            del _cache[key]
            CACHE_KEYS.dec()
            CACHE_OPERATIONS.labels(operation="delete").inc()
            OPERATION_DURATION.labels(operation="delete").observe(time.time() - start)
            return jsonify({"key": key, "deleted": True})

    CACHE_OPERATIONS.labels(operation="delete_miss").inc()
    OPERATION_DURATION.labels(operation="delete").observe(time.time() - start)
    return jsonify({"error": f"Key '{key}' not found"}), 404


@app.route("/stats")
def stats():
    with _lock:
        keys_snapshot = list(_cache.keys())[:20]
        return jsonify({
            "total_keys": len(_cache),
            "sample_keys": keys_snapshot,
        })


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Cache Service running on http://0.0.0.0:8083")
    print("Set a key:    POST http://0.0.0.0:8083/cache")
    print("Get a key:    GET  http://0.0.0.0:8083/cache/<key>")
    print("Metrics:      http://0.0.0.0:8083/metrics")
    app.run(host="0.0.0.0", port=8083, debug=False)
