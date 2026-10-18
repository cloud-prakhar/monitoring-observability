# ELK Stack — Local Logging Lab

> **The rest of this repo is about *metrics* (Prometheus + Grafana).**
> This part is about ***logs*** — the ELK Stack. Metrics tell you *something is wrong*;
> logs tell you *why*. ELK is the most popular open-source tool for collecting, storing,
> and searching logs.

Everything here runs on your machine with Docker — no cloud accounts, no subscriptions.

---

## What is ELK? (the 10-second version)

**ELK = Elasticsearch + Logstash + Kibana** — three tools that work as a team:

| Letter | Tool | Plain-English job | Real-world analogy |
|--------|------|-------------------|--------------------|
| **E** | **Elasticsearch** | Stores logs and makes them instantly searchable | The **library** that keeps every book and has a super-fast index |
| **L** | **Logstash** | Collects logs, cleans them up, and forwards them | The **mailroom** that opens, sorts, and stamps every letter |
| **K** | **Kibana** | The web dashboard to search and chart the logs | The **reading room + search desk** where you actually look things up |

Plus a fourth member you'll meet here: **Beats** (specifically **Filebeat**) — tiny
agents that sit next to your app and *ship* its log files into the stack.

---

## Why learn ELK?

Imagine 10 servers each writing their own log file. When a user reports "the site broke at
2pm", you do **not** want to SSH into 10 machines and run `grep` on 10 files. ELK pulls
**all** logs into one place where you can search across everything in one box —
*"show me every ERROR from the payment service in the last hour"* — and get an answer in
milliseconds. That is the entire point: **centralized, searchable logs.**

---

## Learn in this order

```
1. 01-fundamentals/     ← READ FIRST: what ELK is, how it works, the config files (no commands)
       │
       ▼
2. 02-setup/            ← install the whole stack with Docker (CLI first, then Compose)
       │
       ▼
3. projects/            ← two hands-on apps that ship real logs into ELK
       │  01-flask-json-logger        (App → Filebeat → Elasticsearch → Kibana)
       │  02-web-access-log-analyzer  (App → Filebeat → Logstash → Elasticsearch → Kibana)
       │
       ▼
4. 03-queries/          ← search and analyze your logs (Kibana KQL + Elasticsearch Query DSL)
```

---

## Directory map

```
elk/
├── README.md                       ← you are here
│
├── 01-fundamentals/                ← concepts (read first, no commands)
│   ├── 01-what-is-elk.md           ← E/L/K explained, what they're built on, the database
│   ├── 02-architecture.md          ← mermaid diagram + the full data flow (ETL explained)
│   ├── 03-beats.md                 ← what Beats/Filebeat are and why you need them
│   ├── 04-config-breakdown.md      ← every config file, line by line, and why it matters
│   └── 05-elk-with-applications.md ← how your apps connect: networking + shipping logs
│
├── 02-setup/                       ← install ELK with Docker
│   ├── 01-docker-cli.md            ← run each piece by hand (understand every flag)
│   ├── 02-docker-compose.md        ← the same stack in one file, one command
│   ├── docker-compose.yml          ← the full ELK stack
│   ├── config/                     ← logstash.yml + the Logstash pipeline
│   └── CLEANUP.md                  ← tear it all down
│
├── 03-queries/                     ← search demonstrations (KQL + Query DSL)
│   └── README.md
│
└── projects/                       ← hands-on log-shipping apps
    ├── 01-flask-json-logger/       ← structured JSON logs → Filebeat → Elasticsearch
    └── 02-web-access-log-analyzer/ ← raw access logs → Filebeat → Logstash (ETL) → Elasticsearch
```

---

## Ports at a glance

| Service | Port | URL | What it's for |
|---------|------|-----|---------------|
| Elasticsearch | 9200 | http://localhost:9200 | REST API — store & query logs |
| Logstash (Beats input) | 5044 | — | Where Filebeat sends logs |
| Logstash (monitoring) | 9600 | http://localhost:9600 | Logstash's own health API |
| Kibana | 5601 | http://localhost:5601 | The web UI you actually use |
| Flask JSON Logger (Project 1) | 8091 | http://localhost:8091 | Demo app |
| Web Access Log Analyzer (Project 2) | 8092 | http://localhost:8092 | Demo app |

> **No login by default.** For this local learning lab we turn Elastic's security *off*
> (`xpack.security.enabled=false`) so there are no passwords or certificates to fight with.
> **Never do this in production** — there you would enable security and put a password on
> Elasticsearch. See [01-fundamentals/05-elk-with-applications.md](01-fundamentals/05-elk-with-applications.md).

---

## How this relates to the Prometheus/Grafana part of the repo

| | Metrics (rest of repo) | Logs (this folder) |
|---|---|---|
| Question it answers | "*Is* something wrong, and how much?" | "*Why* did it go wrong?" |
| Data shape | Numbers over time (CPU = 73%) | Text events with context (one log line per event) |
| Collect with | Prometheus (pull/scrape) | Beats / Logstash (push/ship) |
| Store in | Prometheus TSDB | Elasticsearch |
| Visualize in | Grafana | Kibana |

Real teams run **both** — metrics to spot the problem fast, logs to explain it. See the
[logs fundamentals page](../monitoring-fundamentals/02-monitoring-fundamentals/02-logs.md)
for the concept; this folder is the hands-on version.
