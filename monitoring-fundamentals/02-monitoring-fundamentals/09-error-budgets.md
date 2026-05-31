# Error Budgets

> The most powerful concept in SRE. Error budgets transform reliability from a constraint into a resource.

---

## What Is an Error Budget?

An error budget is **the amount of time or errors your service is allowed to have** based on your SLO.

```
SLO: 99.9% availability
Error budget: 100% - 99.9% = 0.1% of time allowed to be unavailable

In a 30-day month:
30 days × 24 hours × 60 minutes = 43,200 minutes
Error budget = 43,200 × 0.001 = 43.2 minutes
```

This means: You can have up to **43 minutes and 12 seconds** of downtime per month and still meet your SLO.

---

## Why Error Budgets Are Revolutionary

Before error budgets, reliability was a constant argument:

```
Engineering: "We need to deploy more features!"
Operations:  "No! We need stability! No deployments!"
```

Error budgets resolve this with math:

```
"We have 40 minutes of error budget remaining this month.
Our last deploy has historically caused 5-minute outages.
We can still make 8 more deploys this month before exhausting our budget.
Go ahead."
```

**Error budget = data-driven permission to take risk.**

---

## Error Budget Consumption

### Calculating Budget Remaining

```promql
# Error budget consumed (as fraction of monthly budget)
1 - (
  (
    sum(rate(http_requests_total{status!~"5.."}[30d]))
    /
    sum(rate(http_requests_total[30d]))
  ) - 0.999  # SLO target
) / 0.001    # Error budget (1 - SLO target)
```

### What Consumes Error Budget?

```
Planned downtime (maintenance windows)         → consumes budget
Unplanned outages                              → consumes budget
Performance degradation above SLO threshold    → consumes budget
Partial availability (some users affected)     → consumes budget proportionally
```

### What Doesn't Consume Error Budget?

```
Downtime due to customer errors                → excluded
Downtime due to force majeure                  → excluded  
Incidents within SLO threshold                 → not counted
```

---

## Error Budget Policy

The most important document in an SRE organization is the **Error Budget Policy** — what happens when the budget is nearly exhausted or fully spent.

### Example Error Budget Policy

```
Error Budget Policy: User API Service
Last Updated: 2024-01-15
Owner: Platform Team

Budget Thresholds and Actions:

┌─────────────────┬─────────────────────────────────────────────────┐
│ Budget Remaining│ Required Action                                  │
├─────────────────┼─────────────────────────────────────────────────┤
│ > 50%           │ Full deployment velocity. All planned changes OK │
├─────────────────┼─────────────────────────────────────────────────┤
│ 25% - 50%       │ No risky deployments. All changes need review.   │
│                 │ Incident retrospective required for any incident │
├─────────────────┼─────────────────────────────────────────────────┤
│ 10% - 25%       │ No new feature deployments.                      │
│                 │ Bug fixes and security patches only.             │
│                 │ Team must present reliability improvement plan.  │
├─────────────────┼─────────────────────────────────────────────────┤
│ 0% - 10%        │ Freeze all non-critical deployments.             │
│                 │ Engineering team focuses on reliability work.    │
│                 │ Weekly SLO review with leadership.               │
├─────────────────┼─────────────────────────────────────────────────┤
│ Exhausted (0%)  │ Feature freeze until next month's budget resets. │
│                 │ Mandatory postmortem for root cause.             │
│                 │ Reliability sprint: no feature work.             │
└─────────────────┴─────────────────────────────────────────────────┘
```

---

## Error Budget Burn Rate

Burn rate is how fast you're consuming your error budget relative to the expected rate.

```
Expected burn rate: 1x
  → You'll exactly exhaust your budget at the end of the window

Burn rate 2x:
  → You'll exhaust budget in half the time

Burn rate 14.4x:
  → At this rate, budget exhausted in 2 hours (needs immediate action)
```

### Burn Rate Alerts (Google's Method)

Google SRE book recommends multi-window, multi-burn-rate alerts:

```yaml
groups:
  - name: error-budget
    rules:
      
      # Tier 1: CRITICAL — Budget exhausted in < 1 hour
      # High burn rate over short window = urgent action needed
      - alert: ErrorBudgetBurnCritical
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m])
            / rate(http_requests_total[5m])
          ) > (0.001 * 14.4)
          AND
          (
            rate(http_requests_total{status=~"5.."}[1h])
            / rate(http_requests_total[1h])
          ) > (0.001 * 14.4)
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Error budget will be exhausted in ~1 hour"
          action: "Page on-call immediately"

      # Tier 2: WARNING — Budget exhausted in < 1 day
      - alert: ErrorBudgetBurnHigh
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[30m])
            / rate(http_requests_total[30m])
          ) > (0.001 * 6)
          AND
          (
            rate(http_requests_total{status=~"5.."}[6h])
            / rate(http_requests_total[6h])
          ) > (0.001 * 6)
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Error budget will be exhausted in ~1 day"
          action: "Investigate and slow down deployments"

      # Tier 3: INFO — Budget exhausted in < 3 days
      - alert: ErrorBudgetBurnMedium
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[2h])
            / rate(http_requests_total[2h])
          ) > (0.001 * 3)
          AND
          (
            rate(http_requests_total{status=~"5.."}[24h])
            / rate(http_requests_total[24h])
          ) > (0.001 * 3)
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "Error budget will be exhausted in ~3 days"
          action: "Review recent changes and deployment frequency"
```

---

## Error Budget Grafana Dashboard

### Required Panels

```
Panel 1: Error Budget Remaining (Stat)
  Current value: 72% remaining
  Color: Green > 50%, Orange 10-50%, Red < 10%

Panel 2: Budget Burn Rate (Gauge)
  Current burn rate: 1.2x
  Normal: 1x, Warning: 3x, Critical: 6x+

Panel 3: Budget Remaining Over Time (Graph)
  Shows the "burn down" of budget over the month
  Projection line showing when budget will be exhausted

Panel 4: Top Error Sources (Table)
  Which endpoints / operations are consuming budget
  Ranked by error contribution

Panel 5: Deployment Timeline (Annotations)
  Shows when deployments happened relative to error spikes
```

---

## Error Budget in Practice: Real Scenarios

### Scenario 1: Healthy Month

```
Week 1: 0 incidents. Budget: 100% → 95% (normal noise)
Week 2: Brief 5-min outage. Budget: 95% → 83%
Week 3: 0 incidents. Budget: 83% → 78%
Week 4: 0 incidents. Budget: 78% → 72%

Month end: 72% remaining
Action: Team can continue at full deployment velocity
Learning: Service is stable; consider tightening SLO next month
```

### Scenario 2: Burning Budget Fast

```
Week 1: Major deployment causes 2-hour outage. Budget: 100% → 8%
Week 2 onwards: Budget policy kicks in
  - Feature deployment freeze
  - Team focuses on reliability: adding circuit breakers,
    improving deployment safety, adding canary analysis
  - Budget remains at 8% (no more incidents)
    
Month end: 8% remaining
Next month: Budget resets to 100%
Action: Reliability sprint completed, deployment process improved
Learning: The budget exhaustion forced investment in reliability
```

### Scenario 3: Too Much Budget (Overcautious)

```
Every month: 90-95% budget remaining
Problem: Team is too conservative — not deploying enough
Insight: We're "spending" too much reliability budget on caution
         We could deploy more and still meet SLO

Action: Team increases deployment frequency
        Better utilizes innovation potential
        Reliability stays well within SLO
```

**Key insight:** Consistently remaining at 90%+ budget means your SLO is too loose or your team is too cautious.

---

## Error Budget and Culture

Error budgets only work if the entire organization understands and respects them.

**Required culture shift:**

| Old Mindset | Error Budget Mindset |
|-------------|---------------------|
| "Reliability and velocity are opposed" | "Budget tells us how much velocity we can take" |
| "Ops says no to all deploys after incident" | "Budget determines deployment pace, not feelings" |
| "Engineering maximizes features" | "Engineering manages budget as a resource" |
| "SRE police rate of change" | "Budget is shared responsibility" |

---

## Key Takeaways

- ✅ Error budget = (1 - SLO target) of time/requests you can "afford" to lose
- ✅ Error budgets convert "reliability vs velocity" from a fight into a negotiation
- ✅ Error budget policy defines what happens at different burn levels
- ✅ Burn rate alerts catch problems before budget is exhausted
- ✅ Exhausting budget should trigger reliability-focused sprints, not blame

---

[← MTTR & MTTD](08-mttr-mttd.md) | [Next Section: Tool Landscape →](../03-tool-landscape/README.md)
