"""
Educational token bucket implementation for the System_design repository.

Goals:
- simple enough to read in a few minutes
- explicit state transitions
- useful to connect theory with practice

This implementation is local/in-memory.
In a distributed system, the same logic would usually live in Redis
or another shared store with atomic updates.
"""

from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass
class TokenBucket:
    capacity: float
    refill_rate: float  # tokens per second
    tokens: float
    last_refill_time: float

    @classmethod
    def create(cls, capacity: int, refill_rate: float) -> "TokenBucket":
        now = time.monotonic()
        return cls(
            capacity=float(capacity),
            refill_rate=float(refill_rate),
            tokens=float(capacity),
            last_refill_time=now,
        )

    def _refill(self) -> None:
        """
        Add tokens according to elapsed time, up to the bucket capacity.
        """
        now = time.monotonic()
        elapsed = now - self.last_refill_time

        if elapsed <= 0:
            return

        added_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + added_tokens)
        self.last_refill_time = now

    def allow(self, cost: float = 1.0) -> bool:
        """
        Return True if a request costing `cost` tokens can be accepted.
        Otherwise return False.
        """
        if cost <= 0:
            raise ValueError("cost must be positive")

        self._refill()

        if self.tokens >= cost:
            self.tokens -= cost
            return True

        return False

    def retry_after_seconds(self, cost: float = 1.0) -> float:
        """
        Estimate how many seconds are needed before `cost` tokens become available.
        """
        if cost <= 0:
            raise ValueError("cost must be positive")

        self._refill()

        if self.tokens >= cost:
            return 0.0

        missing_tokens = cost - self.tokens
        return missing_tokens / self.refill_rate

    def snapshot(self) -> dict[str, float]:
        """
        Return a debug-friendly view of the internal state.
        """
        self._refill()
        return {
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "tokens": self.tokens,
            "last_refill_time": self.last_refill_time,
        }


def demo() -> None:
    """
    Small demonstration:
    - capacity = 5
    - refill rate = 1 token/sec

    This allows an initial burst of 5 requests,
    then roughly 1 request per second.
    """
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

        time.sleep(0.35)


if __name__ == "__main__":
    demo()