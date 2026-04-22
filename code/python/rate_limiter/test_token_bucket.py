import unittest
from unittest.mock import patch
from token_bucket import TokenBucket

class TestTokenBucket(unittest.TestCase):
    def test_burst_capacity(self):
        # Capacity 5, refill 1.0
        # Initial tokens = 5
        bucket = TokenBucket.create(capacity=5, refill_rate=1.0)
        
        # We should allow 5 requests immediately
        for _ in range(5):
            self.assertTrue(bucket.allow())
        
        # The 6th request should be denied
        self.assertFalse(bucket.allow())

    def test_refill_over_time(self):
        with patch('time.monotonic') as mocked_time:
            # Start at t=0
            mocked_time.return_value = 0.0
            bucket = TokenBucket.create(capacity=5, refill_rate=1.0)
            
            # Consume all
            for _ in range(5):
                bucket.allow()
            self.assertFalse(bucket.allow())
            
            # Jump to t=2.5 seconds
            mocked_time.return_value = 2.5
            
            # Should have 2.5 tokens now. Can allow 2 requests.
            self.assertTrue(bucket.allow()) # 1.5 left
            self.assertTrue(bucket.allow()) # 0.5 left
            self.assertFalse(bucket.allow()) # Not enough for 1.0

    def test_capacity_limit(self):
        with patch('time.monotonic') as mocked_time:
            mocked_time.return_value = 0.0
            bucket = TokenBucket.create(capacity=5, refill_rate=1.0)
            
            # Jump 100 seconds into the future
            mocked_time.return_value = 100.0
            
            # Tokens should be capped at 5, not 100+
            self.assertEqual(bucket.snapshot()['tokens'], 5.0)

    def test_retry_after(self):
        with patch('time.monotonic') as mocked_time:
            mocked_time.return_value = 0.0
            bucket = TokenBucket.create(capacity=5, refill_rate=1.0)
            
            # Consume all
            for _ in range(5):
                bucket.allow()
            
            # At t=0, tokens=0. To get 1 token at 1/sec, we need 1 second.
            self.assertAlmostEqual(bucket.retry_after_seconds(), 1.0)
            
            # Move to t=0.5
            mocked_time.return_value = 0.5
            # Now we have 0.5 tokens. Need 0.5 more.
            self.assertAlmostEqual(bucket.retry_after_seconds(), 0.5)

if __name__ == '__main__':
    unittest.main()
