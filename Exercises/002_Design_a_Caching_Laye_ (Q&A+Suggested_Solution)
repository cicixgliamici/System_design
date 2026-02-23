# Exercise 02 — Design a Caching Layer (Q&A + Suggested Solution)

## Scenario

You are building an e-commerce service with two endpoints:

* `GET /catalog` (product list + prices + availability)
* `GET /product/{id}` (product detail)

The SQL database is under pressure. You want to introduce a cache layer (Redis) to reduce latency and DB load.

---

## Requirements

### Traffic & targets

* **Peak traffic:** 80k RPS total
* `GET /catalog`: 90% of traffic (read-heavy)
* `GET /product/{id}`: 10% of traffic
* **Latency target:** p95 < 150ms
* **Availability SLO:** 99.9%

### Data & correctness

* **Catalog data** changes rarely (name, description, images): a few updates per day
* **Price and availability** change often: up to 1 update/min for hot products
* You must support a **flash sale** (traffic 5× for 10 minutes)
* System is **horizontally scaled** (many API instances)

### Constraints

* Prefer **simplicity** and an “interview-friendly” design
* Redis must not become a single point of failure
* You cannot accept availability being wrong for more than ~30 seconds for hot products

  * for the catalog (list), staleness up to **2 minutes** is OK

---

## Deliverables

* what to cache vs what not to cache
* chosen caching pattern (cache-aside, etc.)
* key design + TTLs
* invalidation strategy
* stampede + hot key mitigation
* failure modes + fallback policy
* how you handle freshness for **price/stock**

---

## Questions (answer first)

1. **Q1)** What clarifying questions do you ask?
2. **Q2)** What would you cache for `GET /catalog` and `GET /product/{id}`?
3. **Q3)** Which caching pattern do you choose (cache-aside/read-through/…) and why?
4. **Q4)** How do you define cache keys and your versioning strategy?
5. **Q5)** What TTLs do you set for: catalog, product detail, price, availability?
6. **Q6)** How do you invalidate/update cache when price/stock changes?
7. **Q7)** How do you prevent cache stampede during the flash sale?
8. **Q8)** List 3 failure modes and how the system degrades safely.

---

# Suggested Answers (Q&A)

## A1) Clarifying questions

* Is `GET /catalog` personalized (user segment, locale/currency, filters) or global?
* Roughly how many products exist (order of magnitude)?
* Is “availability” global or per warehouse/store?
* Is the purchase flow using the same source as `GET /product/{id}` (stock needs to be fresher)?
* Single region or multi-region?

**Assumptions for this exercise:** catalog is not personalized beyond locale/currency, stock is global per product, single region.

---

## A2) What to cache

### `GET /catalog` (list)

* Cache the **rendered list view** (IDs + key fields) with a longer TTL.
* Avoid embedding strict, ultra-fresh stock in the list response; show approximate stock status if needed.

### `GET /product/{id}`

* Cache **static product fields** (name, description, images) with a long TTL.
* Split **price** and **stock** into separate keys with short TTLs and/or explicit invalidation.

> Useful technique: **split caching** (static vs volatile) to control staleness.

---

## A3) Pattern

Choose **cache-aside** (lazy loading) as the default:

* read: cache → miss → DB → set cache → return
* resilient: if cache is down, you can still read from DB (with protections)

For volatile fields (price/stock):

* still cache-aside, but add explicit invalidation and short TTLs

---

## A4) Key design + versioning

Use prefixes + schema versions:

* Catalog:

  * `v1:catalog:{locale}:{currency}:page:{n}`
  * or `v1:catalog:{locale}:{currency}:hash:{filters}`
* Product static:

  * `v1:product:{id}:static`
* Price:

  * `v1:product:{id}:price:{currency}`
* Stock:

  * `v1:product:{id}:stock`

Versioning rules:

* bump `v2:` when the value schema changes
* optional “soft invalidation”: store `product_ver:{id}` and include it in keys (stronger under races)

---

## A5) Suggested TTLs

* `catalog:*` → **120s** (staleness up to 2 min is acceptable)
* `product:{id}:static` → **6h–24h** (rarely changes)
* `product:{id}:price:*` → **30s** (10–30s for very hot products)
* `product:{id}:stock` → **10–30s** (matches the “<= 30s wrong” constraint)

Add **TTL jitter** (±10–20%) to avoid synchronized expirations.

---

## A6) Invalidation on updates (price/stock)

When an update arrives:

1. Write to DB (source of truth)
2. Publish an event: `ProductUpdated(id, fields=price/stock)`
3. A worker invalidates/updates keys:

   * delete: `v1:product:{id}:price:*` and `v1:product:{id}:stock`
   * optionally bump `product_ver:{id}` (versioned keys)

Interview-friendly default:

> **Delete-on-write** for price/stock + short TTL.

---

## A7) Stampede prevention (flash sale)

Mitigations:

* **stale-while-revalidate** for catalog: serve slightly stale content while one worker refreshes
* **singleflight/request coalescing** for hot product keys: one request recomputes, others wait or serve stale
* **jittered TTL**
* rate-limit recomputation paths to protect the DB
* optional: **pre-warm** top-N products before the promo

Interview line:

> “We’ll use stale-while-revalidate + singleflight + TTL jitter to prevent thundering herds.”

---

## A8) Failure modes + safe degradation

1. **Redis down / high latency**

* reads: **fail-open** (bypass cache → DB) with circuit breakers and limits
* if DB is at risk: return a simpler response (reduced fields) or apply 429 on non-critical endpoints

2. **DB under heavy load**

* temporarily increase TTLs via feature flag
* serve catalog “stale” longer (grace period)
* shed load (429) on expensive endpoints

3. **Hot keys / skewed traffic**

* split static/volatile keys
* small local L1 cache in each API instance for ultra-hot items
* throttle recomputation per key

---

# Full Solution (High-level Design)

## Components

* Client
* CDN (static assets)
* API Service (stateless)
* Redis (shared cache)
* SQL DB (source of truth)
* Event bus (Kafka/SQS/RabbitMQ conceptually) for invalidation
* Invalidation worker/consumer

## Diagram

```mermaid
flowchart LR
  C[Client] --> CDN[CDN]
  C --> API[API Service]
  API --> R[(Redis Cache)]
  API --> DB[(SQL DB)]
  DB --> BUS[(Event Bus)]
  BUS --> INV[Cache Invalidation Worker]
  INV --> R
```

## Read path

### `GET /product/{id}`

1. Fetch `v1:product:{id}:static`
2. Fetch `v1:product:{id}:price:{currency}`
3. Fetch `v1:product:{id}:stock`
4. Misses fall back to DB; set keys with appropriate TTLs

(Optimization: Redis `MGET` / pipelining.)

### `GET /catalog`

1. Fetch `v1:catalog:{locale}:{currency}:page:{n}`
2. On miss: DB query (or materialized view) → set TTL 120s + jitter
3. With stale-while-revalidate: if expired recently, serve stale and refresh async

---

## “Interview-style” summary

* **Pattern:** cache-aside + split static/volatile keys
* **TTLs:** catalog 120s, static 6–24h, price 30s, stock 10–30s (+ jitter)
* **Freshness:** delete-on-write + short TTL for price/stock
* **Stampede:** singleflight + stale-while-revalidate + jittered TTL
* **Failures:** fail-open for reads, circuit breakers + bulkheads to protect DB
