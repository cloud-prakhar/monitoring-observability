# ELK with Your Applications

> How does ELK actually connect to the app you wrote? This page covers the **two ways apps get
> their logs into ELK** and the **network connectivity** that has to be in place for it to work.

---

## The golden rule: apps just write logs

The cleanest way to use ELK is for your application to **know nothing about ELK**. Your app's job
is simply to **write logs** — to a file or to standard output. A separate shipper (Filebeat)
picks them up.

**Real-world analogy:** you write a letter and drop it in your mailbox. You don't drive it to the
sorting centre yourself — the postal courier does. Your app writes a log line; Filebeat couriers
it to ELK. This separation means:

- If ELK is down, your app keeps running (logs just queue up in the file).
- Logging adds almost no latency to your app (writing a line to a file is fast).
- You can change your whole logging backend without touching app code.

---

## The two ways to ship logs

### Way 1 — App → file → Filebeat (recommended, used in both projects)

```
app.py  ──writes──▶  app.log  ──tailed by──▶  Filebeat  ──ships──▶  ELK
```

The app writes to a log file. Filebeat tails it. **This is the standard, robust pattern** and
the one this lab uses. The app and Filebeat share a folder (a Docker volume).

### Way 2 — App → Logstash directly (over the network)

```
app.py  ──HTTP/TCP──▶  Logstash  ──▶  Elasticsearch
```

The app opens a network connection and sends logs straight to Logstash (or even straight to
Elasticsearch's REST API). Simpler to picture, but **more fragile**: if Logstash is down or slow,
your app's logging can block or lose messages. Useful for some cases, but we prefer Way 1.

> **This lab uses Way 1** for both projects because it's how production systems are actually built
> and it's more reliable.

---

## Structured vs unstructured logs (this decides if you need Logstash)

| Your app logs… | Example | Needs Logstash? | Path |
|----------------|---------|-----------------|------|
| **Structured JSON** | `{"level":"ERROR","msg":"timeout","user":42}` | **No** — already has fields | Filebeat → Elasticsearch (**Project 1**) |
| **Raw text** | `192.168.1.1 - GET /home 500` | **Yes** — needs parsing into fields | Filebeat → Logstash → Elasticsearch (**Project 2**) |

**Rule of thumb:** if *you* control the app, log **JSON** — then you can skip Logstash. You only
reach for Logstash when logs come in a format you can't change (web servers, databases, legacy
apps) and need parsing. This is exactly the contrast our two projects teach.

---

## Network connectivity requirements

For logs to flow, each hop must be able to reach the next one over the network. In Docker, that
means everything must be on the **same Docker network** and refer to each other by **container
name**.

```
┌─────────────────────── Docker network: "elk" ───────────────────────┐
│                                                                      │
│  app ──▶ Filebeat ──▶ Logstash:5044 ──▶ Elasticsearch:9200 ◀── Kibana│
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### The ports that must be open between components

| From | To | Port | Purpose |
|------|----|------|---------|
| Filebeat | Logstash | **5044** | Beats protocol — ship logs for parsing |
| Filebeat | Elasticsearch | **9200** | Ship logs directly (Path A) |
| Logstash | Elasticsearch | **9200** | Load parsed logs |
| Kibana | Elasticsearch | **9200** | Read logs to display |
| You (browser) | Kibana | **5601** | Use the UI |
| You (browser) | Elasticsearch | **9200** | (optional) call the REST API directly |

### The two networking rules that trip up beginners

1. **Use container names, not `localhost`.** Inside the `elk` Docker network, Kibana reaches
   Elasticsearch at `http://elasticsearch:9200`. If Kibana used `localhost:9200`, it would look
   *inside its own container* and find nothing. `localhost` only works from **your laptop's
   browser** to a **published port** (like `localhost:5601` for Kibana). This is the **exact same
   rule** as `http://prometheus:9090` in the Grafana part of this repo.

2. **Each project joins the existing `elk` network with `external: true`.** The `02-setup/`
   stack *creates* the `elk` network. Each project's `docker-compose.yml` says:

   ```yaml
   networks:
     elk:
       external: true     # "join the elk network that 02-setup already created"
   ```

   So you must **start `02-setup/` first**, then start a project — identical to how `infra/` must
   be up before `projects/01-flask-web-api/` in the metrics track.

---

## Putting it together (what each project does)

```
Project 1 — flask-json-logger
   Flask app writes JSON  →  Filebeat  →  Elasticsearch  →  Kibana
   (no Logstash — logs are already structured)

Project 2 — web-access-log-analyzer
   Flask app writes raw access logs  →  Filebeat  →  Logstash (grok ETL)  →  Elasticsearch  →  Kibana
   (Logstash parses the raw text into fields)
```

You'll set up the shared stack once (`02-setup/`), then run each project, watch logs appear in
Kibana, and finally search them in [03-queries/](../03-queries/README.md).

---

## A note on production (so you don't learn bad habits)

This lab turns **security off** so there's nothing to fight with. In a real deployment you would:

- Set `xpack.security.enabled=true` and put a **password** on Elasticsearch.
- Use **HTTPS/TLS** between every component.
- Not expose Elasticsearch (`9200`) to the public internet — only Kibana, behind a login.
- Give Elasticsearch much more RAM and run **multiple nodes** for reliability.

Everything else — the data flow, the config files, the concepts — stays exactly the same.

---

## Key takeaways

- ✅ Best practice: **apps just write logs**; Filebeat ships them (app stays decoupled from ELK)
- ✅ **JSON logs → skip Logstash**; **raw text logs → use Logstash** to parse them
- ✅ All components must share one Docker network and use **container names**, never `localhost`
- ✅ Key ports: Filebeat→Logstash `5044`, everyone→Elasticsearch `9200`, browser→Kibana `5601`
- ✅ Start `02-setup/` first (it creates the `elk` network); projects join it with `external: true`

---

[← Config breakdown](04-config-breakdown.md) | [Up: Fundamentals index](README.md) | [Next: Install ELK with Docker →](../02-setup/README.md)
