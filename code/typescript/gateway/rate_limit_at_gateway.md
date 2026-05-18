# API Gateway Rate Limiter (Fixed Window)

This module demonstrates a basic rate limiting mechanism operating at an API Gateway layer, typically used as a first line of defense before traffic reaches internal microservices.

## How it works

It uses the **Fixed Window Counter** algorithm. Time is divided into fixed intervals (windows) of a specific length (e.g., 60 seconds). Each window has a counter per user (or IP, API Key).
1. When a request arrives, the current window is determined based on the timestamp.
2. The counter for that window is incremented.
3. If the counter exceeds the allowed limit, the request is rejected (HTTP 429).

## Trade-offs

**Pros:**
*   **Simplicity:** Extremely easy to understand and implement.
*   **Low Overhead:** Requires minimal memory (just a timestamp key and an integer counter).

**Cons:**
*   **Boundary Spikes (The "Thundering Herd"):** A user can exhaust their limit at the very end of one window (e.g., 0:59) and then immediately send another full limit of requests at the start of the next window (e.g., 1:00). This means the system can theoretically receive $2 \times \text{limit}$ requests within a very short timeframe.

## Implementation Details

*   In a real-world scenario, this state would be stored in a centralized, fast key-value store like Redis (using `INCR` and `EXPIRE` commands) so that multiple gateway instances share the same limits. This demo uses an in-memory `Map` for simplicity.
*   If boundary spikes become a critical issue in production, the implementation should be upgraded to a Sliding Window Counter or a Token Bucket.

## See Also
*   [Theory: Rate Limiting](../../../Theory/002_rate_limiting_retries_idempotency.md)
*   [Theory: API Gateway](../../../Theory/009_API_Gateway_vs_Service_Mesh.md)
