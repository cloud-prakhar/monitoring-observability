"""
Job Processor — Project 2
Simulates a background task queue: jobs are submitted via HTTP, processed by a
worker thread, and tracked with Prometheus metrics.

Metrics produced:
  jobs_submitted_total       Counter  — jobs submitted (increments on POST /jobs)
  jobs_completed_total       Counter  — jobs finished successfully
  jobs_failed_total          Counter  — jobs that failed (15% failure rate)
  job_duration_seconds       Histogram — how long each job took to process
  job_queue_depth            Gauge    — jobs currently waiting (not yet picked up)
  jobs_currently_processing  Gauge    — jobs being actively processed right now

Routes:
  POST /jobs          → submit a new job, returns job_id
  GET  /jobs/<id>     → check job status (queued / processing / completed / failed)
  GET  /stats         → summary counts
  GET  /metrics       → Prometheus scrapes this
"""

import queue
import random
import threading
import time
import uuid

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
# In-memory job store and queue
# ---------------------------------------------------------------------------

job_store = {}          # job_id → {id, payload, status, ...}
task_queue = queue.Queue()

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

JOBS_SUBMITTED = Counter(
    "jobs_submitted_total",
    "Total number of jobs submitted",
)

JOBS_COMPLETED = Counter(
    "jobs_completed_total",
    "Total number of jobs completed successfully",
)

JOBS_FAILED = Counter(
    "jobs_failed_total",
    "Total number of jobs that failed",
)

JOB_DURATION = Histogram(
    "job_duration_seconds",
    "Time taken to process a single job",
    buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
)

QUEUE_DEPTH = Gauge(
    "job_queue_depth",
    "Number of jobs waiting in the queue (not yet picked up by the worker)",
)

JOBS_PROCESSING = Gauge(
    "jobs_currently_processing",
    "Number of jobs actively being processed right now",
)

# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def worker():
    """Runs in a background thread. Picks jobs off the queue and processes them."""
    while True:
        job_id = task_queue.get()

        job_store[job_id]["status"] = "processing"
        QUEUE_DEPTH.dec()
        JOBS_PROCESSING.inc()

        # Simulate variable-length processing (0.5s to 5s).
        processing_time = random.uniform(0.5, 5.0)
        start = time.time()
        time.sleep(processing_time)

        # Introduce a 15% failure rate so we can observe it on the dashboard.
        if random.random() < 0.15:
            job_store[job_id]["status"] = "failed"
            job_store[job_id]["error"] = "Simulated processing error"
            JOBS_FAILED.inc()
        else:
            job_store[job_id]["status"] = "completed"
            job_store[job_id]["result"] = f"Processed in {processing_time:.2f}s"
            JOBS_COMPLETED.inc()

        JOB_DURATION.observe(time.time() - start)
        JOBS_PROCESSING.dec()
        task_queue.task_done()


# Start a single background worker thread (daemon=True so it exits when the app exits).
threading.Thread(target=worker, daemon=True).start()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/jobs", methods=["POST"])
def submit_job():
    """Submit a new job. Returns a job_id you can poll with GET /jobs/<id>."""
    data = request.get_json(silent=True) or {}
    job_id = str(uuid.uuid4())[:8]

    job_store[job_id] = {
        "id": job_id,
        "payload": data.get("payload", "default-task"),
        "status": "queued",
        "submitted_at": time.time(),
    }

    task_queue.put(job_id)
    JOBS_SUBMITTED.inc()
    QUEUE_DEPTH.inc()

    return jsonify({"job_id": job_id, "status": "queued"}), 202


@app.route("/jobs/<job_id>")
def get_job(job_id):
    """Check the status of a previously submitted job."""
    job = job_store.get(job_id)
    if not job:
        return jsonify({"error": f"Job '{job_id}' not found"}), 404
    return jsonify(job)


@app.route("/stats")
def stats():
    """Summary counts — useful for a quick sanity check."""
    counts = {}
    for job in job_store.values():
        counts[job["status"]] = counts.get(job["status"], 0) + 1
    return jsonify({"total_jobs": len(job_store), "by_status": counts})


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Job Processor running on http://0.0.0.0:8082")
    print("Submit jobs:  POST http://0.0.0.0:8082/jobs")
    print("Metrics:      http://0.0.0.0:8082/metrics")
    app.run(host="0.0.0.0", port=8082, debug=False)
