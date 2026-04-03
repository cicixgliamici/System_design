# Exercise 04 — Design a News Feed (Q&A + Solution)

## Scenario

You are designing the home feed for a social product.
Users can:
- follow other users
- publish posts
- open the app and see a personalized feed

### Requirements

* Show the most recent/relevant posts from followed users
* Feed load should feel fast on app open
* New posts should appear reasonably quickly
* Peak traffic is much higher on reads than writes
* System should scale to tens of millions of users

### Deliverables

* requirements clarification
* feed generation strategy
* storage choices
* caching strategy
* consistency choices
* failure modes
* scaling plan

---

## Questions (answer these first)

1. **Q1)** What clarifying questions do you ask?
2. **Q2)** Do you choose fanout-on-write or fanout-on-read?
3. **Q3)** What data stores do you need?
4. **Q4)** How do you cache the feed?
5. **Q5)** How do you handle celebrity users with huge follower counts?
6. **Q6)** What consistency guarantees matter?
7. **Q7)** What are 3 failure modes and mitigations?
8. **Q8)** How would the design evolve at 10x scale?

---

# Suggested Answers (Q&A)

## A1) Clarifying questions

* Is the feed purely chronological or ranked?
* Are we showing only followed users, or also recommendations?
* Do we need strong freshness, or is a few seconds/minutes of delay acceptable?
* Are likes/comments included inline?
* What is the read/write ratio?
* Do we support multi-region users?

*Assumption for this exercise:* hybrid feed, mostly followed users, read-heavy system, a few seconds of delay acceptable.

---

## A2) Fanout-on-write vs fanout-on-read

### Fanout-on-write
When a user posts, push that post into follower feed materializations.

**Pros**
- very fast reads
- good for heavy read traffic

**Cons**
- expensive writes
- terrible for celebrity users with millions of followers

### Fanout-on-read
When a user opens the app, assemble the feed from followed users at read time.

**Pros**
- cheaper writes
- better for users with huge audiences

**Cons**
- more expensive reads
- can increase tail latency

### Practical hybrid
Use:
- fanout-on-write for normal users
- fanout-on-read for celebrity/high-fanout users

This is usually the strongest interview answer.

---

## A3) Data stores

Possible design:

- **User graph store**
  - who follows whom
- **Post store**
  - authoritative storage of posts
- **Feed cache / feed store**
  - precomputed feed entries for many users
- **Cache**
  - hot feed pages and user/profile data
- **Queue / stream**
  - async fanout and ranking updates

The post store can be SQL or NoSQL depending on access patterns.
The feed store is often denormalized and optimized for fast reads.

---

## A4) Caching strategy

Cache:
- first page of the feed
- user profile snippets
- post metadata
- ranking results or feed fragments

Use:
- cache-aside for hot feed pages
- short TTL
- versioning if ranking model or feed schema changes

Mitigations:
- jittered TTL
- stale-while-revalidate
- per-user feed cache keys like `feed:v1:{user_id}:page:1`

---

## A5) Celebrity problem

If a celebrity posts to 50 million followers, fanout-on-write becomes too expensive.

Mitigation:
- do not fully precompute those fanouts
- mark celebrity accounts as read-time merged sources
- combine:
  - precomputed feed for normal users
  - on-read merge for celebrity/high-fanout sources

This hybrid approach avoids write explosions.

---

## A6) Consistency choices

Strong consistency is usually not required for the entire feed.

Acceptable:
- eventual consistency for post appearance
- slight lag in like/comment counters
- re-ranking after refresh

Important:
- a user should usually see their own post soon after publishing
- monotonic reads are helpful so the feed does not “go backwards”

Possible mitigation:
- after posting, temporarily read own content from leader or inject locally into first page

---

## A7) Failure modes and mitigations

1. **Fanout queue backlog grows**
   - mitigation: scale consumers, backpressure, degrade to partial freshness

2. **Cache miss storm on hot feed pages**
   - mitigation: stale-while-revalidate, jittered TTL, request coalescing

3. **One hot user dominates writes**
   - mitigation: celebrity read-time handling, partition queues by user id, rate control

---

## A8) Evolution at 10x scale

- shard post storage by user id or region
- partition fanout queues
- introduce ranking pipelines
- separate feed serving from write ingestion
- use multi-tier caching
- serve some content from region-local read replicas/caches
- improve observability around feed freshness and queue lag

---

# Full Solution (high-level design)

## Components

- Client App
- Feed API
- Cache
- Feed Store / Timeline Store
- Post Store
- Follower Graph Store
- Fanout Workers
- Event Queue / Stream
- Ranking Service (optional)

## Diagram

```mermaid
flowchart LR
  C[Client App] --> F[Feed API]
  F --> CA[(Cache)]
  F --> FS[(Feed Store)]
  F --> PS[(Post Store)]
  F --> GS[(Follower Graph Store)]

  PS --> Q[(Event Queue / Stream)]
  Q --> W[Fanout Workers]
  W --> FS

  F --> R[Ranking Service]
````

## Read path

1. client requests page 1 of the feed
2. Feed API checks cache
3. on hit, return immediately
4. on miss, read from feed store
5. merge in celebrity/read-time sources if needed
6. cache result with short TTL
7. return

## Write path

1. user publishes a post
2. store post in authoritative post store
3. emit event to queue
4. fanout workers update follower feed entries for standard users
5. celebrity sources are not fully fanned out; they are merged at read time

## Trade-offs

* hybrid fanout improves scalability but increases system complexity
* eventual consistency is acceptable for most feed freshness
* cache is essential for low latency but adds invalidation and stampede risks
* ranking quality competes with latency budget

## Quick “Interview-style” one-liners

* **Feed strategy:** hybrid fanout-on-write + fanout-on-read for celebrities
* **Storage:** authoritative post store + denormalized feed store
* **Caching:** cache first page aggressively
* **Consistency:** eventual is acceptable, but preserve near read-after-write for own posts
* **Scalability:** partition queues, shard stores, isolate hot users

```
