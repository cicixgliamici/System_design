"""
Educational token bucket implementation.

=============================================================================
WHAT IS A TOKEN BUCKET?
=============================================================================

A token bucket is a rate-limiting algorithm. Imagine a bucket that:
  - holds a maximum of `capacity` tokens
  - refills at a steady rate of `refill_rate` tokens per second
  - starts full

Each incoming request must consume one (or more) tokens to be allowed.
If the bucket has enough tokens, the request is accepted and tokens are
deducted. If not, the request is rejected.

Key properties:
  - BURSTING: because the bucket starts full and can accumulate tokens up to
    `capacity`, the algorithm naturally allows short bursts of traffic above
    the average rate. This is more user-friendly than strict per-second limits.
  - SMOOTHING: over time the average accepted rate converges to `refill_rate`,
    since that is how fast tokens are replenished.
  - SIMPLICITY: state is just two numbers (tokens, last_refill_time).

Compare with the Fixed Window algorithm (used in code/typescript/gateway/):
  Fixed Window is simpler but has an "edge burst" problem: a client can send
  2× the limit by timing requests at the boundary of two windows.
  Token Bucket does not have this issue.

=============================================================================
DESIGN DECISION: CLOCK INJECTION
=============================================================================

`TokenBucket.create()` and the internal `_refill()` method need to know the
current time to compute how many tokens to add since the last refill.

Instead of calling time.monotonic() directly, we accept a `clock` callable.
This is the same pattern used in:
  - code/python/resilience/circuit_breaker_demo.py
  - code/python/cache/cache_aside_demo.py

Benefits:
  - Tests can pass a controlled clock (a lambda returning a fixed float) to
    simulate the passage of time without any real sleep.
  - Tests run instantly and deterministically regardless of the machine load.
  - The production path is unchanged: callers that don't provide a clock get
    time.monotonic by default.

=============================================================================
DISTRIBUTED SYSTEMS NOTE
=============================================================================

This implementation is local/in-memory. It works for a single process.

In a distributed system with multiple replicas of the same service, each
replica would maintain its own separate bucket, so the aggregate limit would
be N × limit (where N is the number of replicas). To enforce a global limit
across all replicas you would typically:
  - Store the token count and last_refill_time in Redis using atomic Lua scripts
    or the INCR/EXPIRE commands.
  - Use consistent hashing to route the same client ID to the same replica,
    so each replica only handles a partition of clients.

See Theory/002_rate_limiting_retries_idempotency.md for the full design discussion.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

# A Clock is any zero-argument callable that returns the current time as a
# float (seconds). time.monotonic is preferred over time.time because it
# is guaranteed to be monotonically increasing — it never goes backward,
# even during NTP adjustments or daylight saving changes.
Clock = Callable[[], float]


@dataclass
class TokenBucket:
    """
    A single token bucket for one client / one resource.

    Fields (internal — use TokenBucket.create() to construct)
    ----------------------------------------------------------
    capacity         : float   — maximum number of tokens in the bucket
    refill_rate      : float   — tokens added per second
    tokens           : float   — current token count (may be fractional)
    last_refill_time : float   — timestamp of the last refill (from clock)
    clock            : Clock   — time source (injectable for testing)
    """

    capacity: float
    refill_rate: float       # tokens per second
    tokens: float
    last_refill_time: float
    clock: Clock

    @classmethod
    def create(
        cls,
        capacity: int,
        refill_rate: float,
        clock: Clock = time.monotonic,
    ) -> "TokenBucket":
        """
        Construct a TokenBucket that starts completely full.

        Parameters
        ----------
        capacity    : Maximum tokens (also the initial fill level).
        refill_rate : How many tokens are added per second.
        clock       : Time source. Defaults to time.monotonic. Pass a custom
                      callable in tests to control time without sleeping.
        """
        return cls(
            capacity=float(capacity),
            refill_rate=float(refill_rate),
            tokens=float(capacity),
            last_refill_time=clock(),
            clock=clock,
        )

    def _refill(self) -> None:
        """
        Add tokens proportional to the time elapsed since the last refill.

        Formula: new_tokens = elapsed_seconds × refill_rate
        The result is clamped to `capacity` so the bucket never overflows.

        This is called lazily — only when a request arrives — rather than on a
        background timer. This "lazy refill" approach avoids the need for any
        threading or scheduling, making the implementation simpler and easier
        to reason about.
        """
        now = self.clock()
        elapsed = now - self.last_refill_time

        if elapsed <= 0:
            # Clock did not advance (can happen in tests with a fixed clock).
            return

        added_tokens = elapsed * self.refill_rate
        # min() ensures we never exceed capacity.
        self.tokens = min(self.capacity, self.tokens + added_tokens)
        self.last_refill_time = now

    def allow(self, cost: float = 1.0) -> bool:
        """
        Attempt to consume `cost` tokens for an incoming request.

        Returns True  — request is allowed; tokens are deducted.
        Returns False — not enough tokens; request is rejected.

        Parameters
        ----------
        cost : Number of tokens this request consumes. Default is 1.0 (one
               request = one token). Use a higher value for more expensive
               operations (e.g., a bulk download might cost 5 tokens).
        """
        if cost <= 0:
            raise ValueError("cost must be positive")

        # Bring the token count up to date before checking.
        self._refill()

        if self.tokens >= cost:
            self.tokens -= cost
            return True

        # Not enough tokens — reject without modifying the bucket state.
        return False

    def retry_after_seconds(self, cost: float = 1.0) -> float:
        """
        Estimate how many seconds the caller should wait before retrying.

        If the bucket already has enough tokens, returns 0.0 (retry immediately).
        Otherwise returns the time needed to accumulate the missing tokens at
        the current refill_rate.

        This value can be returned to clients as the `Retry-After` HTTP header:
            HTTP/1.1 429 Too Many Requests
            Retry-After: 3
        """
        if cost <= 0:
            raise ValueError("cost must be positive")

        self._refill()

        if self.tokens >= cost:
            return 0.0

        missing_tokens = cost - self.tokens
        # Time = tokens_needed / refill_rate
        return missing_tokens / self.refill_rate

    def snapshot(self) -> dict[str, float]:
        """
        Return a debug-friendly snapshot of the bucket's current state.
        Useful for logging, metrics, and observability.

        Calling _refill() here ensures the snapshot reflects the current
        token count, not the count at the time of the last request.
        """
        self._refill()
        return {
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "tokens": self.tokens,
            "last_refill_time": self.last_refill_time,
        }


# ---------------------------------------------------------------------------
# Demo (run as: python -m rate_limiter.token_bucket)
# ---------------------------------------------------------------------------

def demo() -> None:
    """
    Demonstrates the burst-then-throttle behavior of a token bucket.

    Configuration:
      capacity    = 5  → allows an initial burst of 5 requests
      refill_rate = 1  → then ~1 request per second is sustained

    You should observe:
      - Requests 0-4: all allowed (consuming the initial tokens).
      - Requests 5+:  alternately allowed/rejected depending on refill timing.
    """
    import time as _time  # noqa: PLC0415 (local import for demo only)

    bucket = TokenBucket.create(capacity=5, refill_rate=1.0)

    for i in range(10):
        allowed = bucket.allow()
        retry_after = bucket.retry_after_seconds()
        state = bucket.snapshot()

        print(
            f"request={i:02d} "
            f"allowed={allowed} "
            f"tokens={state['tokens']:.2f} "
            f"retry_after={retry_after:.2f}s"
        )

        _time.sleep(0.35)


if __name__ == "__main__":
    demo()