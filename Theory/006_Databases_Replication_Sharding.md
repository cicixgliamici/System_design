# Databases, Replication, and Sharding (Fundamentals)

Databases are usually the most critical stateful component in a system design interview.

Almost every serious system must answer:
- where is data stored?
- how do we read it quickly?
- how do we write it safely?
- how do we scale it?
- what happens when a DB node fails?

This chapter focuses on the practical interview concepts:
- SQL vs NoSQL
- replication
- read replicas
- sharding
- hot partitions
- indexes
- trade-offs between scale and correctness

---

## 1) Why databases are central

Application servers are often stateless and easy to replicate.

The database is different:
- it stores durable state
- it is harder to scale
- it is harder to migrate
- failures are more painful

That is why many system design trade-offs revolve around protecting and scaling the database.

---

## 2) SQL vs NoSQL

### SQL databases
Examples:
- PostgreSQL
- MySQL

Strengths:
- strong schema
- transactions
- joins
- constraints
- mature tooling

Good fit when:
- relationships matter
- correctness is important
- transactions are central
- queries are rich and structured

Limitations:
- scaling writes can become harder
- sharding is often more operationally complex

### NoSQL databases
Examples:
- key-value stores
- document databases
- wide-column stores
- graph databases

Strengths:
- often easier horizontal scaling
- flexible schema in some models
- strong fit for specific access patterns

Good fit when:
- data model is access-pattern driven
- very large scale is expected
- denormalization is acceptable
- joins are limited or avoided

Limitations:
- weaker transactional model in many systems
- correctness may move into application logic
- query flexibility can be narrower

Interview rule:
> do not choose SQL or NoSQL by fashion; choose by access pattern, consistency needs, and scale.

---

## 3) Access patterns first

Before choosing the database, ask:
- what are the main reads?
- what are the main writes?
- what is the primary lookup key?
- do we query by user, time, region, or object id?
- do we need transactions?
- do we need secondary indexes?

A database choice without access-pattern reasoning is usually weak.

---

## 4) Replication

Replication means keeping copies of data on multiple nodes.

### Why replicate?
- improve availability
- improve read scalability
- recover from node failures
- reduce maintenance impact

### Typical primary-replica model
- one primary handles writes
- one or more replicas serve reads
- data is copied from primary to replicas

**Pros**
- simple mental model
- easy read scaling
- good for many web systems

**Cons**
- replication lag
- stale reads on replicas
- primary can become a write bottleneck

---

## 5) Replication lag

Replication is often asynchronous or semi-synchronous.

This means:
- a write may succeed on primary
- replicas may see it a little later

Problems this can cause:
- user writes profile, then reads old data from replica
- counters or order status look temporarily stale
- “read-after-write” behavior breaks

Mitigations:
- read recent writes from primary
- session stickiness to leader after write
- bounded staleness logic
- explicit product acceptance of eventual consistency

Interview phrase:
> replicas improve scale, but replication lag affects correctness expectations.

---

## 6) Read replicas

Read replicas are one of the first scaling steps after a single primary.

Good for:
- read-heavy systems
- dashboards
- content retrieval
- product catalogs
- profile reads

Not enough for:
- very heavy write traffic
- strict freshness after writes
- global-scale write-heavy systems

---

## 7) Indexes

Indexes speed up reads by organizing data for lookup.

### Benefits
- faster queries
- lower latency
- less full-table scanning

### Costs
- more storage
- slower writes
- more maintenance complexity

Interview point:
> indexes are not free; every additional index speeds up some reads and slows down writes.

Good question to ask:
- what are the most common query patterns?

---

## 8) Sharding

Sharding means splitting data across multiple database nodes.

Instead of one DB containing all rows:
- shard 1 stores part of the data
- shard 2 stores another part
- and so on

### Why shard?
- increase write throughput
- increase storage capacity
- distribute load

### Common shard keys
- `user_id`
- `tenant_id`
- `region`
- `time range`

Choosing the shard key is critical.

---

## 9) Good shard key vs bad shard key

A good shard key should:
- distribute traffic evenly
- distribute storage evenly
- align with common query patterns
- minimize cross-shard operations

A bad shard key creates:
- hotspots
- uneven storage growth
- expensive scatter-gather queries

Example:
- shard by `country` can be risky if one country dominates traffic
- shard by `user_id` is often more evenly distributed

---

## 10) Hot partitions

A hot partition is a shard receiving disproportionate traffic.

Examples:
- one celebrity user
- one trending product
- one tenant much larger than others

Problems:
- one shard saturates while others are idle
- latency spikes
- poor overall fleet utilization

Mitigations:
- better shard key choice
- key hashing
- logical partitioning plus rebalancing
- caching hot objects
- splitting extremely large tenants separately

---

## 11) Rebalancing and resharding

As the system grows:
- some shards become bigger than others
- traffic patterns change
- new capacity must be added

Rebalancing means moving data to redistribute load.

This is operationally difficult because:
- data migration is expensive
- routing tables change
- consistency and availability must be preserved during movement

This is why bad shard-key choices are costly.

---

## 12) Cross-shard queries and transactions

Sharding helps scale, but complicates some operations.

Harder problems:
- joins across shards
- transactions across shards
- global ordering
- unique constraints across all data

Mitigations:
- denormalization
- application-level aggregation
- asynchronous workflows
- designing around single-shard ownership when possible

Interview rule:
> if you shard, try to keep most requests within one shard.

---

## 13) Typical scaling path

A common evolution path is:

1. single DB
2. add indexes
3. add cache
4. add read replicas
5. separate read/write paths
6. shard when replication is no longer enough

This is a strong answer because it shows incremental evolution, not overengineering on day one.

---

## 14) SQL vs NoSQL in interview examples

### URL shortener
- SQL can work well initially
- key-value style access pattern may later justify a simpler distributed store

### Feed / timeline
- often needs denormalized storage and async fanout patterns
- NoSQL or hybrid designs can fit well

### Payments / orders
- SQL is often preferred because correctness and transactions matter

### Analytics / event ingestion
- append-heavy and large-scale patterns may fit distributed NoSQL / stream storage better

---

## 15) Failure modes and mitigations

### 1) Primary fails
Mitigation:
- automated failover
- replicas ready for promotion
- connection retry logic
- careful leader election / managed DB services

### 2) Replica lag becomes large
Mitigation:
- monitor lag
- route freshness-sensitive reads to primary
- scale replicas
- reduce expensive replica queries

### 3) One shard becomes hot
Mitigation:
- caching
- shard splitting
- better partitioning strategy
- isolate large tenants

### 4) Too many indexes slow writes
Mitigation:
- audit index usage
- drop unused indexes
- separate OLTP from analytics workloads

---

## 16) Interview checklist (quick)

When discussing databases, cover:
- access patterns
- SQL vs NoSQL choice
- indexing strategy
- replication model
- replica lag implications
- shard key
- hot partition risk
- failure and failover plan

---

## Mini template block (copy into case studies)

### Storage plan

- Main database type:
- Primary access patterns:
- Primary key / partition key:
- Secondary indexes:
- Replication model:
- Read/write split:
- Sharding strategy:
- Consistency notes:
- Failure handling: