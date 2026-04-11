"""
Educational circuit breaker demo.

States:
- CLOSED: requests flow normally
- OPEN: requests are rejected fast
- HALF_OPEN: allow a small number of trial calls
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
import time


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 2.0
    half_open_max_calls: int = 2

    state: State = State.CLOSED
    consecutive_failures: int = 0
    opened_at: float = 0.0
    half_open_calls: int = 0

    def _transition_to_open(self) -> None:
        self.state = State.OPEN
        self.opened_at = time.monotonic()
        self.half_open_calls = 0

    def _transition_to_half_open_if_ready(self) -> None:
        if self.state != State.OPEN:
            return

        if time.monotonic() - self.opened_at >= self.recovery_timeout_seconds:
            self.state = State.HALF_OPEN
            self.half_open_calls = 0

    def before_call(self) -> bool:
        self._transition_to_half_open_if_ready()

        if self.state == State.OPEN:
            return False

        if self.state == State.HALF_OPEN and self.half_open_calls >= self.half_open_max_calls:
            return False

        if self.state == State.HALF_OPEN:
            self.half_open_calls += 1

        return True

    def record_success(self) -> None:
        self.consecutive_failures = 0

        if self.state in (State.OPEN, State.HALF_OPEN):
            self.state = State.CLOSED
            self.half_open_calls = 0

    def record_failure(self) -> None:
        if self.state == State.HALF_OPEN:
            self._transition_to_open()
            return

        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self._transition_to_open()


def flaky_dependency() -> str:
    # About 40% simulated failures.
    if random.random() < 0.4:
        raise RuntimeError("dependency timeout")
    return "ok"


def demo() -> None:
    random.seed(7)
    cb = CircuitBreaker()

    for i in range(20):
        if not cb.before_call():
            print(f"request={i:02d} blocked state={cb.state}")
            time.sleep(0.35)
            continue

        try:
            result = flaky_dependency()
            cb.record_success()
            print(f"request={i:02d} result={result} state={cb.state}")
        except RuntimeError as exc:
            cb.record_failure()
            print(f"request={i:02d} error={exc} state={cb.state}")

        time.sleep(0.35)


if __name__ == "__main__":
    demo()
