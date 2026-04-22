import unittest
from unittest.mock import patch, MagicMock
from retry_with_jitter_demo import RetryConfig, compute_backoff_with_jitter, call_with_retry

class TestRetryPolicy(unittest.TestCase):
    def test_backoff_calculation(self):
        config = RetryConfig(
            base_delay_seconds=1.0,
            max_delay_seconds=10.0,
            jitter_ratio=0.0 # No jitter for deterministic test
        )
        
        # attempt 1: 1.0 * 2^0 = 1.0
        self.assertEqual(compute_backoff_with_jitter(1, config), 1.0)
        # attempt 2: 1.0 * 2^1 = 2.0
        self.assertEqual(compute_backoff_with_jitter(2, config), 2.0)
        # attempt 5: 1.0 * 2^4 = 16.0 -> capped at 10.0
        self.assertEqual(compute_backoff_with_jitter(5, config), 10.0)

    @patch('retry_with_jitter_demo.unstable_dependency')
    @patch('time.sleep')
    def test_retry_success_eventually(self, mock_sleep, mock_dep):
        config = RetryConfig(max_attempts=3)
        
        # Fail twice, then succeed
        mock_dep.side_effect = [RuntimeError("fail"), RuntimeError("fail"), "success"]
        
        result = call_with_retry(config)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_dep.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('retry_with_jitter_demo.unstable_dependency')
    @patch('time.sleep')
    def test_retry_exhaustion(self, mock_sleep, mock_dep):
        config = RetryConfig(max_attempts=3)
        
        # Always fail
        mock_dep.side_effect = RuntimeError("permanent fail")
        
        with self.assertRaises(RuntimeError):
            call_with_retry(config)
        
        self.assertEqual(mock_dep.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

if __name__ == '__main__':
    unittest.main()
