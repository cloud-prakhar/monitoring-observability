# ELK Fundamentals (read first)

The **concepts** behind the ELK Stack — read these *before* installing anything. No commands
here, just the "what" and "why". Each file is short and builds on the previous one.

---

## Pages

| # | Page | What it covers |
|---|------|----------------|
| 1 | [What is ELK?](01-what-is-elk.md) | What E, L, and K each do, what they're built on (Java + Lucene), and what kind of database Elasticsearch is |
| 2 | [Architecture & data flow](02-architecture.md) | The full journey of a log line (mermaid diagram) and what **ETL** means |
| 3 | [Beats](03-beats.md) | The tiny shippers that get logs *into* the stack — what Filebeat is and why you need it |
| 4 | [Config file breakdown](04-config-breakdown.md) | Every config file (Elasticsearch, Logstash, Kibana, Filebeat), line by line, and why each matters |
| 5 | [ELK with your applications](05-elk-with-applications.md) | How your apps connect: networking requirements and the two ways to ship logs |

---

## The one diagram to remember

```
   YOUR APP            BEATS            LOGSTASH         ELASTICSEARCH        KIBANA
  (writes logs)  →  (ships logs)  →  (cleans logs)  →  (stores + indexes) →  (you search)
   app.log          Filebeat          parse/enrich      the database         the dashboard
```

If you remember only one thing: **logs flow left to right**, and each tool does exactly one
job in that chain. Everything else is detail.

---

[Start: What is ELK? →](01-what-is-elk.md)
