# Search Systems: Inverted Index Basics

## Why this topic matters

Many products need search beyond exact key lookups:

- e-commerce product discovery
- documentation portals
- knowledge bases
- social content search

Relational databases are great for transactional reads/writes, but full-text ranking is usually handled by a dedicated search engine.

---

## Core concept: inverted index

An **inverted index** maps terms to documents.

Instead of:
- document → words

we keep:
- word → list of document IDs (+ optional metadata like positions/frequencies)

Example:

- `"cache" -> [doc2, doc9, doc15]`
- `"latency" -> [doc1, doc2, doc7]`

This makes keyword retrieval fast at scale.

---

## Typical indexing pipeline

1. ingest source documents (DB/events/files)
2. tokenize text
3. normalize terms (lowercase, stemming, stop-word filtering)
4. build/update posting lists
5. store index shards + replicas

For near-real-time systems, updates happen continuously in small batches.

---

## Query flow (simplified)

1. parse query (`"distributed cache"`)
2. find posting lists for each term
3. intersect/union candidate documents
4. score results (e.g., BM25 + business signals)
5. apply filters/facets/sorting
6. return top-k results

---

## Relevance signals

Common ranking inputs:

- lexical relevance (term frequency, field boosts)
- freshness (newer content)
- popularity (click-through, purchases)
- personalization (if enabled)

Trade-off: richer ranking often increases latency and complexity.

---

## Architectural patterns

- **dual-write avoidance**: prefer event-driven indexing from a source-of-truth DB
- **eventual consistency**: search index is often slightly behind primary DB
- **index versioning**: build new index, then atomically swap aliases
- **shard strategy**: shard by document ID/hash; replicate for availability

---

## Failure modes to discuss

1. indexing lag spike → stale search results
2. hot shard → uneven latency
3. bad analyzer config → relevance degradation

Mitigations include queue backpressure controls, shard rebalancing, and canary evaluation of relevance changes.

---

## Interview angle

Good answers clarify:

- freshness requirement (seconds vs minutes)
- acceptable eventual consistency window
- top query patterns (keyword, prefix, typo tolerance)
- ranking objective (relevance, revenue, engagement)
