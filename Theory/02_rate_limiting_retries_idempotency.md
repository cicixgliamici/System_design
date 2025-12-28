# Rate Limiting, Retries, and Idempotency (Fundamentals)

This chapter expands on the reliability basics from Chapter 1:
- **Rate limiting** to protect systems from abuse/overload
- **Retries** to handle transient failures safely
- **Idempotency** to make retries correct

---

## 1) Why rate limiting exists
Rate limiting is a **load-control** mechanism. It helps:
- protect downstream services and databases
- prevent abuse (scraping, brute force, noisy clients)
- keep p99 latency stable under spikes
- enforce fair usage per user / API key / IP

**Common outcomes:**
- return **HTTP 429** with a `Retry-After` header
- degrade gracefully instead of falling over

---

## 2) Where to apply rate limiting
Typical enforcement points (often layered):
1. **Edge / API Gateway** (best first line)
2. **Load Balancer / Reverse Proxy** (coarse, IP-based)
3. **Service-level** (fine-grained by endpoint/user)
4. **Downstream** (e.g., DB connection pools as hard limits)

**Rule of thumb:** enforce as early as possible, but keep service-level checks for correctness.

---

## 3) Rate limiting algorithms (interview essentials)
### Fixed Window Counter
- Count requests per window (e.g., per minute).
- **Pro:** simple.
- **Con:** boundary spike problem (burst at window edges).

### Sliding Window Log
- Store timestamps of requests.
- **Pro:** accurate.
- **Con:** expensive in memory/CPU at scale.

### Sliding Window Counter (approx)
- Combine current + previous window counters.
- **Pro:** good accuracy, cheap.
- **Con:** still approximate.

### Token Bucket (recommended default)
- Tokens refill at a steady rate; each request consumes 1 token.
- Allows **bursts** up to bucket size.
- **Pro:** great practical behavior, easy mental model.

### Leaky Bucket
- Enforces constant outflow.
- Useful when you want smoother traffic.

> In interviews, starting with **Token Bucket** is usually a safe choice.

---

## 4) Distributed rate limiting (at scale)
If you have multiple service instances, you need a shared state or consistent partitioning.

### Option A — Central store (common)
- Store counters/tokens in **Redis**.
- Use atomic ops (Lua script / transactions).
- **Pros:** simple, consistent across instances.
- **Cons:** Redis becomes a dependency (latency, availability).

### Option B — Partitioned by key
- Use **consistent hashing** to route the same user key to the same limiter node.
- **Pros:** avoids central hot spot.
- **Cons:** more infrastructure and rebalancing complexity.

**Practical hybrid:** gateway does coarse limiting, services do fine-grained with Redis.

---

## 5) What to return to clients
For HTTP APIs:
- Status: **429 Too Many Requests**
- Headers (optional but nice):
  - `Retry-After: <seconds>`
  - `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

Also define client guidance:
- clients should back off (exponential backoff + jitter)
- don’t retry immediately on 429

---

## 6) Retries done safely
Retries should target **transient** failures (timeouts, 503, network hiccups).

**Best practice:**
- exponential backoff + jitter
- cap the number of retries
- set a total time budget (don’t retry forever)
- apply **retry budgets** (limit retries as a % of traffic)

**Avoid:** retry storms (everyone retries at once, making the incident worse).

---

## 7) Idempotency (the “make retries correct” tool)
Idempotency means: repeating the same request does not cause duplicate effects.

Typical use case:
- `POST /payments`
- client times out, retries
- without idempotency: double charge risk

### How to implement
- Client sends `Idempotency-Key: <uuid>`
- Server stores result keyed by `(client_id, idempotency_key)` with TTL
- If key repeats: return the **same result** as the first time

Often combined with:
- **dedup** in queues/streams (message-id)
- DB constraints (unique keys) + upsert patterns

---

## 8) Common failure modes and mitigations
- **Redis unavailable** → fail-open or fail-closed?
  - fail-open: better availability, risk overload
  - fail-closed: protect system, risk rejecting good traffic
  - typical: fail-closed on expensive endpoints, fail-open on cheap ones
- **Hot keys** (one user generates huge traffic)
  - per-user limiter, plus global limiter
- **Clock issues** (if using time windows)
  - prefer algorithms robust to small drift; rely on server time
- **Thundering herd** at reset boundaries
  - token bucket, jitter, and smoothing help

---

## 9) Interview checklist (quick)
When asked about rate limiting + retries:
- pick an algorithm (token bucket)
- decide where enforced (gateway + service)
- explain state (Redis + atomic operations)
- return semantics (429 + retry-after)
- handle failures (fallback strategy)
- mention idempotency for write endpoints
