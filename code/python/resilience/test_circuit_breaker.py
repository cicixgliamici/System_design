"""
Tests for the circuit breaker finite-state machine.

=============================================================================
TESTING STRATEGY: CLOCK INJECTION
=============================================================================

The CircuitBreaker uses a `clock` parameter (a callable returning a float)
to read the current time. In production this defaults to time.monotonic.

In tests we inject a simple mutable object that acts as a controllable clock:

    clock = FakeClock(0.0)          # starts at t=0
    cb = CircuitBreaker(clock=clock.now)
    clock.advance(6.0)              # jump 6 seconds into the future

This approach is:
  - EXPLICIT: the dependency on time is visible in the CircuitBreaker signature.
  - DETERMINISTIC: no real sleep, no wall-clock drift, no flakiness.
  - FAST: the entire test suite runs in milliseconds.
  - NO PATCHING: unittest.mock.patch is not needed; no module-level side effects.

Compare with the alternative (patching time.monotonic globally):
    with patch('time.monotonic') as mock:
        mock.return_value = 0.0
        ...
  This works but is fragile: it patches ALL calls to time.monotonic in the
  entire process, not just the calls inside CircuitBreaker. If any other
  code also uses time.monotonic during the test, the mock may interfere.
  Clock injection avoids this problem entirely.

=============================================================================
TESTS ORGANISED BY STATE TRANSITION
=============================================================================

The tests cover the following FSM transitions:

  CLOSED → OPEN:           test_opens_after_failure_threshold
  OPEN   → HALF_OPEN:      test_transitions_to_half_open_after_timeout
  HALF_OPEN → CLOSED:      test_half_open_success_closes_circuit
  HALF_OPEN → OPEN:        test_half_open_failure_reopens_circuit
  CLOSED (no trip):        test_does_not_open_below_threshold
  OPEN (timeout pending):  test_stays_open_before_timeout
  HALF_OPEN (cap reached): test_half_open_blocks_after_max_calls
"""

import unittest
from .circuit_breaker_demo import CircuitBreaker, State


# ---------------------------------------------------------------------------
# Helper: a simple mutable clock for tests
# ---------------------------------------------------------------------------

class FakeClock:
    """
    A controllable time source for testing.

    Usage:
        clock = FakeClock(start=0.0)
        cb = CircuitBreaker(clock=clock.now)
        clock.advance(5.0)   # jump 5 seconds forward
    """

    def __init__(self, start: float = 0.0) -> None:
        self._time = start

    def now(self) -> float:
        """Return the current fake time."""
        return self._time

    def advance(self, seconds: float) -> None:
        """Move the clock forward by `seconds`."""
        self._time += seconds

    def set(self, t: float) -> None:
        """Set the clock to an absolute time `t`."""
        self._time = t


# ---------------------------------------------------------------------------
# Helper: build a CircuitBreaker in OPEN state without repeating setup code
# ---------------------------------------------------------------------------

def _make_open_breaker(
    clock: FakeClock,
    failure_threshold: int = 3,
    recovery_timeout_seconds: float = 5.0,
) -> CircuitBreaker:
    """
    Convenience factory: create a CircuitBreaker and immediately trip it by
    recording `failure_threshold` consecutive failures.
    """
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout_seconds=recovery_timeout_seconds,
        clock=clock.now,
    )
    for _ in range(failure_threshold):
        cb.record_failure()
    assert cb.state == State.OPEN, "Precondition: breaker must be OPEN"
    return cb


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestCircuitBreakerFSM(unittest.TestCase):
    """Tests that verify each state transition of the circuit breaker FSM."""

    # ------------------------------------------------------------------
    # CLOSED state behaviour
    # ------------------------------------------------------------------

    def test_starts_closed(self):
        """A freshly created breaker must be CLOSED and allow calls."""
        clock = FakeClock()
        cb = CircuitBreaker(clock=clock.now)
        self.assertEqual(cb.state, State.CLOSED)
        self.assertTrue(cb.before_call())

    def test_does_not_open_below_threshold(self):
        """
        Failures below the threshold must NOT trip the breaker.

        With threshold=3, two consecutive failures should keep the circuit CLOSED.
        This verifies the counter increments correctly without triggering early.
        """
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=3, clock=clock.now)

        cb.record_failure()
        cb.record_failure()

        self.assertEqual(cb.state, State.CLOSED)
        self.assertTrue(cb.before_call())

    def test_opens_after_failure_threshold(self):
        """
        Exactly `failure_threshold` consecutive failures must open the circuit.

        After tripping:
          - state must be OPEN
          - before_call() must return False (fast-fail)
        """
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=3, clock=clock.now)

        for _ in range(3):
            cb.record_failure()

        self.assertEqual(cb.state, State.OPEN)
        self.assertFalse(cb.before_call())

    def test_success_resets_failure_counter(self):
        """
        A success in CLOSED state must reset consecutive_failures to zero.

        This ensures that non-consecutive failures do not accumulate toward
        the threshold (e.g., 2 failures + 1 success + 2 failures should NOT
        trip a breaker with threshold=3).
        """
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=3, clock=clock.now)

        cb.record_failure()
        cb.record_failure()
        # Success resets the counter
        cb.record_success()
        # Two more failures — should still be below threshold
        cb.record_failure()
        cb.record_failure()

        self.assertEqual(cb.state, State.CLOSED)
        self.assertEqual(cb.consecutive_failures, 2)

    # ------------------------------------------------------------------
    # OPEN state behaviour
    # ------------------------------------------------------------------

    def test_stays_open_before_timeout(self):
        """
        The circuit must remain OPEN until recovery_timeout_seconds have elapsed.

        We advance the clock to just before the timeout boundary and confirm
        that before_call() still returns False.
        """
        clock = FakeClock(start=0.0)
        cb = _make_open_breaker(clock, recovery_timeout_seconds=5.0)

        # Advance to just before the timeout
        clock.advance(4.9)

        self.assertEqual(cb.state, State.OPEN)
        self.assertFalse(cb.before_call())

    # ------------------------------------------------------------------
    # OPEN → HALF_OPEN transition
    # ------------------------------------------------------------------

    def test_transitions_to_half_open_after_timeout(self):
        """
        After recovery_timeout_seconds have elapsed, before_call() must:
          - transition the state to HALF_OPEN
          - return True (first trial call is allowed)

        The transition happens lazily inside before_call() — no background
        thread is needed.
        """
        clock = FakeClock(start=0.0)
        cb = _make_open_breaker(clock, recovery_timeout_seconds=5.0)

        # Advance past the timeout
        clock.advance(6.0)

        allowed = cb.before_call()

        self.assertTrue(allowed)
        self.assertEqual(cb.state, State.HALF_OPEN)

    # ------------------------------------------------------------------
    # HALF_OPEN state behaviour
    # ------------------------------------------------------------------

    def test_half_open_allows_limited_trial_calls(self):
        """
        In HALF_OPEN state, at most `half_open_max_calls` calls should be allowed.
        Calls beyond that limit must be blocked until one trial resolves.
        """
        clock = FakeClock(start=0.0)
        cb = _make_open_breaker(clock, recovery_timeout_seconds=5.0)
        cb._CircuitBreaker__dict__ if False else None  # just a reference marker

        # Move to HALF_OPEN
        clock.advance(6.0)
        cb.before_call()  # trial call #1 — allowed

        # half_open_max_calls defaults to 2, so one more trial is allowed
        allowed_second = cb.before_call()  # trial call #2
        self.assertTrue(allowed_second)

        # The 3rd call exceeds max_calls — must be blocked
        blocked = cb.before_call()
        self.assertFalse(blocked)
        self.assertEqual(cb.state, State.HALF_OPEN)

    def test_half_open_success_closes_circuit(self):
        """
        A successful call in HALF_OPEN state must close the circuit.

        This verifies the recovery path: the downstream is healthy again,
        so normal operation can resume.
        """
        clock = FakeClock(start=0.0)
        cb = _make_open_breaker(clock, recovery_timeout_seconds=5.0)

        # Transition to HALF_OPEN
        clock.advance(6.0)
        cb.before_call()

        # Probe succeeds
        cb.record_success()

        self.assertEqual(cb.state, State.CLOSED)
        self.assertEqual(cb.consecutive_failures, 0)
        # After closing, calls should be allowed normally
        self.assertTrue(cb.before_call())

    def test_half_open_failure_reopens_circuit(self):
        """
        A failure in HALF_OPEN state must immediately re-open the circuit.

        The recovery timer is also reset, so the breaker waits another full
        recovery_timeout_seconds before trying again.
        """
        clock = FakeClock(start=0.0)
        cb = _make_open_breaker(clock, recovery_timeout_seconds=5.0)

        # Transition to HALF_OPEN
        clock.advance(6.0)
        cb.before_call()

        # Probe fails
        cb.record_failure()

        self.assertEqual(cb.state, State.OPEN)
        # The timer was reset to the current clock value (6.0),
        # so before_call() must still block until another 5 s pass.
        self.assertFalse(cb.before_call())

    def test_half_open_failure_resets_recovery_timer(self):
        """
        After a probe fails and the circuit re-opens, the recovery_timeout
        must restart from the moment of re-opening (not from the original open).

        Scenario:
          t=0    : circuit opens (3 failures)
          t=6    : circuit moves to HALF_OPEN (timeout elapsed)
          t=6    : probe fails → circuit re-opens, timer reset to t=6
          t=10   : only 4s elapsed since re-open (< 5s timeout) → still OPEN
          t=12   : 6s elapsed since re-open (> 5s timeout) → HALF_OPEN again
        """
        clock = FakeClock(start=0.0)
        cb = _make_open_breaker(clock, recovery_timeout_seconds=5.0)

        clock.advance(6.0)     # first timeout elapses
        cb.before_call()       # HALF_OPEN
        cb.record_failure()    # probe fails → OPEN again, timer reset to t=6

        clock.advance(4.0)     # now at t=10, only 4s since re-open
        self.assertFalse(cb.before_call())  # still OPEN

        clock.advance(2.0)     # now at t=12, 6s since re-open
        self.assertTrue(cb.before_call())   # HALF_OPEN again


if __name__ == "__main__":
    unittest.main()
