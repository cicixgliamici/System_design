# Retry with Exponential Backoff and Jitter

This module implements a robust retry mechanism to gracefully handle transient failures (e.g., temporary network glitches, 503 Service Unavailable) in distributed systems.

## How it works

When a call fails, retrying immediately is often a bad idea, especially under high load. Instead, this implementation uses:

1.  **Exponential Backoff:** The wait time between retries increases exponentially (e.g., $2^0, 2^1, 2^2...$). This gives the failing downstream service time to recover.
2.  **Jitter (Randomness):** A random factor is added to the backoff duration. Without jitter, if a service goes down, hundreds of clients might retry at the exact same exponential intervals, creating a "thundering herd" that immediately crashes the service again as soon as it recovers.

## Trade-offs

**Pros:**
*   **Protects Downstream Services:** Prevents overload during recovery phases.
*   **Increases Success Rate:** Effectively handles brief, transient errors.

**Cons:**
*   **Increased Tail Latency:** Retries inherently increase the response time for the client.
*   **Idempotency Required:** Retries should only be applied to idempotent operations (e.g., `GET`, `PUT`, `DELETE`, or `POST` with idempotency keys) to avoid unintended side effects like double-charging.

## Implementation Details

The implementation is provided as a Python decorator (`@retry_with_jitter`).
*   It supports a maximum number of retries (`max_retries`).
*   It calculates the backoff using `base_delay * (2 ** attempt)`.
*   It applies a random "Full Jitter" by selecting a sleep time uniformly between `0` and the calculated exponential backoff.
*   Like other resilience patterns in this repository, it supports a `sleep_fn` for deterministic unit testing without actual delays.

## See Also
*   [Theory: Retries and Idempotency](../../../Theory/002_rate_limiting_retries_idempotency.md)
