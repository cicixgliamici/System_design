"""
Educational circuit breaker implementation.

=============================================================================
WHAT IS A CIRCUIT BREAKER?
=============================================================================

A circuit breaker is a resilience pattern that prevents a service from
repeatedly calling a dependency that is known to be failing. It works like an
electrical circuit breaker: when too many failures are detected, the circuit
"trips" (opens) and subsequent calls are rejected immediately without even
reaching the failing dependency. After a configurable timeout, it allows a
small number of trial calls through to check if the dependency has recovered.

This avoids:
  - Wasting thread/goroutine resources on calls that will likely fail anyway.
  - Cascading failures: if service A calls B and B is slow/down, A accumulates
    blocked threads, which then starves A's other callers, and so on.
  - Making a struggling downstream service even worse by hammering it.

=============================================================================
THE THREE STATES
=============================================================================

                   failures >= threshold
     CLOSED  ──────────────────────────────►  OPEN
       ▲                                         │
       │                                         │ timeout elapsed
       │                                         ▼
       └──────────────────────────────────  HALF_OPEN
              first probe succeeds               │
                                                 │ probe fails
                                                 ▼
                                              OPEN (reset timer)

  CLOSED    — Normal operation. Calls go through. Failures are counted.
  OPEN      — All calls are rejected immediately (fast-fail). No downstream
              load is generated. The breaker waits for recovery_timeout.
  HALF_OPEN — A small number of trial calls are allowed. If they succeed the
              breaker transitions back to CLOSED. If any fails, it re-opens.

=============================================================================
DESIGN DECISION: CLOCK INJECTION
=============================================================================

Instead of calling time.monotonic() directly inside the class, we accept a
`clock` callable at construction time. This is a classic dependency injection
pattern. Its main benefit is testability:

    Without injection (bad for tests):
        - Tests must use unittest.mock.patch, which patches the module-level
          function. This is fragile and ties tests to internal implementation
          details.
        - Tests become slow if they ever need to wait for real time to pass.

    With injection (good for tests):
        - Tests pass a simple lambda that returns a controlled timestamp.
        - No patching required. No sleeps. Tests are deterministic and fast.
        - The production code uses time.monotonic by default, so behavior
          is unchanged for callers that do not provide a clock.

This pattern is also used in the cache-aside module (code/python/cache/) and
the token bucket module (code/python/rate_limiter/).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class State(str, Enum):
    """The three states of the circuit breaker finite-state machine."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# A Clock is any callable that returns the current time as a float (seconds).
# Using time.monotonic is the standard choice for measuring elapsed durations
# because it is not affected by system clock adjustments (NTP, DST, etc.).
Clock = Callable[[], float]


@dataclass
class CircuitBreaker:
    """
    A simple, educational circuit breaker.

    Parameters
    ----------
    failure_threshold : int
        How many consecutive failures are needed to trip the breaker (CLOSED →
        OPEN). Defaults to 3.
    recovery_timeout_seconds : float
        How long (in seconds) the breaker stays OPEN before allowing a trial
        call (transition to HALF_OPEN). Defaults to 2.0.
    half_open_max_calls : int
        Maximum number of trial calls allowed while HALF_OPEN. Once this limit
        is reached the breaker blocks further calls until one of the ongoing
        trials succeeds or fails. Defaults to 2.
    clock : Clock
        A callable returning the current time. Defaults to time.monotonic.
        Inject a custom clock in tests to avoid real sleeps.

    Usage
    -----
    cb = CircuitBreaker()

    if cb.before_call():
        try:
            result = call_downstream()
            cb.record_success()
        except Exception:
            cb.record_failure()
    else:
        # circuit is open — fast-fail without touching the downstream
        raise CircuitOpenError(...)
    """

    # --- Configuration (set at construction time) ---
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 2.0
    half_open_max_calls: int = 2

    # --- Runtime state (managed internally) ---
    state: State = State.CLOSED
    consecutive_failures: int = 0
    opened_at: float = 0.0
    half_open_calls: int = 0

    # Clock is last because dataclass field ordering requires fields with
    # defaults to come after fields without defaults.  We use field() with a
    # default_factory so that each instance gets its own reference to the
    # default clock, avoiding any shared-state issues.
    clock: Clock = field(default_factory=lambda: time.monotonic)

    # ------------------------------------------------------------------
    # Private state-transition helpers
    # ------------------------------------------------------------------

    def _transition_to_open(self) -> None:
        """
        Trip the breaker: move to OPEN and record the time the circuit opened.
        We reset half_open_calls so the counter is clean for the next HALF_OPEN
        window.
        """
        self.state = State.OPEN
        self.opened_at = self.clock()  # Use injected clock, not time.monotonic
        self.half_open_calls = 0

    def _transition_to_half_open_if_ready(self) -> None:
        """
        Check whether the recovery timeout has elapsed since the circuit opened.
        If so, move to HALF_OPEN to allow trial calls.

        This is called at the start of every before_call() so that the breaker
        automatically "wakes up" after the timeout without needing a background
        thread or timer.
        """
        if self.state != State.OPEN:
            return  # Only relevant when the circuit is open

        elapsed = self.clock() - self.opened_at
        if elapsed >= self.recovery_timeout_seconds:
            self.state = State.HALF_OPEN
            self.half_open_calls = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def before_call(self) -> bool:
        """
        Decide whether a call should be allowed through.

        Returns True  — the call is permitted (circuit is CLOSED or HALF_OPEN
                         with remaining trial capacity).
        Returns False — the call is blocked (circuit is OPEN, or HALF_OPEN
                         trial capacity is exhausted).

        Side effects:
          - May transition OPEN → HALF_OPEN if the timeout has elapsed.
          - Increments half_open_calls when a trial call is granted.
        """
        # Always check if the timeout has elapsed first.
        self._transition_to_half_open_if_ready()

        if self.state == State.OPEN:
            # Circuit is open and timeout has not elapsed yet — reject.
            return False

        if self.state == State.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                # We've already issued the maximum number of trial calls.
                # Block until one of them resolves (success or failure).
                return False
            # Grant a trial call and count it.
            self.half_open_calls += 1

        # CLOSED state, or HALF_OPEN with remaining capacity — allow.
        return True

    def record_success(self) -> None:
        """
        Notify the breaker that the last call succeeded.

        In CLOSED state   — resets the consecutive failure counter.
        In HALF_OPEN state — closes the circuit (recovery confirmed).
        In OPEN state     — should not happen in normal usage, but resets
                             anyway for robustness.
        """
        self.consecutive_failures = 0

        if self.state in (State.OPEN, State.HALF_OPEN):
            # Recovery confirmed: resume normal operation.
            self.state = State.CLOSED
            self.half_open_calls = 0

    def record_failure(self) -> None:
        """
        Notify the breaker that the last call failed.

        In CLOSED state   — increments the failure counter; trips the breaker
                             if the threshold is reached.
        In HALF_OPEN state — the probe failed, so we immediately re-open the
                             circuit (reset the recovery timer).
        In OPEN state     — should not happen (before_call would have blocked
                             the call), but handled gracefully.
        """
        if self.state == State.HALF_OPEN:
            # Trial call failed — not ready to recover yet; re-open.
            self._transition_to_open()
            return

        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self._transition_to_open()


# ---------------------------------------------------------------------------
# Demo (run as: python -m resilience.circuit_breaker_demo)
# ---------------------------------------------------------------------------

def flaky_dependency() -> str:
    """
    Simulates an unreliable downstream service.
    About 40% of calls raise a RuntimeError (timeout simulation).
    """
    if random.random() < 0.4:
        raise RuntimeError("dependency timeout")
    return "ok"


def demo() -> None:
    """
    Runs a short simulation with a fixed random seed so the output is
    reproducible. You can observe the breaker:
      1. Opening after repeated failures.
      2. Blocking calls while OPEN.
      3. Transitioning to HALF_OPEN after the timeout.
      4. Closing again on a successful probe.
    """
    random.seed(7)

    # Use a real wall-clock for the demo (unlike tests, which inject a fake clock).
    cb = CircuitBreaker(recovery_timeout_seconds=2.0)

    for i in range(20):
        if not cb.before_call():
            print(f"request={i:02d} blocked  state={cb.state}")
            time.sleep(0.35)
            continue

        try:
            result = flaky_dependency()
            cb.record_success()
            print(f"request={i:02d} result={result}  state={cb.state}")
        except RuntimeError as exc:
            cb.record_failure()
            print(f"request={i:02d} error={exc}  state={cb.state}")

        time.sleep(0.35)


if __name__ == "__main__":
    demo()
