# What is ELK?

> ELK is three open-source tools — **E**lasticsearch, **L**ogstash, and **K**ibana — that
> together collect your application's logs, store them, and let you search them from one web page.

---

## The three letters

### E — Elasticsearch (the storage + search engine)

Elasticsearch is where every log line ends up and lives. It is a **search engine** first and
a database second: its whole reason for existing is to find a needle in a haystack *fast*.

**Real-world analogy:** think of the index at the back of a textbook. Instead of reading all
500 pages to find where "photosynthesis" is mentioned, you flip to the index and it tells you
"pages 42, 87, 203" instantly. Elasticsearch builds that kind of index for **every word in
every log line**. This is called an **inverted index** (word → list of documents that contain it),
and it's why searching millions of logs feels instant.

- **Why it matters:** without it you'd be running `grep` across huge files on many servers.
  Elasticsearch makes "find every log containing `timeout` from yesterday" return in milliseconds.

### L — Logstash (the collector + cleaner)

Logstash sits in the middle. It **receives** logs, **transforms** them (cleans, reshapes,
adds fields), and **forwards** them to Elasticsearch.

**Real-world analogy:** a mailroom. Letters arrive in all shapes and languages. The mailroom
opens each one, sorts it, stamps it with the date, translates it into a standard format, and
puts it in the right pigeonhole. Logstash does that for log lines — turning messy raw text
into clean, structured data.

- **Why it matters:** raw logs are messy (a web server log is just a line of text). Logstash
  turns `192.168.1.1 - - [10/Oct/2024] "GET /home" 200` into neat fields you can filter on:
  `client_ip`, `method`, `url`, `status`. This is the **ETL** step (explained in
  [02-architecture.md](02-architecture.md)).

### K — Kibana (the dashboard)

Kibana is the web UI. It talks to Elasticsearch and lets you **search logs**, **build charts**,
and **make dashboards** — all in your browser. You almost never talk to Elasticsearch directly;
you use Kibana.

**Real-world analogy:** the reading room and search desk of the library. The books (data) live
in the back; Kibana is the friendly front desk where you ask questions and see results.

- **Why it matters:** it turns a raw pile of logs into something a human can actually use —
  type a search, get a live table, draw a graph of errors over time.

---

## What are they built on? (the foundations)

| Tool | Built with | Built on top of |
|------|------------|-----------------|
| **Elasticsearch** | **Java** (runs on the JVM) | **Apache Lucene** — the underlying search library that does the actual indexing |
| **Logstash** | **Java + JRuby** (runs on the JVM) | A plugin engine: *input → filter → output* plugins |
| **Kibana** | **Node.js + TypeScript** | A web app that calls the Elasticsearch REST API |

The key takeaway: **Elasticsearch is a friendly, distributed wrapper around Apache Lucene.**
Lucene is a decades-old Java library that knows how to build inverted indexes on a single
machine. Elasticsearch adds the network API, clustering (spreading data across many machines),
and JSON-over-HTTP so you can use it from any language.

> Because Elasticsearch and Logstash run on the **JVM (Java Virtual Machine)**, they need a
> chunk of RAM (memory) reserved up front — that's the `ES_JAVA_OPTS=-Xms512m -Xmx512m` setting
> you'll see in the setup. It tells Java "you may use this much heap memory."

---

## What kind of database does Elasticsearch use?

Elasticsearch is a **document database** that stores data as **JSON documents**, and it is also
a **search engine**. Some vocabulary, with the closest SQL-database word next to it:

| Elasticsearch term | Means… | SQL equivalent |
|--------------------|--------|----------------|
| **Document** | One JSON record — e.g. one log line | A **row** |
| **Field** | One key inside the document — e.g. `status: 500` | A **column** |
| **Index** | A collection of similar documents — e.g. `web-access-2024` | A **table** |
| **Mapping** | The schema: what type each field is (text, number, date) | The **table schema** |
| **Shard** | A piece of an index (so it can be split across machines) | (no direct equivalent) |

So a single web request log becomes **one JSON document** like this, stored in an **index**:

```json
{
  "@timestamp": "2024-10-10T14:32:01Z",
  "client_ip": "192.168.1.100",
  "method": "GET",
  "url": "/checkout",
  "status": 500,
  "service": "web-access-log-analyzer"
}
```

Under the hood Lucene builds an **inverted index** so that searching for `status: 500` doesn't
scan every document — it jumps straight to the list of documents where `status` is `500`.

> **It is NOT a relational database.** There are no JOINs across tables like in MySQL/Postgres.
> Instead, you usually store everything you need about an event *inside the one document*
> (this is called *denormalizing*). That's a perfect fit for logs, because each log line is
> already a self-contained event.

---

## Key takeaways

- ✅ **E**lasticsearch = stores logs and searches them fast (built on Java + Apache Lucene)
- ✅ **L**ogstash = collects and cleans logs before storing them (the ETL step)
- ✅ **K**ibana = the web UI to search logs and build dashboards
- ✅ Elasticsearch is a **JSON document database + search engine**, *not* a relational one
- ✅ The magic trick is the **inverted index** (word → documents), which makes search instant

---

[← Fundamentals index](README.md) | [Next: Architecture & data flow →](02-architecture.md)
