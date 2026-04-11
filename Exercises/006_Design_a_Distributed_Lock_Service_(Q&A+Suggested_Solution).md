# Exercise 06 — Design a Distributed Lock Service (Q&A + Suggested Solution)

## Scenario

You need a distributed lock to protect critical jobs:

- only one worker processes a billing batch at a time
- lock auto-expires if worker crashes
- lock owner periodically renews lease

## Requirements

- Acquisition latency p95 < 30ms
- Handle 20k lock operations/s (acquire/renew/release)
- Prevent stale owner from releasing someone else's lock
- Survive single-node failures

---

## Questions

1. Which clarifying questions are essential?
2. What lock semantics do you define (lease, fairness, reentrancy)?
3. What data model and atomic operations are needed?
4. How do you prevent split-brain ownership issues?
5. How do renew and release work safely?
6. What failure modes and mitigations should be included?

---

## Suggested Answers

### A1) Clarifying questions

- Is strict mutual exclusion mandatory, or occasional duplicates tolerated?
- How long can lock holders run normally?
- Do we need FIFO fairness?
- Single region or multi-region?
- What should clients do on lock contention?

Assumption: single region; strict mutual exclusion for business-critical jobs.

### A2) Semantics

Define lock as a **lease**:

- `acquire(key, ttl)` returns `(granted, fence_token)`
- owner must renew before `ttl` expires
- expired lock can be acquired by others

Avoid claiming strict fairness initially; prioritize correctness and simplicity.

### A3) Data model + atomicity

Per lock key store:

- `owner_id`
- `expires_at`
- `fence_token` (monotonic increasing)

Atomic operations needed:

- acquire if lock missing/expired
- renew only if `owner_id` matches current owner
- release only if `owner_id` matches current owner

### A4) Split-brain protection

Use **fencing tokens**:

- each successful acquire increments token
- downstream protected resources reject old tokens

Even if an old owner resumes after network pause, stale token prevents unsafe writes.

### A5) Safe renew/release

- Renew: compare-and-set on owner ID + unexpired lease
- Release: delete only when owner ID matches
- Never allow blind delete by key alone

### A6) Failure modes

1. Lock node crash:
   - replicated store (e.g., quorum-based or managed KV)
2. Client pause/GC stop-the-world:
   - short leases + fencing tokens
3. Clock skew issues:
   - prefer store-side time and lease checks in one place
