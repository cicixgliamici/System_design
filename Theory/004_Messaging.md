# Messaging, Queues, and Event-Driven Architecture (EDA)

This guide explains when to use queues/events, how to choose between queue and stream models, and which trade-offs to expect.

---

## 1) Why messaging matters

Messaging is useful when you need to:
- decouple services (producers and consumers can evolve independently)
- absorb traffic spikes (buffering)
- move slow tasks to async workflows (email, thumbnails, export, webhooks)
- improve reliability with controlled retries

Mental model:
> fast user request + heavy background processing.

---

## 2) Queue vs Pub/Sub vs Stream

### Queue (work queue)
- A message is processed by **one consumer** in a consumer group.
- Ideal for "process once" jobs (e.g., sending an email).

### Pub/Sub
- One event can be consumed by **multiple subscribers**.
- Ideal to notify multiple domains (analytics, audit, search indexing).

### Stream (append-only log)
- Events are ordered and persisted, consumers read by offset.
- Ideal for replay, audit, data pipelines, and near-real-time analytics.

Practical choice:
- background jobs → queue
- multiple integrations → pub/sub
- domain events + replay → stream

---

## 3) Delivery guarantees

- **At-most-once**: no duplicates, but possible data loss.
- **At-least-once**: near-zero loss in practice, but duplicates are possible.
- **Exactly-once**: expensive/complex, often limited to the broker scope.

Rule of thumb for product systems:
> build **idempotent consumers** + use at-least-once delivery.

---

## 4) Consumer idempotency

Useful techniques:
- unique `event_id` and dedup in DB/cache (`processed_events`)
- upsert with a natural business key
- transaction: "write business state + mark event as processed"

Example:
- `OrderPaid` arrives twice
- notification consumer sends one email because `event_id` was already processed

---

## 5) Ordering and partitioning

Global ordering is rare and expensive.
Most systems need ordering **per key**:
- partition by `user_id` or `order_id`
- all events for the same key go to the same partition

Trade-off:
- more partitions = higher throughput
- ordering is guaranteed only within a partition

---

## 6) Retries, DLQ, and poison messages

### Retry strategy
- exponential backoff + jitter
- max attempts
- consumer timeout

### Dead Letter Queue (DLQ)
Messages that fail repeatedly are moved to DLQ for analysis/replay.

### Poison message
A message that is always invalid (schema mismatch, corrupt payload).
Mitigations:
- schema validation at ingestion
- circuit breaker for slow dependencies
- alerting on DLQ growth

---

## 7) Schema evolution

Events change over time; avoid sudden breaking changes.

Practices:
- add optional fields, avoid removing required fields used by consumers
- version schemas (`v1`, `v2`) or use a schema registry
- use tolerant-reader consumers (ignore unknown fields)

---

## 8) Minimum observability

Key metrics to monitor:
- queue depth / consumer lag
- processing rate
- retry rate
- DLQ count
- end-to-end latency from event to side effect

Example SLO:
- "95% of events processed within 30 seconds".

---

## 9) Interview mini-checklist

- What is the core domain event?
- Which delivery semantics are acceptable?
- How do you guarantee idempotency?
- What happens if a consumer is down for 2 hours?
- How do you replay safely without duplicating business effects?
- How do you handle schema evolution?

---

## 10) Quick template for event-driven design

```md
## Core events
- ...

## Producers
- ...

## Consumers
- ...

## Delivery semantics
- ...

## Idempotency
- ...

## Retry + DLQ
- ...

## Metrics / SLO
- ...
```
