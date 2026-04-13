# Cache-Aside in Python

## Explanation

### How this cache-aside example works

This example shows a simple implementation of the **cache-aside pattern**, one of the most common caching strategies in backend systems.

The goal is to reduce repeated reads from a slower database by storing recently accessed values in a faster in-memory cache.

### The problem it solves

Databases are usually slower and more expensive to query than memory.

If the application repeatedly asks for the same key, such as:

* `user:1`
* `user:2`

it is wasteful to hit the database every time.

A cache helps by keeping recently read values in memory, so later requests can be served faster.

### The core idea of cache-aside

In the cache-aside pattern, the application follows this logic:

1. look for the value in the cache
2. if the value is found, return it
3. if the value is not found, read it from the database
4. store the database result in the cache
5. return the value

The cache is therefore filled **on demand**, only when needed.

### What `FakeDatabase` represents

`FakeDatabase` simulates a persistent storage system.

Its `get()` method:

* prints a debug message
* waits for a short time using `time.sleep(0.05)`
* returns the value associated with the key

The artificial delay is useful because it makes the difference between cache hits and database reads visible in the demo.

### What `CacheEntry` stores

Each cached item is represented by `CacheEntry`, which contains:

* `value`: the cached data
* `expires_at`: the expiration timestamp

This means the cache does not store values forever. Each item is valid only up to its TTL.

### What `InMemoryCache` does

`InMemoryCache` is a small in-memory key-value cache.

Its internal dictionary maps a key to a `CacheEntry`.

It supports two main operations:

* `get(key)` to retrieve a cached value
* `set(key, value, ttl_seconds)` to store a value with an expiration time

### What can happen in `cache.get()`

When `get()` is called, there are three possible cases:

1. **cache miss**: the key is not present
2. **cache expired**: the key exists, but its TTL has passed
3. **cache hit**: the key exists and is still valid

If an entry has expired, the code removes it from the cache and returns `None`.

### Why `time.monotonic()` is used

The code uses `time.monotonic()` instead of wall-clock time.

This is useful for TTL logic because monotonic time only moves forward and is not affected by system clock adjustments.

That makes expiration checks more reliable.

### What `set()` does

The `set()` method stores a value in the cache and computes its expiration time as:

```text
current_monotonic_time + ttl_seconds
```

So the entry remains valid only for the configured TTL window.

### What `read_with_cache_aside()` does

This function is the heart of the example.

Its logic is:

1. try the cache first
2. if the value is found, return it immediately
3. otherwise query the database
4. if the database returns a value, store it in cache
5. return the value

This is exactly the cache-aside pattern.

The application, not the cache itself, is responsible for deciding when to go to the database and when to populate the cache.

### What the demo shows

The demo performs three reads for `user:1`:

1. **first read**: cache miss, then database read, then cache set
2. **second read**: cache hit, so the database is not accessed
3. **third read after sleeping 1.6 seconds**: the cached entry has expired, so the database is read again and the cache is refreshed

This makes the TTL behavior very clear.

### Why TTL is important

TTL, or time-to-live, prevents cached data from staying in memory forever.

Without expiration, the application could return stale values long after the database has changed.

TTL is a simple way to balance:

* performance
* freshness of data

### Why cache-aside is useful

Cache-aside is popular because it is:

* simple
* flexible
* easy to control from application code
* effective for read-heavy workloads

It works especially well when the same data is requested repeatedly.

### Limitations of this basic example

This demo is intentionally small, so it does not handle production concerns such as:

* cache eviction policies like LRU or LFU
* maximum memory size
* concurrent access protection
* cache stampede prevention
* write-through or write-behind strategies
* distributed caches like Redis or Memcached

### In one sentence

This code demonstrates cache-aside by first checking an in-memory cache, falling back to the database on a miss or expiration, and then storing the result back in cache for future reads.
