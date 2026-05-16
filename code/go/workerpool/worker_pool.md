# Worker Pool with Backpressure (Go)

## What this module demonstrates

This example shows a **worker pool** pattern: a fixed number of goroutines
(workers) that process jobs submitted through a shared buffered channel.

The key property modelled here is **backpressure**: when the queue is full,
the producer blocks rather than dropping work or crashing. This is an
intentional design choice that keeps the system honest about its capacity.

---

## Core concepts

### The problem it solves

When a system receives bursts of work it cannot immediately process, it needs
a strategy:

- **Drop** (fast but lossy)
- **Grow unboundedly** (risky — can exhaust memory)
- **Block the producer** (safe, honest, controllable) ← this implementation

A worker pool with a bounded queue implements the third option.

### Structure

```
Producer ──► [job channel (buffered)] ──► Worker 1
                                      ──► Worker 2
                                      ──► Worker 3
```

The channel capacity (`queueCapacity`) is the backpressure boundary.
If the channel is full, `Submit` blocks until a worker frees a slot.

---

## Key design decisions

| Decision | Reason |
|---|---|
| Buffered channel as the queue | Decouples producer from workers; allows bursting up to capacity |
| `sync.WaitGroup` for shutdown | Guarantees all in-flight jobs complete before `Shutdown` returns |
| `close(jobs)` to signal termination | Workers exit their `range` loop cleanly without sentinel values |
| Fixed worker count at construction | Simpler to reason about than dynamic scaling for this demo |

---

## Backpressure in practice

With `queueCapacity = 5` and `workerCount = 3`:

- The producer can submit up to 5 jobs without any worker being free.
- Job #6 blocks the producer until a worker picks up one of the queued jobs.
- This applies natural back-pressure to the upstream caller.

In production systems, you might instead return an error (fail-fast) rather
than blocking, to avoid cascading stalls. Both approaches are valid — the
right choice depends on whether the producer can tolerate latency.

---

## Interaction with other concepts

- **Rate limiting** (see [`code/python/rate_limiter/`](../../../python/rate_limiter/)) — a rate limiter
  can sit upstream to bound how fast jobs enter the pool.
- **Load balancing** — multiple worker pools can sit behind a load balancer
  to scale horizontally.
- **Observability** — in production, you'd instrument queue depth, worker
  utilization, and job processing latency.

---

## Theory reference

→ [`Theory/001_first_fundamentals.md`](../../../Theory/001_first_fundamentals.md)
(Section 4 — Scaling: vertical vs horizontal; building blocks overview)

---

## In one sentence

This code distributes jobs across a fixed pool of goroutines through a
bounded channel, so that the producer naturally slows down when workers are
saturated rather than overflowing the system.
