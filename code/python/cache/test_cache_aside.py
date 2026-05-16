"""
Tests for the cache-aside pattern implementation.

Strategy:
- InMemoryCache uses time.monotonic() internally.
- We patch time.monotonic to control the clock deterministically,
  avoiding any real sleep in the test suite.
- FakeDatabase is injected directly (no patching needed).
"""

import unittest
from unittest.mock import patch
from .cache_aside_demo import InMemoryCache, FakeDatabase, read_with_cache_aside


class TestInMemoryCache(unittest.TestCase):
    def test_miss_returns_none(self):
        cache = InMemoryCache()
        result = cache.get("missing-key")
        self.assertIsNone(result)

    def test_set_and_hit(self):
        cache = InMemoryCache()
        with patch("time.monotonic", return_value=0.0):
            cache.set("user:1", "alice", ttl_seconds=10.0)

        with patch("time.monotonic", return_value=5.0):  # still within TTL
            result = cache.get("user:1")

        self.assertEqual(result, "alice")

    def test_expired_entry_returns_none(self):
        cache = InMemoryCache()
        with patch("time.monotonic", return_value=0.0):
            cache.set("user:1", "alice", ttl_seconds=1.0)

        # Jump past the TTL
        with patch("time.monotonic", return_value=2.0):
            result = cache.get("user:1")

        self.assertIsNone(result)

    def test_expired_entry_is_evicted(self):
        """After an expired get, the key must be removed from the store."""
        cache = InMemoryCache()
        with patch("time.monotonic", return_value=0.0):
            cache.set("user:1", "alice", ttl_seconds=1.0)

        with patch("time.monotonic", return_value=2.0):
            cache.get("user:1")

        self.assertNotIn("user:1", cache.store)

    def test_set_overwrites_existing_entry(self):
        cache = InMemoryCache()
        with patch("time.monotonic", return_value=0.0):
            cache.set("user:1", "alice", ttl_seconds=10.0)
            cache.set("user:1", "bob", ttl_seconds=10.0)

        with patch("time.monotonic", return_value=1.0):
            result = cache.get("user:1")

        self.assertEqual(result, "bob")


class TestCacheAside(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase(data={"user:1": "alice", "user:2": "bob"})
        self.cache = InMemoryCache()

    def test_miss_fetches_from_db_and_populates_cache(self):
        with patch("time.monotonic", return_value=0.0):
            result = read_with_cache_aside(self.cache, self.db, "user:1", ttl_seconds=10.0)

        self.assertEqual(result, "alice")
        self.assertIn("user:1", self.cache.store)

    def test_second_read_is_a_cache_hit(self):
        with patch("time.monotonic", return_value=0.0):
            read_with_cache_aside(self.cache, self.db, "user:1", ttl_seconds=10.0)

        # Second read must not require clock to advance (still within TTL)
        with patch("time.monotonic", return_value=5.0):
            result = read_with_cache_aside(self.cache, self.db, "user:1", ttl_seconds=10.0)

        self.assertEqual(result, "alice")

    def test_missing_key_returns_none_and_does_not_populate_cache(self):
        with patch("time.monotonic", return_value=0.0):
            result = read_with_cache_aside(self.cache, self.db, "user:999", ttl_seconds=10.0)

        self.assertIsNone(result)
        self.assertNotIn("user:999", self.cache.store)

    def test_after_expiry_re_fetches_from_db(self):
        """When the cached entry expires, the next read must go back to the DB."""
        with patch("time.monotonic", return_value=0.0):
            read_with_cache_aside(self.cache, self.db, "user:1", ttl_seconds=1.0)

        # Simulate DB update
        self.db.data["user:1"] = "alice-updated"

        with patch("time.monotonic", return_value=2.0):  # past TTL
            result = read_with_cache_aside(self.cache, self.db, "user:1", ttl_seconds=1.0)

        self.assertEqual(result, "alice-updated")


if __name__ == "__main__":
    unittest.main()
