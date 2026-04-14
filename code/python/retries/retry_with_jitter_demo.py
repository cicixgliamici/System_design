"""
Educational retry demo with exponential backoff + jitter.

Why this file exists:
- show a practical retry policy for transient failures
- explain each step with comments for study purposes
- keep the code runnable in isolation
"""

from __future__ import annotations

# Standard library imports only (simple educational setup).
import random
import time
from dataclasses import dataclass


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    # Maximum number of attempts (first try included).
    max_attempts: int = 5
    # Base delay (in seconds) used by exponential backoff.
    base_delay_seconds: float = 0.2
    # Upper bound to avoid unbounded sleep growth.
    max_delay_seconds: float = 2.0
    # Randomness factor to spread retries across clients.
    jitter_ratio: float = 0.25


def compute_backoff_with_jitter(attempt: int, config: RetryConfig) -> float:
    """
    Compute delay for the given attempt index.

    attempt=1 means "before second request".
    """
    # Exponential backoff: base * 2^(attempt-1)
    raw_delay = config.base_delay_seconds * (2 ** (attempt - 1))

    # Cap delay so latency doesn't explode.
    capped_delay = min(raw_delay, config.max_delay_seconds)

    # Jitter range is +- (capped_delay * jitter_ratio).
    jitter_delta = capped_delay * config.jitter_ratio

    # Uniform jitter to avoid synchronized retries.
    jitter = random.uniform(-jitter_delta, jitter_delta)

    # Sleep must never be negative.
    return max(0.0, capped_delay + jitter)


def unstable_dependency() -> str:
    """
    Simulate a dependency that fails transiently.

    About 50% chance to raise an exception.
    """
    if random.random() < 0.5:
        raise RuntimeError("temporary upstream error")

    return "success"


def call_with_retry(config: RetryConfig) -> str:
    """Execute unstable_dependency using the configured retry policy."""

    # Loop over all attempts, including the initial request.
    for attempt in range(1, config.max_attempts + 1):
        try:
            # Try the call.
            result = unstable_dependency()
            print(f"attempt={attempt} -> {result}")
            return result
        except RuntimeError as exc:
            # If this was the last attempt, surface the error.
            if attempt == config.max_attempts:
                print(f"attempt={attempt} -> failed permanently: {exc}")
                raise

            # Compute backoff delay before next attempt.
            delay = compute_backoff_with_jitter(attempt, config)
            print(
                f"attempt={attempt} -> transient error: {exc}; "
                f"retrying in {delay:.3f}s"
            )

            # Sleep before retrying.
            time.sleep(delay)

    # Defensive fallback (normally unreachable due return/raise above).
    raise RuntimeError("unreachable retry state")


def demo() -> None:
    """Run the demo with deterministic seed for repeatable study output."""

    # Deterministic seed so output is easier to compare while learning.
    random.seed(11)

    # Create policy configuration.
    config = RetryConfig(
        max_attempts=5,
        base_delay_seconds=0.2,
        max_delay_seconds=1.5,
        jitter_ratio=0.3,
    )

    # Execute call with retry behavior.
    call_with_retry(config)


if __name__ == "__main__":
    # Entry point for local execution: python retry_with_jitter_demo.py
    demo()
