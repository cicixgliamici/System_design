# Consensus and Leader Election (Practical Basics)

## Why this topic matters

Many distributed systems need a single decision that all healthy nodes eventually agree on:

- who is the current leader?
- which config version is valid?
- can this write be committed?

Without consensus, split-brain behavior can corrupt state.

---

## Consensus in one sentence

**Consensus** means multiple nodes agree on the same sequence of decisions, even with crashes and message delays (within model assumptions).

Popular protocols in practice:
- Raft
- Paxos family

---

## Leader election

A cluster often elects one node as leader to simplify writes and coordination.

Typical properties to expect:

- at most one leader per term/epoch
- followers reject stale leaders
- leadership can change after failures/timeouts

---

## Terms, logs, and commit (Raft-like mental model)

Useful mental model:

1. leader receives a command
2. leader appends command to replicated log
3. followers acknowledge replication
4. once quorum acknowledges, entry is committed
5. committed entry is applied to state machine

This gives safety first, availability second under partitions.

---

## Quorum intuition

With `N` replicas, quorum is usually `floor(N/2) + 1`.

Why it helps:
- any two quorums overlap
- overlapping node carries latest committed knowledge

Example: `N=5`, quorum is `3`.

---

## Failure modes to discuss

1. Leader crash
   - timeout triggers new election
2. Network partition
   - minority side cannot form quorum
3. Slow follower
   - catch-up via log replication/backfill

---

## Trade-offs

Pros:
- strong coordination guarantees
- predictable recovery semantics

Costs:
- added write latency (replication + quorum)
- operational complexity
- careful timeout tuning required

---

## Interview angle

Strong answers clarify:

- read/write consistency expectations
- quorum size and fault tolerance target
- behavior during partitions
- what happens to in-flight writes on leader failover
