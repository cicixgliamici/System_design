# System Design

[![CI](https://github.com/cicixgliamici/System_design/actions/workflows/ci.yml/badge.svg)](https://github.com/cicixgliamici/System_design/actions/workflows/ci.yml)

An educational repository about system design fundamentals, distributed systems reasoning, architectural patterns, and hands-on implementations.

The goal is to bridge theory and practice: every concept documented in the `Theory/` layer has a corresponding working implementation in the `code/` layer, with tests.

---

## Quick navigation

| Section | Description | Link |
|---|---|---|
| 📖 Theory | Core system design concepts | [`Theory/`](./Theory/README.md) |
| 💻 Code | Working implementations with tests | [`code/`](./code/README.md) |
| 🏗️ Case Studies | Structured design walkthroughs | [`Case_Studies/`](./Case_Studies/) |
| 📝 Exercises | Q&A prompts with suggested solutions | [`Exercises/`](./Exercises/) |

---

## Implemented modules

### Go

| Module | Concept | Source | Tests | Doc |
|---|---|---|---|---|
| `hashring` | Consistent Hashing | [consistent_hashing.go](./code/go/hashring/consistent_hashing.go) | ✅ | [.md](./code/go/hashring/consistent_hashing.md) |
| `loadbalancer` | Round-Robin Load Balancing | [round_robin.go](./code/go/loadbalancer/round_robin.go) | ✅ | [.md](./code/go/loadbalancer/round_robin.md) |
| `workerpool` | Worker Pool with Backpressure | [worker_pool_with_backpressure.go](./code/go/workerpool/worker_pool_with_backpressure.go) | ✅ | [.md](./code/go/workerpool/worker_pool.md) |

### Python

| Module | Concept | Source | Tests | Doc |
|---|---|---|---|---|
| `cache` | Cache-Aside Pattern (TTL) | [cache_aside_demo.py](./code/python/cache/cache_aside_demo.py) | ✅ | [.md](./code/python/cache/cache_aside_demo.md) |
| `rate_limiter` | Token Bucket | [token_bucket.py](./code/python/rate_limiter/token_bucket.py) | ✅ | [.md](./code/python/rate_limiter/token_bucket.md) |
| `resilience` | Circuit Breaker (3-state FSM) | [circuit_breaker_demo.py](./code/python/resilience/circuit_breaker_demo.py) | ✅ | [.md](./code/python/resilience/circuit_breaker_demo.md) |
| `retries` | Retry with Exponential Backoff + Jitter | [retry_with_jitter_demo.py](./code/python/retries/retry_with_jitter_demo.py) | ✅ | [.md](./code/python/retries/retry_with_jitter_demo.md) |

### TypeScript

| Module | Concept | Source | Tests | Doc |
|---|---|---|---|---|
| `gateway` | Fixed-Window Rate Limiter at API Gateway | [rate_limit_at_gateway.ts](./code/typescript/gateway/rate_limit_at_gateway.ts) | ✅ | [.md](./code/typescript/gateway/rate_limit_at_gateway.md) |
| `discovery` | In-Memory Service Registry | [simple_registry.ts](./code/typescript/discovery/simple_registry.ts) | ✅ | [.md](./code/typescript/discovery/simple_registry.md) |

---

## Theory coverage

| File | Topic |
|---|---|
| [000](./Theory/000_what_is_system_design_and_goal.md) | What is System Design and the goal of this repo |
| [001](./Theory/001_first_fundamentals.md) | First fundamentals: requirements, scaling, building blocks |
| [002](./Theory/002_rate_limiting_retries_idempotency.md) | Rate Limiting, Retries, Idempotency |
| [003](./Theory/003_Caching.md) | Caching: patterns, invalidation, stampede |
| [004](./Theory/004_Messaging.md) | Messaging: queues, pub-sub, delivery guarantees |
| [005](./Theory/005_Load_Balancing.md) | Load Balancing: algorithms, health checks, HA |
| [006](./Theory/006_Databases_Replication_Sharding.md) | Databases: replication, sharding |
| [007](./Theory/007_Consistency_CAP_and_Quorums.md) | Consistency, CAP theorem, Quorums |
| [008](./Theory/008_Observability_and_SLOs.md) | Observability and SLOs |
| [009](./Theory/009_API_Gateway_vs_Service_Mesh.md) | API Gateway vs Service Mesh |
| [010](./Theory/010_Search_and_Inverted_Index_Basics.md) | Search and Inverted Index Basics |
| [011](./Theory/011_Consensus_and_Leader_Election.md) | Consensus and Leader Election |
| [012](./Theory/012_Data_Modeling_for_High_Scale.md) | Data Modeling for High Scale |

---

## Running tests

```bash
# Run all tests (Go + Python + TypeScript)
make test-all

# Per-language
make test-go
make test-python
make test-ts
```

---

## Repository goals

- Build a strong conceptual foundation in distributed systems
- Implement each key pattern in working, tested code
- Connect theory to practice through explicit cross-links
- Practice design reasoning through case studies and exercises

---

## License

MIT
