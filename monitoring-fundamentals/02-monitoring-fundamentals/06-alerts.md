# Alerts

> Alerts are the automated voice that says "hey, look at this." Done well, they save you. Done poorly, they become noise you ignore.

---

## What is an Alert?

An alert is an **automated notification** triggered when a monitoring condition is met.

```
Condition: CPU usage > 90% for 10 minutes
Alert fires: "🔴 HighCPU on web-server-01: 94%"
Notification: Slack, PagerDuty, email
```

---

## The Alert Quality Test

Before creating any alert, answer these questions:

1. **Is it actionable?** Can a human DO something when this fires?
2. **Is it urgent?** Does it need attention in the next hour? (If not, it's not an alert — it's a report)
3. **Is it accurate?** Will it mostly fire when something is genuinely wrong?
4. **Is there a runbook?** Does the alert tell you what to do?

---

## Alert Anatomy (Prometheus)

```yaml
- alert: HighMemoryUsage        # Name
  expr: |                       # Condition
    (1 - node_memory_MemAvailable_bytes 
         / node_memory_MemTotal_bytes) * 100 > 85
  for: 10m                      # Duration (prevent flapping)
  labels:
    severity: warning           # Routing label
    team: platform              # Team responsible
  annotations:
    summary: "Memory {{ $value | humanize }}% on {{ $labels.instance }}"
    description: "Memory has been above 85% for 10 minutes."
    runbook_url: "https://wiki.example.com/runbooks/high-memory"
```

---

## Alert Severity Levels

| Level | Meaning | Response |
|-------|---------|---------|
| **Critical** | Service is down or SLA will be violated | Page immediately, 24/7 |
| **Warning** | Degraded performance, will become critical | Check during business hours |
| **Info** | Informational, no action required | Ticket or no action |

**Rule of thumb:** If it doesn't need a human to act in the next 30 minutes, it's not critical.

---

## Common Alert Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Threshold too low | Alerts too often, creates fatigue | Start high, tune down |
| No `for` clause | Fires on transient spikes | Add `for: 5m` |
| No runbook | Engineers don't know what to do | Always include runbook_url |
| Alert on causes, not symptoms | CPU high ≠ users impacted | Alert on error rate, not CPU |
| Too many critical alerts | Real criticals get ignored | Be selective with critical severity |

---

## Good Alerts vs Bad Alerts

```yaml
# ❌ BAD: Too noisy, no context
- alert: CPUHigh
  expr: cpu_usage > 80
  # No 'for', fires immediately
  # No context about what to do

# ✅ GOOD: Actionable, contextualized
- alert: CPUHighSustained
  expr: cpu_usage > 90
  for: 15m   # Must be sustained
  labels:
    severity: warning
  annotations:
    summary: "CPU {{ $value }}% on {{ $labels.instance }}"
    runbook_url: "https://wiki/runbooks/cpu"
    dashboard_url: "https://grafana/d/cpu-dash?var-instance={{ $labels.instance }}"
```

---

## Key Takeaways

- ✅ Alerts must be actionable, accurate, and have runbooks
- ✅ Use the `for` clause to avoid transient spike false positives
- ✅ Alert on symptoms (error rate, latency) not causes (CPU usage)
- ✅ Reserve "critical/page" severity for genuine user impact
- ✅ Alert fatigue from too many alerts is dangerous — teams stop responding

---

[← Dashboards](05-dashboards.md) | [Next: SLIs, SLOs, SLAs →](07-sli-slo-sla.md)
