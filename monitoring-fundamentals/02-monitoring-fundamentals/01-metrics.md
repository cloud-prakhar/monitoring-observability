# Metrics

> The primary data type in Prometheus. Understanding metrics deeply makes everything else easier.

---

## What is a Metric?

A **metric** is a numerical measurement of something, recorded at a point in time.

```
Metric name:  http_requests_total
Value:        15,234
Timestamp:    2024-01-15 14:32:00 UTC
Labels:       {method="GET", path="/api/users", status="200"}
```

Metrics answer questions like:
- How many requests per second is this service handling?
- What percentage of requests are failing?
- How much memory is being used right now?
- How has CPU usage changed over the last 24 hours?

---

## The Four Prometheus Metric Types

### 1. Counter

A **counter** is a value that only goes up (or resets to zero on restart).

**Use for:** Counting things — requests, errors, bytes sent, tasks completed

```
http_requests_total{method="GET"} = 15,234
http_requests_total{method="POST"} = 4,891
```

**Important:** You never query the raw counter value. You query the **rate of change**.

```promql
# Wrong: raw counter value (meaningless)
http_requests_total

# Right: requests per second over last 5 minutes
rate(http_requests_total[5m])
```

**Why it only goes up:** If you're counting "total requests ever handled," that number should never decrease. If it does, it means the service restarted (and the counter reset to 0).

---

### 2. Gauge

A **gauge** is a value that can go up and down.

**Use for:** Current state — memory usage, CPU %, number of active connections, temperature, queue length

```
node_memory_MemAvailable_bytes = 4,294,967,296  (4 GB available)
node_cpu_usage_ratio = 0.45  (45% CPU)
active_connections = 234
```

**Query directly** (no rate needed):

```promql
# Current available memory in GB
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024

# Alert when less than 500MB available
node_memory_MemAvailable_bytes < 524288000
```

---

### 3. Histogram

A **histogram** samples observations and puts them into configurable buckets. It tracks:
- The count of observations in each bucket (`_bucket`)
- The sum of all observed values (`_sum`)
- The total count of observations (`_count`)

**Use for:** Measuring distributions — request duration, response size

```
# How long did HTTP requests take?
http_request_duration_seconds_bucket{le="0.1"}  = 8,234   (under 100ms)
http_request_duration_seconds_bucket{le="0.5"}  = 12,891  (under 500ms)
http_request_duration_seconds_bucket{le="1.0"}  = 14,100  (under 1s)
http_request_duration_seconds_bucket{le="+Inf"} = 15,234  (total)
http_request_duration_seconds_sum               = 3847.2   (total seconds)
http_request_duration_seconds_count             = 15,234   (total requests)
```

**Key use — Calculating percentiles:**

```promql
# 99th percentile response time over last 5 minutes
histogram_quantile(0.99, 
  rate(http_request_duration_seconds_bucket[5m]))

# 50th percentile (median)
histogram_quantile(0.50,
  rate(http_request_duration_seconds_bucket[5m]))
```

---

### 4. Summary

A **summary** is similar to a histogram but calculates quantiles client-side (in the application).

```
# Pre-calculated quantiles
http_request_duration_seconds{quantile="0.5"}  = 0.045
http_request_duration_seconds{quantile="0.9"}  = 0.120
http_request_duration_seconds{quantile="0.99"} = 0.850
http_request_duration_seconds_sum              = 3847.2
http_request_duration_seconds_count            = 15,234
```

**Histogram vs Summary:**

| | Histogram | Summary |
|--|-----------|---------|
| Percentile calculation | At query time (PromQL) | At collection time (client) |
| Aggregatable across instances | ✅ Yes | ❌ No |
| Memory cost | Lower (server) | Higher (client) |
| Preferred? | ✅ Usually | Only if percentile accuracy critical |

---

## Metric Naming Conventions

Prometheus follows specific naming conventions:

```
<namespace>_<subsystem>_<name>_<unit>

Examples:
http_requests_total              # total = counter
http_request_duration_seconds    # seconds = unit
node_memory_MemAvailable_bytes   # bytes = unit
process_cpu_seconds_total        # total = counter
go_goroutines                    # current count = gauge
```

**Rules:**
- Use lowercase with underscores
- Include units (seconds, bytes, etc.)
- End counters with `_total`
- Don't use metric name to encode label info

---

## Labels: The Power of Multi-Dimensional Metrics

Labels are key-value pairs attached to metrics that allow filtering and grouping.

```
http_requests_total{
  method="GET",
  path="/api/users",
  status="200",
  service="user-api",
  region="us-east-1"
}
```

**Without labels** (old way, Nagios-style):
- `http_requests_total_GET_api_users_200_user-api_us-east-1`
- You'd need thousands of metrics, one per combination

**With labels** (Prometheus way):
- One metric name
- Filter and group at query time

```promql
# All errors, by service
sum by (service) (rate(http_requests_total{status=~"5.."}[5m]))

# Just errors for user-api in us-east-1
rate(http_requests_total{service="user-api", region="us-east-1", status=~"5.."}[5m])
```

---

## Cardinality: The One Thing That Can Break Prometheus

**Cardinality** is the number of unique time series in Prometheus. Too many can cause memory issues.

**Low cardinality (good):**
```
http_requests_total{method="GET", status="200"} = 1 time series
http_requests_total{method="POST", status="200"} = 1 time series
http_requests_total{method="GET", status="500"} = 1 time series
# Total: 3 time series (3 = 2 methods × ~2 status codes used)
```

**High cardinality (dangerous):**
```
# DON'T DO THIS:
http_requests_total{user_id="user-12345"} = 1 per user
# If you have 10 million users: 10 million time series
```

**Warning signs of cardinality explosion:**
- Label values that are UUIDs, user IDs, or session IDs
- Unbounded label values (anything user-provided)
- Timestamp values as labels

---

## How Prometheus Stores Metrics (TSDB Overview)

Prometheus uses its own **Time Series Database (TSDB)**:

```
Data structure: (metric_name + labels) → [(timestamp, value), (timestamp, value), ...]

Example:
"http_requests_total{method='GET',status='200'}" → [
  (1705329120, 15234),
  (1705329135, 15241),  ← 15 seconds later, 7 more requests
  (1705329150, 15249),  ← another 8 requests
  ...
]
```

Data is stored in **chunks** of 2 hours in memory, then compressed to disk. Default retention: 15 days.

---

## Real-World Metric Examples

### Linux Server Metrics (Node Exporter)
```
node_cpu_seconds_total{cpu="0", mode="user"}
node_memory_MemAvailable_bytes
node_disk_read_bytes_total{device="sda"}
node_network_receive_bytes_total{device="eth0"}
node_filesystem_avail_bytes{mountpoint="/"}
```

### Kubernetes Metrics (kube-state-metrics)
```
kube_deployment_status_replicas_ready
kube_pod_container_resource_requests{resource="cpu"}
kube_node_status_condition{condition="Ready", status="true"}
```

### Application Metrics (custom, from your code)
```python
# Python example using prometheus_client
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('http_requests_total', 
                        'Total requests', 
                        ['method', 'endpoint', 'status'])

REQUEST_LATENCY = Histogram('http_request_duration_seconds',
                            'Request latency',
                            ['method', 'endpoint'],
                            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0])

# In your request handler:
REQUEST_COUNT.labels(method='GET', endpoint='/api/users', status='200').inc()
REQUEST_LATENCY.labels(method='GET', endpoint='/api/users').observe(0.045)
```

---

## Key Takeaways

- ✅ Metrics are numerical measurements at a point in time
- ✅ Prometheus has four types: Counter, Gauge, Histogram, Summary
- ✅ Labels make metrics multi-dimensional and powerful
- ✅ Watch out for cardinality explosion with high-cardinality labels
- ✅ Histograms are preferred over summaries for percentile calculations

---

[← Section Index](README.md) | [Next: Logs →](02-logs.md)
