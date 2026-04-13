from __future__ import annotations

from dataclasses import dataclass, field
import time


# FakeDatabase simulates a slow persistent data source.
#
# In a real system this could be PostgreSQL, MySQL, DynamoDB, etc.
# Here we keep data in memory and add a small sleep to imitate the cost
# of reading from a database.
@dataclass
class FakeDatabase:
    data: dict[str, str]

    def get(self, key: str) -> str | None:
        print(f"[db] read key={key}")
        time.sleep(0.05)
        return self.data.get(key)


# CacheEntry represents one cached item.
#
# It stores:
# - the cached value
# - the expiration timestamp
#
# Once the current time passes expires_at, the entry is considered stale.
@dataclass
class CacheEntry:
    value: str
    expires_at: float


# InMemoryCache is a very small in-memory cache with TTL support.
#
# The store dictionary maps each key to a CacheEntry.
@dataclass
class InMemoryCache:
    store: dict[str, CacheEntry] = field(default_factory=dict)

    # get tries to read a value from the cache.
    #
    # Possible outcomes:
    # - miss: the key is not in the cache
    # - expired: the key exists but its TTL has passed
    # - hit: the value is still valid and can be returned immediately
    def get(self, key: str) -> str | None:
        entry = self.store.get(key)
        now = time.monotonic()

        if entry is None:
            print(f"[cache] miss key={key}")
            return None

        if now >= entry.expires_at:
            print(f"[cache] expired key={key}")
            del self.store[key]
            return None

        print(f"[cache] hit key={key}")
        return entry.value

    # set inserts or refreshes a cache entry with a TTL.
    #
    # The expiration moment is computed as:
    # current_time + ttl_seconds
    def set(self, key: str, value: str, ttl_seconds: float) -> None:
        self.store[key] = CacheEntry(
            value=value,
            expires_at=time.monotonic() + ttl_seconds,
        )
        print(f"[cache] set key={key} ttl={ttl_seconds}s")


# read_with_cache_aside implements the cache-aside pattern.
#
# Flow:
# 1. try reading from cache
# 2. if the value is present, return it immediately
# 3. otherwise read from the database
# 4. if found in the database, store it in cache
# 5. return the value
#
# This is called "cache-aside" because the application explicitly decides
# when to read from the cache and when to populate it.
def read_with_cache_aside(
    cache: InMemoryCache,
    db: FakeDatabase,
    key: str,
    ttl_seconds: float = 1.5,
) -> str | None:
    cached = cache.get(key)
    if cached is not None:
        return cached

    value = db.get(key)
    if value is not None:
        cache.set(key, value, ttl_seconds)

    return value


# demo shows the behavior of the cache-aside flow.
#
# Expected sequence:
# - first read: cache miss -> database read -> cache fill
# - second read: cache hit
    demo()
