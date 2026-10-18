# ELK Queries — Searching Your Logs

> Once logs are in Elasticsearch, the payoff is **searching** them. There are two query languages
> you'll meet, and this page demonstrates both using the data from the two projects.

**Prerequisite:** have logs in Elasticsearch — run
[Project 1](../projects/01-flask-json-logger/CONNECT.md) and/or
[Project 2](../projects/02-web-access-log-analyzer/CONNECT.md) first.

---

## The two query languages (don't mix them up)

| | **KQL** (Kibana Query Language) | **Query DSL** (Elasticsearch JSON) |
|---|---|---|
| Where you type it | The **search bar** in Kibana → Discover | The **REST API** (`curl`, or Kibana Dev Tools) |
| Looks like | `level: "ERROR" and status >= 500` | A block of JSON with `query`, `bool`, `match`… |
| Best for | Quick interactive filtering | Automation, scripts, complex aggregations |
| Analogy | The simple search box on a website | The full advanced-search form, sent as JSON |

**Rule of thumb:** explore with **KQL** in the UI; automate with **Query DSL** via the API. They
search the same data — KQL is just a friendly shorthand.

---

# Part 1 — KQL (in Kibana → Discover)

Open **http://localhost:5601 → ☰ → Discover**, pick a Data View (`flask-logs` or `web-access`),
set the time range (top-right) to **Last 1 hour**, and type these in the search bar.

### Basics

| KQL | Meaning |
|-----|---------|
| `level: "ERROR"` | Field `level` exactly equals `ERROR` |
| `response: 404` | Numeric field equals 404 |
| `message: "login failed"` | Field contains this phrase |
| `*` | Everything (the default) |

### Comparisons (numbers & dates)

| KQL | Meaning |
|-----|---------|
| `response >= 500` | Server errors (Project 2) |
| `amount > 100` | Orders over 100 (Project 1) |
| `latency_ms > 500` | Slow requests |
| `response >= 400 and response < 500` | All client errors (4xx) |

### Combining with AND / OR / NOT

| KQL | Meaning |
|-----|---------|
| `level: "ERROR" and path: "/error"` | Errors on a specific route |
| `response: 404 or response: 500` | Either status code |
| `not level: "INFO"` | Everything except INFO (warnings + errors) |
| `verb: "POST" and response >= 500` | Failed POST requests |

### Wildcards & existence

| KQL | Meaning |
|-----|---------|
| `agent: *Googlebot*` | User agent contains "Googlebot" |
| `request: /api/*` | Any URL starting with `/api/` |
| `user: *` | Documents that *have* a `user` field |

> **Tip:** click any field name in the left sidebar of Discover to see its top values and add a
> filter with one click — no typing needed.

---

# Part 2 — Query DSL (the REST API)

This is how programs talk to Elasticsearch. Run these with `curl`, or paste them into
**Kibana → ☰ → Dev Tools** (which gives you autocomplete and a "run" button).

### Get everything (with a limit)

```bash
curl -s "http://localhost:9200/flask-logs-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "size": 5,
  "query": { "match_all": {} }
}'
```

### Exact match on a field (`term`)

`term` = exact value, no analysis. Great for keywords, status codes, levels.

```bash
curl -s "http://localhost:9200/flask-logs-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "query": { "term": { "level": "ERROR" } }
}'
```

### Full-text search on a message (`match`)

`match` analyzes the text (case-insensitive, word-by-word) — use it on message fields.

```bash
curl -s "http://localhost:9200/flask-logs-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "query": { "match": { "message": "login failed" } }
}'
```

### Numeric range (`range`)

```bash
curl -s "http://localhost:9200/web-access-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "query": { "range": { "response": { "gte": 500 } } }
}'
```

### Combine conditions (`bool`)

`bool` is how you AND/OR/NOT in Query DSL:
- `must` = AND (all must match), `should` = OR, `must_not` = NOT, `filter` = AND but faster (no scoring).

```bash
curl -s "http://localhost:9200/web-access-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "query": {
    "bool": {
      "must":     [ { "term": { "verb": "POST" } } ],
      "filter":   [ { "range": { "response": { "gte": 500 } } } ],
      "must_not": [ { "match": { "agent": "Googlebot" } } ]
    }
  }
}'
```
Reads as: *POST requests **AND** status ≥ 500 **AND NOT** from Googlebot.*

---

# Part 3 — Aggregations (the real power)

Searching finds matching logs. **Aggregations** summarize them — counts, averages, top-N. This is
what turns logs into insight (and into Kibana charts).

### Count requests per status code (`terms` aggregation)

```bash
curl -s "http://localhost:9200/web-access-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "size": 0,
  "aggs": {
    "by_status": {
      "terms": { "field": "response" }
    }
  }
}'
```
`"size": 0` = don't return individual logs, just the summary. The result buckets each status code
with a count — *"200: 412, 404: 38, 500: 11"*. This is exactly what a "status codes" pie chart shows.

### Top 5 busiest client IPs

```bash
curl -s "http://localhost:9200/web-access-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "size": 0,
  "aggs": {
    "top_ips": {
      "terms": { "field": "clientip", "size": 5 }
    }
  }
}'
```
Answers *"who is hitting us the most?"* — great for spotting a misbehaving client or a bot.

### Average order amount (`avg` aggregation, Project 1)

```bash
curl -s "http://localhost:9200/flask-logs-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "size": 0,
  "query": { "term": { "path": "/order" } },
  "aggs": {
    "avg_order": { "avg": { "field": "amount" } }
  }
}'
```

### Errors over time (`date_histogram` — the basis of every time chart)

```bash
curl -s "http://localhost:9200/web-access-*/_search?pretty" -H 'Content-Type: application/json' -d '
{
  "size": 0,
  "query": { "range": { "response": { "gte": 500 } } },
  "aggs": {
    "errors_per_minute": {
      "date_histogram": { "field": "@timestamp", "fixed_interval": "1m" }
    }
  }
}'
```
Buckets errors into 1-minute windows — this is literally how Kibana draws "errors per minute".

---

# Part 4 — Handy admin queries

```bash
# List all indexes and how many docs each holds
curl -s "http://localhost:9200/_cat/indices?v"

# Cluster health (green / yellow / red)
curl -s "http://localhost:9200/_cluster/health?pretty"

# How many docs match a query (count only, no documents)
curl -s "http://localhost:9200/web-access-*/_count?pretty" -H 'Content-Type: application/json' -d '
{ "query": { "range": { "response": { "gte": 500 } } } }'

# See the field types Elasticsearch detected (the "mapping")
curl -s "http://localhost:9200/web-access-*/_mapping?pretty"

# Delete an index (careful!)
curl -X DELETE "http://localhost:9200/web-access-2024.10.10"
```

---

## KQL ↔ Query DSL cheat sheet

| Goal | KQL (search bar) | Query DSL (JSON) |
|------|------------------|-------------------|
| Exact match | `level: "ERROR"` | `{"term": {"level": "ERROR"}}` |
| Text search | `message: "timeout"` | `{"match": {"message": "timeout"}}` |
| Number ≥ | `response >= 500` | `{"range": {"response": {"gte": 500}}}` |
| AND | `a: 1 and b: 2` | `bool.must: [...]` |
| OR | `a: 1 or b: 2` | `bool.should: [...]` |
| NOT | `not a: 1` | `bool.must_not: [...]` |
| Wildcard | `url: /api/*` | `{"wildcard": {"url": "/api/*"}}` |

---

## Key takeaways

- ✅ **KQL** for fast interactive searching in Kibana; **Query DSL** (JSON) for the API/automation
- ✅ `term` = exact match, `match` = full-text, `range` = numbers/dates, `bool` = combine them
- ✅ **Aggregations** (`terms`, `avg`, `date_histogram`) summarize logs — this powers every chart
- ✅ `"size": 0` returns just the summary, not the raw logs
- ✅ Kibana **Dev Tools** is the friendliest place to practice Query DSL (autocomplete + run button)

---

[← Back to ELK home](../README.md)
