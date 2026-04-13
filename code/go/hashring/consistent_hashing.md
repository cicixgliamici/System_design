## How this consistent hashing example works

This example shows a simple implementation of **consistent hashing**, a technique often used in distributed systems to assign keys to servers, caches, or storage nodes.

### The problem it solves

Suppose we want to map keys such as:

* `user:1`
* `user:2`
* `cart:91`

to backend nodes like:

* `cache-a`
* `cache-b`
* `cache-c`

A naive strategy could be:

```text
hash(key) % number_of_nodes
```

The problem is that when a node is added or removed, **almost all keys get remapped**.
That is expensive in systems such as distributed caches, because a topology change causes large-scale movement of data.

### The core idea of consistent hashing

Instead of directly using modulo, we place both:

* **nodes**
* **keys**

on the same hash space, which we imagine as a **ring**.

Then, for a given key:

1. we compute its hash
2. we move clockwise on the ring
3. we assign the key to the **first node encountered**

If we reach the end of the ring, we wrap around to the beginning.

This means that when a new node is added, only the keys in a limited region of the ring are reassigned.

### Why virtual replicas are used

If each physical node appeared only once on the ring, distribution could be uneven.

To improve balance, each real node is inserted multiple times as **virtual replicas**, for example:

* `cache-a#0`
* `cache-a#1`
* `cache-a#2`

Each replica gets its own hash and occupies a different position on the ring.

This makes the distribution of keys more uniform.

In this code:

```go
ring := NewConsistentHashRing(50)
```

each physical node gets **50 virtual replicas**.

### What `AddNode` does

When a node is added:

1. the code checks that it is not already present
2. it creates `virtualReplicas` copies of that node
3. each replica is hashed independently
4. all replicas are inserted into `entries`
5. the ring is sorted by hash

So `entries` is the actual representation of the ring.

### What `GetNode` does

When a key arrives:

1. the key is hashed
2. the code performs a **binary search** on the sorted ring
3. it finds the first entry whose hash is greater than or equal to the key hash
4. that entry’s node is returned
5. if no such entry exists, the search wraps to index `0`

This is efficient because the lookup is:

```text
O(log N)
```

after sorting.

### Why remapping is limited

The most important property of consistent hashing is this:

* when a new node is added, **only some keys move**
* most keys remain on the same node

That is why in the example, after adding `cache-d`, you should expect **limited remapping**, not a full redistribution.

This is exactly why consistent hashing is used in systems like:

* distributed caches
* load balancers
* sharded databases
* distributed key-value stores

### In one sentence

This code builds a sorted hash ring of virtual nodes and assigns each key to the first node clockwise on the ring, reducing remapping when nodes are added.
