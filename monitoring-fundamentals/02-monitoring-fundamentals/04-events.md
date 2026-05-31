# Events

> Events are significant occurrences that you want to record and overlay on your monitoring.

---

## What is an Event?

An event is a **noteworthy occurrence** at a specific point in time that provides context for your metrics.

Examples:
- Deployment of version 2.1.0
- Database migration ran
- Traffic spike from marketing campaign
- Configuration change
- Kubernetes node restart
- Security incident

---

## Events vs Logs

| | Events | Logs |
|--|--------|------|
| Volume | Low (significant occurrences) | High (every application line) |
| Purpose | Context for graphs | Debugging details |
| Stored in | Grafana annotations, or Prometheus ALERTS metric | Loki, ELK |
| Queried | Overlaid on dashboards | Searched |

---

## Events as Grafana Annotations

The most common use: overlay deployment events on graphs to see if a deployment caused a metric change.

```bash
# Add annotation from CI/CD pipeline (after deployment)
curl -X POST http://admin:password@grafana:3000/api/annotations \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Deployed v2.1.0 to production",
    "tags": ["deployment", "production", "v2.1.0"],
    "time": '$(date +%s000)',
    "timeEnd": '$(date +%s000)'
  }'
```

In Grafana, this appears as a vertical line on all dashboards, making it trivial to see "did error rate change after this deployment?"

---

## Kubernetes Events as Prometheus Metrics

Kubernetes events (pod OOMKilled, node NotReady, etc.) can be converted to Prometheus metrics:

```promql
# Kubernetes warning events (signals problems)
count by (reason, namespace) (kube_event_count{type="Warning"} > 0)
```

---

## Key Takeaways

- ✅ Events mark significant occurrences (deployments, incidents, changes)
- ✅ In Grafana, events become annotations — visual markers on time series graphs
- ✅ Correlating events with metrics is the fastest way to find "what changed?"
- ✅ Always annotate deployments — it makes debugging dramatically faster

---

[← Traces](03-traces.md) | [Next: Dashboards →](05-dashboards.md)
