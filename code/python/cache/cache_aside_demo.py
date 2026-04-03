from __future__ import annotations

from dataclasses import dataclass, field
import time


@dataclass
class FakeDatabase:
    data: dict[str, str]

    def get(self, key: str) -> str | None:
        print(f"[db] read key={key}")
        time.sleep(0.05)
        return self.data.get(key)


@dataclass
class CacheEntry:
    value: str
    expires_at: float


@dataclass
class InMemoryCache:
    store: dict[str, CacheEntry] = field(default_factory=dict)

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

    def set(self, key: str, value: str, ttl_seconds: float) -> None:
        self.store[key] = CacheEntry(
            value=value,
            expires_at=time.monotonic() + ttl_seconds,
        )
        print(f"[cache] set key={key} ttl={ttl_seconds}s")


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


def demo() -> None:
    db = FakeDatabase(
        data={
            "user:1": "Alice",
            "user:2": "Bob",
        }
    )
    cache = InMemoryCache()

    print(read_with_cache_aside(cache, db, "user:1"))
    print(read_with_cache_aside(cache, db, "user:1"))
    time.sleep(1.6)
    print(read_with_cache_aside(cache, db, "user:1"))


if __name__ == "__main__":
    demo()