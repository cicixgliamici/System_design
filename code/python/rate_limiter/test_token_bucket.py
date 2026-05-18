"""
Tests for the token bucket rate-limiter.

=============================================================================
TESTING STRATEGY: CLOCK INJECTION
=============================================================================

TokenBucket.create() accepts an optional `clock` parameter (a callable
returning a float). In tests we pass a simple lambda or a FakeClock
so we can control time without sleeping.

This is the same pattern used across the Python layer:
  - code/python/resilience/test_circuit_breaker.py  (FakeClock)
  - code/python/cache/test_cache_aside.py            (patch on time.monotonic)

The approach here uses a mutable FakeClock that can be advanced between
assertions, making multi-step time-travel scenarios easy to read.

=============================================================================
WHAT THESE TESTS VERIFY
=============================================================================

test_initial_burst_capacity   — bucket starts full; all `capacity` requests pass
test_sixth_request_rejected   — the (capacity+1)th request fails (empty bucket)
test_refill_proportional      — tokens grow linearly with elapsed time
test_tokens_capped_at_capacity — tokens never exceed capacity, even after long gaps
test_retry_after_empty_bucket — correct wait time when bucket is empty
test_retry_after_partial      — correct wait time when bucket is partially full
test_retry_after_zero         — returns 0.0 when tokens are already sufficient
test_cost_greater_than_one    — requests can consume multiple tokens at once
test_invalid_cost_raises      — negative or zero cost raises ValueError
"""

import unittest
from .token_bucket import TokenBucket


class FakeClock:
    """
    Minimal controllable clock for testing.

    All token-bucket time operations happen relative to this clock,
    so we can simulate seconds passing without any real wall-clock delay.
    """

    def __init__(self, start: float = 0.0) -> None:
        self._time = start

    def now(self) -> float:
        return self._time

    def advance(self, seconds: float) -> None:
        """Move the clock forward by `seconds`."""
        self._time += seconds


class TestTokenBucket(unittest.TestCase):
    def _bucket(self, capacity: int = 5, refill_rate: float = 1.0) -> tuple:
        """
        Helper: create a TokenBucket with a FakeClock starting at t=0.
        Returns (bucket, clock) so tests can advance time freely.
        """
        clock = FakeClock(start=0.0)
        bucket = TokenBucket.create(
            capacity=capacity, refill_rate=refill_rate, clock=clock.now
        )
        return bucket, clock

    # ------------------------------------------------------------------
    # Initial burst behaviour
    # ------------------------------------------------------------------

    def test_initial_burst_capacity(self):
        """
        A freshly created bucket starts completely full.

        With capacity=5, exactly 5 consecutive requests should be allowed
        without advancing the clock (i.e., all tokens consumed immediately).

        This is the "burst" property: the bucket lets a burst of `capacity`
        requests through before throttling kicks in.
        """
        bucket, _ = self._bucket(capacity=5, refill_rate=1.0)
        for _ in range(5):
            self.assertTrue(
                bucket.allow(), "Expected request to be allowed during initial burst"
            )

    def test_sixth_request_rejected(self):
        """
        After the burst is exhausted, the next request must be rejected.

        This verifies that the bucket correctly enforces the capacity limit
        at t=0 before any refill has occurred.
        """
        bucket, _ = self._bucket(capacity=5)
        for _ in range(5):
            bucket.allow()
        self.assertFalse(
            bucket.allow(), "6th request should be rejected (bucket empty)"
        )

    # ------------------------------------------------------------------
    # Refill behaviour
    # ------------------------------------------------------------------

    def test_refill_proportional_to_elapsed_time(self):
        """
        Tokens must refill linearly: elapsed_seconds × refill_rate.

        Scenario (refill_rate=1.0 token/sec):
          - Consume all 5 tokens at t=0.
          - Advance to t=2.5 → 2.5 tokens available.
          - Allow() twice (2.0 tokens consumed) → 0.5 tokens remaining.
          - Allow() again → rejected (0.5 < 1.0).
        """
        bucket, clock = self._bucket(capacity=5, refill_rate=1.0)

        for _ in range(5):
            bucket.allow()
        self.assertFalse(bucket.allow())

        clock.advance(2.5)

        self.assertTrue(bucket.allow())  # 1.5 tokens remaining
        self.assertTrue(bucket.allow())  # 0.5 tokens remaining
        self.assertFalse(bucket.allow())  # not enough for 1.0

    def test_tokens_capped_at_capacity(self):
        """
        Even after a very long idle period, the token count must not exceed
        the bucket's capacity.

        Without this cap, a client that goes idle for an hour could then send
        3600 × refill_rate requests all at once — defeating the rate limit.
        The cap prevents this "credit accumulation" attack.
        """
        bucket, clock = self._bucket(capacity=5, refill_rate=1.0)

        clock.advance(
            100.0
        )  # 100 seconds of idle time → would be 100 tokens without cap

        snapshot = bucket.snapshot()
        self.assertEqual(snapshot["tokens"], 5.0, "Tokens must be capped at capacity")

    # ------------------------------------------------------------------
    # retry_after_seconds
    # ------------------------------------------------------------------

    def test_retry_after_empty_bucket(self):
        """
        When the bucket is empty, retry_after_seconds() must return the exact
        time needed to accumulate one token at the configured refill_rate.

        With refill_rate=1.0 and tokens=0.0: wait = 1.0 / 1.0 = 1.0 second.
        """
        bucket, _ = self._bucket(capacity=5, refill_rate=1.0)

        for _ in range(5):
            bucket.allow()

        self.assertAlmostEqual(bucket.retry_after_seconds(), 1.0)

    def test_retry_after_partial_fill(self):
        """
        When the bucket has 0.5 tokens and we need 1.0, the wait is 0.5s.

        This tests fractional token arithmetic, which is important for
        high refill_rate buckets or fractional cost requests.
        """
        bucket, clock = self._bucket(capacity=5, refill_rate=1.0)

        for _ in range(5):
            bucket.allow()  # exhaust at t=0

        clock.advance(0.5)  # 0.5 tokens accumulated

        self.assertAlmostEqual(bucket.retry_after_seconds(), 0.5)

    def test_retry_after_returns_zero_when_tokens_available(self):
        """
        If the bucket has enough tokens, retry_after_seconds() must return 0.0
        (no wait required). This is the signal to clients to retry immediately.
        """
        bucket, _ = self._bucket(capacity=5)
        self.assertEqual(bucket.retry_after_seconds(), 0.0)

    # ------------------------------------------------------------------
    # Variable cost requests
    # ------------------------------------------------------------------

    def test_cost_greater_than_one(self):
        """
        Requests can consume more than one token (e.g., heavy operations).

        With capacity=5 and cost=3, only one such request fits in the full
        bucket (5 tokens). A second request with cost=3 must be rejected
        because only 2 tokens remain.

        This models APIs where different endpoints have different costs:
        e.g., a bulk export costs 5 tokens, a single GET costs 1 token.
        """
        bucket, _ = self._bucket(capacity=5)

        self.assertTrue(bucket.allow(cost=3.0))  # 2 tokens remaining
        self.assertFalse(bucket.allow(cost=3.0))  # 2 < 3 → rejected

    def test_invalid_cost_raises_value_error(self):
        """
        A non-positive cost is a programming error and must raise ValueError.

        Accepting cost=0 silently would mean requests are "free" (always pass),
        which defeats the purpose of rate limiting.
        """
        bucket, _ = self._bucket()

        with self.assertRaises(ValueError):
            bucket.allow(cost=0)

        with self.assertRaises(ValueError):
            bucket.allow(cost=-1)


if __name__ == "__main__":
    unittest.main()
