# Exercise 07 — Design a Metrics Ingestion Pipeline (Q&A + Suggested Solution)

## Scenario

Design a platform that ingests application metrics from many services.

Examples:
- `request_count`
- `error_rate`
- `latency_p95`
- host/container CPU and memory

## Requirements

- ingest peak: **3 million metric points/sec**
- near-real-time dashboards (< 15s delay)
- retain raw data for 7 days, aggregated data for 13 months
- multi-tenant isolation and quotas
- high write throughput and cost control

---

## Questions

1. Which clarifying questions are essential?
2. How do you structure ingest, buffering, and storage?
3. What data model do you use for labels/tags?
4. How do you downsample and retain data by tier?
5. How do you protect against cardinality explosion?
6. What failure modes do you plan for?

---

## Suggested Answers

### A1) Clarifying questions

- Pull model, push model, or both?
- Max allowed labels per metric?
- Query profile: mostly dashboards or ad-hoc analytics?
- Need per-tenant dedicated storage?

Assumption: push-based ingestion, strict label quotas, single region to start.

### A2) Architecture

1. agents/SDKs push to ingest gateway
2. gateway validates/authenticates/normalizes
3. broker buffers bursts
4. stream processors perform pre-aggregation
5. raw + rollup storage tiers
6. query API serves dashboards and alerts

### A3) Data model

Use time-series points with dimensions:

`(tenant_id, metric_name, label_set_hash, timestamp, value)`

Store label dictionaries separately to reduce repetition cost.

### A4) Retention

- Raw: high-resolution for short window (7 days)
- Rollups: 1m/5m/1h aggregates for long retention
- Query engine picks cheapest sufficient tier automatically

### A5) Cardinality control

- hard quotas per tenant
- block dynamic/unbounded label keys (e.g., `user_id`)
- top-k heavy hitter detection and alerts

### A6) Failure modes

1. ingest spike:
   - broker buffering + backpressure
2. storage node failure:
   - replication and automatic reroute
3. bad client payload storms:
   - schema validation + rate limits + tenant circuit breaker
