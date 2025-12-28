# System Design: what it is and what the goal is

## Definition (one-liner)
**System design** is the practice of designing a **distributed software system** (services, databases, caches, queues, networks) that meets functional and non-functional requirements through well-reasoned **trade-offs**.

---

## Why it appears in interviews
A system design interview is not about finding a “perfect” architecture. It tests whether you can:
- clarify requirements and scope
- estimate rough capacity numbers (RPS/QPS, storage, bandwidth)
- design something **scalable** and **reliable**
- reason about **failures**, graceful degradation, and operability
- explain **trade-offs** (consistency vs availability, cost vs performance, etc.)

---

## What interviewers typically evaluate
1. **Clarity**: you ask the right questions and define scope
2. **Structure**: you follow a repeatable process
3. **Numbers**: capacity planning + identify bottlenecks
4. **Architecture**: sensible components and data flows
5. **Deep dives**: 2–3 critical areas (DB/cache/queue/consistency)
6. **Resilience**: retries, idempotency, rate limiting, DR basics
7. **Trade-offs**: you can defend choices and propose next iterations

---

## What a strong answer produces
You usually end up with:
- **Requirements** (functional + non-functional)
- **Back-of-the-envelope** (RPS, storage, bandwidth, latency budget)
- **High-level diagram** (client → LB/API → services → DB/cache/queue/CDN)
- **API / data model** (only as needed)
- **Bottlenecks & failure modes** (what breaks and how you mitigate)
- **Trade-offs** + “Next steps” (v2, 10x scale, cost)

---

## Recommended interview flow (repeatable)
Use the same structure every time:

1. **Scope & assumptions**
   - What’s in / what’s out?
2. **Requirements**
   - Functional (what it must do)
   - Non-functional (latency, availability, consistency, cost)
3. **Capacity planning**
   - Users, peak RPS, data size, growth
4. **High-level design**
   - Main components and flows
5. **Deep dive (2–3 areas)**
   - e.g., DB choice, caching, sharding, fanout, async processing
6. **Reliability & operability**
   - retries/idempotency, rate limits, observability, DR
7. **Trade-offs & iteration**
   - what you optimized for and how you’d scale to 10x

---

## What it is vs what it is not
It’s **not** writing perfect code or picking the “right cloud service”.
It **is** presenting a coherent, defensible design that scales and behaves well under failures.

---

## Minimal glossary (common interview terms)
- **RPS/QPS**: requests per second
- **p95/p99 latency**: tail latency percentiles
- **SLA/SLO/SLI**: reliability agreements/targets/indicators
- **Horizontal scaling**: add nodes instead of scaling up a single machine
- **Replication / Sharding**: copies / partitioning
- **Consistency**: strong vs eventual
- **Idempotency**: repeating a request does not change the outcome
- **Backpressure**: controlling load to avoid collapse

---

## How to use this repository
- Learn **building blocks** and **trade-offs**
- Practice **case studies** using the same template
- Each case study should include:
  - numbers + diagram + failure modes + trade-offs

> Final goal: have interview-ready notes and a repeatable approach you can execute under pressure.