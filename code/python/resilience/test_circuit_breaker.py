import unittest
from unittest.mock import patch
from circuit_breaker_demo import CircuitBreaker, State

class TestCircuitBreaker(unittest.TestCase):
    def test_closes_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        
        # 2 failures shouldn't open it
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, State.CLOSED)
        
        # 3rd failure opens it
        cb.record_failure()
        self.assertEqual(cb.state, State.OPEN)
        self.assertFalse(cb.before_call())

    def test_transitions_to_half_open(self):
        with patch('time.monotonic') as mocked_time:
            mocked_time.return_value = 0.0
            cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=5.0)
            
            # Open the circuit
            for _ in range(3):
                cb.record_failure()
            self.assertEqual(cb.state, State.OPEN)
            
            # Jump 6 seconds
            mocked_time.return_value = 6.0
            
            # Should be allowed (transitions to half-open)
            self.assertTrue(cb.before_call())
            self.assertEqual(cb.state, State.HALF_OPEN)

    def test_half_open_success_closes(self):
        with patch('time.monotonic') as mocked_time:
            mocked_time.return_value = 0.0
            cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=5.0)
            
            # Open then move to half-open
            for _ in range(3): cb.record_failure()
            mocked_time.return_value = 6.0
            cb.before_call()
            
            # Success in half-open should close it
            cb.record_success()
            self.assertEqual(cb.state, State.CLOSED)
            self.assertEqual(cb.consecutive_failures, 0)

    def test_half_open_failure_opens_immediately(self):
        with patch('time.monotonic') as mocked_time:
            mocked_time.return_value = 0.0
            cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=5.0)
            
            # Open then move to half-open
            for _ in range(3): cb.record_failure()
            mocked_time.return_value = 6.0
            cb.before_call()
            
            # Failure in half-open should immediately re-open (no threshold check)
            cb.record_failure()
            self.assertEqual(cb.state, State.OPEN)

if __name__ == '__main__':
    unittest.main()
