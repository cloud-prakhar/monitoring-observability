# Logs

> Logs are the narrative of what happened. Metrics tell you something is wrong; logs tell you why.

---

## What is a Log?

A log is a **timestamped record of a discrete event** in your system.

```
2024-01-15 14:32:01 ERROR [user-service] Failed to authenticate user
  user_id=12345
  ip=192.168.1.100
  error="invalid token: token expired at 2024-01-15T14:30:00Z"
  trace_id=abc123def456
```

Unlike metrics (numbers over time), logs contain **context** — the who, what, and why.

---

## Log Levels

```
DEBUG   → Detailed diagnostic information (dev only)
INFO    → Normal application events
WARN    → Unexpected but handled situations
ERROR   → Failures that need attention
FATAL   → Critical failures causing application exit
```

---

## Structured vs Unstructured Logs

**Unstructured (old way):**
```
2024-01-15 14:32:01 User 12345 login failed: bad password from 192.168.1.100
```

**Structured JSON (modern standard):**
```json
{
  "timestamp": "2024-01-15T14:32:01Z",
  "level": "ERROR",
  "message": "Login failed",
  "user_id": 12345,
  "ip": "192.168.1.100",
  "reason": "bad_password",
  "trace_id": "abc123def456"
}
```

**Why structured is better:**
- Machine-parseable (Loki, Elasticsearch can index fields)
- Filter by any field: `level=ERROR AND user_id=12345`
- Correlate with traces: `trace_id=abc123def456`

---

## Logs in the Monitoring Stack

| Tool | Role |
|------|------|
| **Grafana Loki** | Log aggregation (Prometheus-style, label-based) |
| **Elasticsearch + Kibana** | Log search and analytics |
| **Splunk** | Enterprise log management + SIEM |
| **CloudWatch Logs** | AWS-native log aggregation |

This repo focuses on metrics (Prometheus). For logs, see the [Loki getting started guide](https://grafana.com/docs/loki/latest/get-started/).

---

## Key Takeaways

- ✅ Logs record discrete events with context (metrics record numbers over time)
- ✅ Structured logs (JSON) enable filtering and correlation
- ✅ Log levels (DEBUG, INFO, WARN, ERROR, FATAL) control verbosity
- ✅ Correlate logs with metrics using shared labels (trace_id, service, timestamp)

---

[← Metrics](01-metrics.md) | [Next: Traces →](03-traces.md)
