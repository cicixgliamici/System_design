# Caching (Fundamentals): patterns, invalidation, stampede, consistency

Caching is one of the highest ROI levers in system design:

* reduces **latency** (p95/p99)
* reduces **DB load** and cost
* improves **availability** via graceful degradation

But it introduces the hard parts:

* invalidation
* staleness
* stampedes / hot keys
* operational complexity

---

## 1) What to cache (and what not to)

### Good candidates

* **read-heavy** data (high read/write ratio)
* expensive computations (aggregations, recommendations, rendering)
* “mostly immutable” objects (profiles, configs, product catalog)
* public content (CDN + edge caching)

### Bad candidates

* highly volatile data with strict correctness (bank balances)
* per-request unique results with low reuse
* data that is huge and rarely accessed (unless you have tiered caches)

Rule of thumb:

> Cache **reads** and keep **writes authoritative** in the database.

---

## 2) Where caching happens (layers)

Caching is usually multi-layered:

1. **Client cache** (browser/app): HTTP cache headers, local storage
2. **CDN / Edge**: static assets, images, public pages
3. **Reverse proxy**: NGINX/Varnish, micro-caching
4. **Application cache**: Redis/Memcached
5. **Database cache**: DB buffer pool (works “for free” but don’t rely on it alone)

Interview-friendly approach:

> Start from the edge (CDN) and move inward (Redis near the service).

---

## 3) Cache data model + keys

A cache is a key/value store: correctness depends on key design.

### Key design checklist

* include the **primary lookup dimension** (user_id, object_id)
* include **versioning** (schema changes) → `v1:profile:{user_id}`
* include **tenant/locale** if relevant → `v1:catalog:{tenant}:{locale}:{id}`
* avoid key explosion by caching only meaningful aggregates

### TTL (time-to-live)

TTL is your “safety net”.

* prevents infinite staleness
* bounds storage usage
* makes invalidation simpler (but not perfect)

---

## 4) Core caching patterns (interview essentials)

### A) Cache-Aside (Lazy Loading) — default choice

Flow:

1. read from cache
2. miss → read from DB
3. put into cache with TTL
4. return

**Pros**

* simple
* cache failures don’t block DB reads

**Cons**

* first read is slow (cold miss)
* stampede risk on popular keys

---

### B) Read-Through

Cache sits in front and fetches from DB automatically on miss.

**Pros**

* cleaner application logic

**Cons**

* more infrastructure / coupling

---

### C) Write-Through

Writes go to cache and DB synchronously.

**Pros**

* cache always warm for reads

**Cons**

* higher write latency
* cache becomes part of write path (more failure handling)

---

### D) Write-Back (Write-Behind)

Writes go to cache first, DB updated async.

**Pros**

* very fast writes
* absorbs spikes

**Cons**

* risk of data loss on cache failure
* much harder correctness model

Interview tip:

> For most product systems: **Cache-Aside** is the safe default.

---

## 5) Invalidation strategies (the hard part)

There are three classic approaches:

### 1) TTL-only (eventual correctness)

* simplest
* accept temporary staleness

Good for:

* counters, “likes”, feed previews, catalog pages

---

### 2) Explicit invalidation on write

On update:

* update DB (source of truth)
* delete cache key(s) or update them

Two variants:

* **delete** (“cache-aside invalidation”): safer, but next read is a miss
* **update**: faster reads, but risk inconsistent derived values

Good for:

* profiles, settings, “must be fresh-ish” data

---

### 3) Versioned keys (soft invalidation)

Instead of deleting:

* bump a version number (e.g., `profile_version:{user_id}`) and read key includes it
* old keys expire via TTL

**Pros**

* avoids distributed delete storms
* very robust under race conditions

**Cons**

* more keys + slightly more complexity

---

## 6) Consistency + correctness pitfalls

### Stale reads

If you can tolerate eventual consistency:

* TTL-only or async invalidation is acceptable

If not:

* avoid caching that field or use short TTL + explicit invalidation

---

### Race condition: “write then stale overwrite”

Scenario:

* request A reads DB (old), then sets cache
* request B writes new value, deletes cache
* A’s late cache set reintroduces stale value

Mitigations:

* **set with version** (CAS / compare-and-set pattern)
* **write timestamps** (only set if newer)
* **versioned keys** (recommended)

---

## 7) Cache stampede (thundering herd)

When a hot key expires, many requests miss and hammer DB.

Mitigations:

1. **Request coalescing / singleflight**

   * only one request recomputes; others wait/serve stale
2. **Stale-while-revalidate**

   * serve slightly stale value while refreshing in background
3. **Probabilistic early refresh**

   * refresh before TTL ends for very hot keys
4. **Jittered TTL**

   * randomize TTL to avoid synchronized expirations
5. **Rate limit on misses**

   * protect DB from bursty recompute

Interview sentence that scores:

> “We’ll use stale-while-revalidate + jittered TTL to avoid stampedes.”

---

## 8) Hot keys and uneven traffic

A single celebrity user/product can dominate traffic.

Mitigations:

* cache partitioning + good hashing
* local L1 cache on each instance (small, short TTL)
* break large objects into smaller keys
* apply **per-key** rate limits on recomputation

---

## 9) Failure modes & fallbacks

### Cache down / unreachable

Decide policy:

* **Fail-open**: bypass cache, hit DB (higher load, higher cost)
* **Fail-closed**: reject requests (protect DB, worse availability)

Common compromise:

* fail-open for cheap endpoints
* fail-closed for expensive endpoints (e.g., heavy search queries)

### Cache data corruption / poison

* validate schema/version
* use versioned keys
* keep TTL bounded

### Evictions / memory pressure

* capacity planning: hit ratio, average object size, TTL
* choose eviction policy (LRU is common)

---

## 10) Back-of-the-envelope (cache sizing quick math)

You want to estimate:

* **working set** size (how many hot objects)
* average object size
* TTL & access frequency

Example:

* hot objects: 5 million
* avg size: 1 KB
* memory needed ≈ 5,000,000 * 1 KB ≈ 5 GB
  Add overhead + replication → plan 2–3x.

Key metric:

* **hit ratio** (aim for a target, e.g., 90–99% depending on use case)

---

## 11) Interview checklist (quick)

When you propose caching, cover:

* what you cache and the key design
* pattern (cache-aside by default)
* TTL + invalidation plan
* stampede mitigation
* failure policy (fail-open/closed)
* consistency trade-off (what can be stale?)

---

## Mini template block (copy into case studies)

### Caching plan

* What cached:
* Key format:
* TTL:
* Pattern: cache-aside / read-through / write-through
* Invalidation:
* Stampede mitigation:
* Failure policy:
* Consistency notes:
