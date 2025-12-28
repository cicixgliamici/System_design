# First fundamentals (to start strong)

This note introduces the “core concepts” you’ll use in ~90% of system design interviews.

---

## 1) Requirements: functional vs non-functional
### Functional (what it does)
Examples:
- “shorten URLs and redirect”
- “send messages, deliver, read receipts”
- “feed with posts and likes”

### Non-functional (how it must behave)
Examples:
- **latency**: p95 < 200ms
- **availability**: 99.9% or 99.99%
- **consistency**: strong vs eventual (what’s acceptable?)
- **scalability**: peak traffic, growth, multi-region
- **cost**: budget constraints, efficiency

> Tip: pick 2–3 key NFR “drivers” and let them guide your design choices.

---

## 2) Back-of-the-envelope numbers
### Common metrics
- **RPS/QPS**: requests per second
- **Read/Write ratio**
- **Storage**: total data + growth
- **Bandwidth**: ingress/egress
- **Peak factor**: peak vs average (e.g., 5x, 10x)

### Quick formulas
- `RPS ≈ daily_requests / 86400`
- `Storage/day ≈ daily_events * bytes_per_event`
- `Bandwidth ≈ RPS * bytes_per_response`

Useful magnitude facts:
- 1 KB = 10^3 B, 1 MB = 10^6 B, 1 GB = 10^9 B, 1 TB = 10^12 B (approx)
- 1 day = 86,400 seconds

---

## 3) Latency vs throughput (and why p99 matters)
- **Latency**: response time of a single request
- **Throughput**: how many requests per second you can serve
- **Tail latency (p95/p99)**: users feel the worst cases, not the average

Typical tail latency causes:
- GC pauses
- occasional slow queries
- lock contention
- flaky downstream dependencies

---

## 4) Scaling: vertical vs horizontal
- **Vertical scaling**: bigger machine (eventually hits limits / cost)
- **Horizontal scaling**: more instances + load balancing

Most interview architectures assume:
- **stateless services** (easy to replicate)
- state stored in **DB/cache/object storage**

---

## 5) Essential building blocks
### Load Balancer (LB)
Distributes traffic across instances.
Concepts:
- health checks
- round-robin / least-connections
- L4 vs L7 (TCP vs HTTP-aware)

### Cache (e.g., Redis)
Reduces latency and DB load.
Patterns:
- cache-aside (lazy loading)
- write-through / write-back (more advanced)
Risks:
- cache stampede (many misses at once)
- invalidation (the “hard problem”)

### Databases
- **SQL**: transactions, constraints, complex queries, strong schema
- **NoSQL**: simpler scale for certain access patterns, denormalization
Typical questions:
- what is the primary access key?
- do you need strong transactions?
- how do you handle growth and hot keys?

### Messaging (Queue / Pub-Sub / Stream)
Used for async work and decoupling.
Concepts:
- at-least-once vs at-most-once delivery
- consumer groups
- retries + DLQ (dead letter queue)

### CDN
Edge caching for static assets and media.

---

## 6) Consistency: strong vs eventual (product-driven)
- **Strong consistency**: reads immediately see the latest write
  - pros: simpler correctness
  - cons: higher latency / more complexity in distributed systems
- **Eventual consistency**: state converges over time
  - pros: higher availability / better scalability
  - cons: temporary inconsistencies you must handle

Examples:
- bank balance: usually strong
- like count: eventual is often fine

---

## 7) Reliability: retries, idempotency, rate limiting
### Retries (do them safely)
- use **exponential backoff + jitter**
- avoid infinite retries and retry storms

### Idempotency
If you repeat the same request (due to timeouts/retries), the outcome stays correct.
Techniques:
- idempotency keys
- dedup by message id
- controlled upserts

### Rate limiting
Protects against abuse and overload:
- token bucket / leaky bucket (concepts)
- limits per user/IP/API key

---

## 8) Minimal case study template
Copy this block into every new `design.md`:

## Requirements
- Functional:
- Non-functional:
- Out of scope:

## Assumptions
- ...

## Back-of-the-envelope
- Users:
- Peak RPS:
- Storage/day:
- Bandwidth:

## High-level design
- Components:
- Main flows:

## Deep dives
1) ...
2) ...

## Failure modes & mitigations
- ...

## Trade-offs
- ...

## Next iteration
- ...

---

For each: Requirements + Numbers + High-level diagram + 3 failure modes.