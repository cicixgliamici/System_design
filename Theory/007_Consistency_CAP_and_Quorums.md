# Consistency, CAP, and Quorums (Fundamentals)

Consistency is one of the most important distributed-systems topics in system design.

In interviews, the real question is usually not:
> “Do you know the CAP theorem?”

It is:
> “What kind of correctness does the product need, and what latency/availability trade-offs are acceptable?”

---

## 1) What consistency means in practice

Consistency is about what a client sees after reads and writes.

Typical questions:
- after I write, do I immediately see the new value?
- do all replicas show the same value at the same time?
- can different users temporarily see different versions?

This is not only a database topic:
- caches affect consistency
- replicas affect consistency
- queues and async processing affect consistency
- multi-region systems affect consistency

---

## 2) Strong vs eventual consistency

### Strong consistency
After a successful write, future reads see the latest value.

**Pros**
- easier reasoning
- better correctness guarantees
- good for sensitive state

**Cons**
- higher latency
- lower availability under partitions or replica failures
- more coordination overhead

Good examples:
- payments
- balances
- inventory reservation
- unique username creation

### Eventual consistency
After a write, the system converges over time, but some reads may temporarily return stale data.

**Pros**
- better availability
- better scalability
- lower latency in distributed systems

**Cons**
- temporary anomalies
- more product-level complexity
- clients may need reconciliation logic

Good examples:
- like counts
- feed ranking
- analytics dashboards
- notification read models

Interview rule:
> choose consistency by product semantics, not by technical preference.

---

## 3) Useful consistency guarantees

Strong/eventual is only part of the story.

### Read-after-write consistency
A client that writes something can immediately read its own update.

Useful for:
- profile edits
- posting content
- order status updates

### Monotonic reads
Once a client has seen a newer value, it should not later see an older one.

Useful for:
- timelines
- settings
- dashboards

### Causal consistency
Operations that are causally related are observed in the expected order.

Useful for:
- messaging systems
- collaborative systems
- social interactions

In interviews, even mentioning read-after-write and monotonic reads already makes the discussion much stronger.

---

## 4) CAP theorem in interview terms

CAP says that in the presence of a **network partition**, you cannot fully guarantee both:
- strong consistency
- full availability

You must make a trade-off.

### Consistency
all nodes behave like they expose one up-to-date value

### Availability
every request receives a non-error response

### Partition tolerance
the system continues to operate despite communication failures between nodes

Important:
> in real distributed systems, partitions are not optional, so the real trade-off is usually between consistency and availability during failure.

---

## 5) Leader-based replication

A very common model:
- one leader/primary accepts writes
- followers/replicas receive updates
- reads may go to leader or replicas

### Benefits
- simple write path
- predictable conflict resolution
- common in production systems

### Drawbacks
- leader can become bottleneck
- replica lag creates stale reads
- failover adds complexity

Common mitigation:
- route freshness-sensitive reads to the leader
- allow stale reads on replicas for less critical endpoints

---

## 6) Quorums

Quorums are a way to reason about replicated reads/writes.

Suppose:
- `N` replicas total
- `W` replicas must acknowledge a write
- `R` replicas are read from

If:
- `R + W > N`

then reads and writes overlap on at least one replica, which helps clients see fresh data more often.

### Example
- `N = 3`
- `W = 2`
- `R = 2`

Then:
- writes need 2 acknowledgments
- reads query 2 replicas
- overlap improves freshness

### Trade-off
Higher `W`:
- better write durability/consistency
- slower writes

Higher `R`:
- better read freshness
- slower reads

This is a classic latency vs correctness trade-off.

---

## 7) Eventual consistency in product design

If you choose eventual consistency, you must define what users may observe.

Examples:
- like count updates after a few seconds
- feed order slightly changes after refresh
- unread notification count temporarily lags

That is acceptable only if:
- the product can tolerate it
- the UI communicates state clearly
- reconciliation eventually happens

Interview phrase:
> eventual consistency is acceptable when temporary staleness does not break user trust or business invariants.

---

## 8) Common anomalies

### Stale reads
User reads old data after an update.

### Lost update
Two clients overwrite each other without coordination.

### Write conflicts
Concurrent updates produce inconsistent or ambiguous state.

### Non-monotonic reads
Client sees newer state, then older state later from another replica.

Mitigations:
- leader reads after write
- version numbers
- optimistic locking
- compare-and-set
- quorum strategies
- session affinity
- conflict resolution rules

---

## 9) Multi-region consistency

Multi-region systems add:
- more latency
- more replica lag
- harder failover
- harder conflict management

Typical approach:
- keep one write leader per dataset/region
- use async replication to other regions
- route reads locally when staleness is acceptable
- route critical writes to the authoritative region

Trade-off:
- global low latency vs global strong consistency

---

## 10) Consistency with caches and queues

Consistency is not only the database.

### With cache
Problems:
- stale cache after DB write
- race conditions during invalidation

Mitigations:
- versioned keys
- explicit invalidation
- short TTL for sensitive fields

### With queues
Problems:
- async consumers update read models later
- duplicates / reordering

Mitigations:
- idempotent consumers
- ordering by key where needed
- eventual convergence guarantees

---

## 11) Interview checklist (quick)

When discussing consistency, cover:
- what needs strong consistency?
- what can be eventual?
- do we need read-after-write?
- what happens with replica lag?
- what happens during partitions?
- do caches or async consumers make data stale?
- what is acceptable from the product point of view?

---

## Mini template block (copy into case studies)

### Consistency plan

- Strong consistency needed for:
- Eventual consistency acceptable for:
- Read-after-write requirements:
- Replica usage:
- Quorum / leader strategy:
- Cache consistency notes:
- Failure / partition behavior: