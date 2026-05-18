# Token Bucket Rate Limiter

This module implements the **Token Bucket** algorithm, a standard rate limiting mechanism used to control the rate of requests sent to a system.

## How it works

The token bucket conceptually consists of:
1.  **A Bucket** that holds a maximum number of tokens (`capacity`).
2.  **A Refill Rate** at which new tokens are added to the bucket (`refill_rate` in tokens per second).

When a request arrives, it attempts to consume a token:
- If a token is available, the request is allowed.
- If the bucket is empty, the request is rejected (or rate-limited).

## Trade-offs

**Pros:**
*   **Allows Bursts:** Unlike a strict fixed-window counter, a token bucket allows short bursts of traffic up to the bucket's capacity.
*   **Memory Efficient:** It only needs to store the current token count and the timestamp of the last refill, rather than a log of all requests (like the sliding window log).
*   **Smooth Rate:** Over time, it enforces a steady average rate while accommodating momentary spikes.

**Cons:**
*   **Tuning Complexity:** You must carefully tune both `capacity` and `refill_rate` to balance burst tolerance and downstream protection.

## Implementation Details

*   **Lazy Refill:** Instead of a background thread constantly adding tokens, the implementation calculates and adds the accumulated tokens lazily, exactly at the moment a request arrives. This drastically reduces CPU overhead.
*   **Clock Injection:** The class accepts an optional `clock` function (defaulting to `time.time`). This is a critical pattern for **deterministic testing**. By injecting a mock clock, our unit tests can simulate the passage of time instantly without using `time.sleep()`, preventing flaky and slow tests.

## See Also
*   [Theory: Rate Limiting](../../../Theory/002_rate_limiting_retries_idempotency.md)
