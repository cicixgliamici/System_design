# Data Modeling for High Scale Systems

## Why this topic matters

At scale, many incidents are caused by data model choices rather than code bugs.

A good model must balance:
- query performance
- write throughput
- correctness constraints
- operational simplicity

---

## Start from access patterns

Before choosing SQL/NoSQL tables, list top queries:

- hottest reads
- highest write paths
- latency-sensitive endpoints
- range scans vs key lookups

Rule of thumb: model for dominant access patterns, not abstract purity.

---

## Normalization vs denormalization

### Normalization
- less duplication
- stronger consistency by default
- more joins at read time

### Denormalization
- faster reads for critical endpoints
- fewer joins in hot path
- extra complexity for update propagation

Most real systems use a hybrid approach.

---

## Partition key design

Partition key quality strongly affects scalability.

Good partition keys:
- distribute load evenly
- match frequent query filters
- avoid hot partitions

Bad key examples:
- monotonically increasing keys causing write hotspots
- tenant IDs when one tenant dominates all traffic

---

## Secondary indexes and cost

Indexes speed reads but increase write amplification.

For each index ask:
- which exact query needs this index?
- is it worth slower writes + extra storage?
- can we use a covering index for the hot response shape?

---

## Schema evolution

At scale, schema changes are production events.

Recommended practices:
- backward-compatible deployments
- expand/migrate/contract strategy
- dual-read or dual-write only when necessary
- data backfills with throttling and observability

---

## Interview angle

Great responses include:
- concrete entities and keys
- 2–3 critical queries with expected cardinality
- partition/index choices with trade-offs
- migration path as traffic grows 10x
