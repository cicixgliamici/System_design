# Round Robin in Go

## Explanation

### How this round-robin example works

This example shows a simple implementation of **round-robin load balancing**, a strategy used to distribute requests evenly across a set of backend servers.

### The problem it solves

Suppose we have multiple backend instances such as:

* `api-1`
* `api-2`
* `api-3`

and we want incoming requests to be distributed across them.

A basic goal of a load balancer is to avoid sending every request to the same backend, which would overload one server while leaving the others underused.

### The core idea of round robin

Round robin is one of the simplest load-balancing strategies.

The idea is:

1. send the first request to the first backend
2. send the second request to the second backend
3. send the third request to the third backend
4. when the list ends, start again from the beginning

So with three backends, the sequence becomes:

```text
api-1 -> api-2 -> api-3 -> api-1 -> api-2 -> api-3 -> ...
```

This makes the distribution predictable and easy to understand.

### What the `RoundRobin` struct stores

The `RoundRobin` struct contains:

* `mu`: a mutex used to protect shared state
* `backends`: the list of available backend servers
* `index`: the position of the next backend to use

The `index` is the key piece of state, because it tells the load balancer which backend should receive the next request.

### Why the mutex is needed

In a real system, many requests may arrive at the same time from different goroutines.

Without synchronization, two goroutines could read and update `index` at the same time, causing incorrect behavior or race conditions.

The mutex ensures that:

* only one goroutine at a time can access and modify the index
* backend selection remains correct and thread-safe

That is why `Next()` locks the mutex before reading and updating the internal state.

### What `NewRoundRobin` does

The constructor:

1. checks that the backend list is not empty
2. initializes the struct
3. starts the index at `0`

If the backend list were empty, the algorithm would have nowhere to send requests, so the code correctly panics.

### What `Next()` does

The `Next()` method returns the backend that should handle the next request.

Its logic is:

1. lock the mutex
2. read the backend at the current index
3. increment the index
4. wrap around using modulo when the end of the list is reached
5. return the selected backend

The wrap-around step is:

```text
(rr.index + 1) % len(rr.backends)
```

This is what makes the algorithm cycle forever through the backend list.

### What the output shows

In `main()`, the load balancer is initialized with three backends:

* `api-1`
* `api-2`
* `api-3`

Then `Next()` is called 10 times.

So the expected pattern is:

```text
request=00 -> backend=api-1
request=01 -> backend=api-2
request=02 -> backend=api-3
request=03 -> backend=api-1
...
```

This demonstrates that requests are distributed evenly in a repeating order.

### Why round robin is useful

Round robin is useful because it is:

* simple
* fast
* easy to implement
* good when all backends have similar capacity

It works well when the servers are roughly identical and requests have similar cost.

### Limitations of basic round robin

This basic implementation does not consider:

* backend health
* different backend capacities
* request latency
* long-running versus short-running requests

So while round robin is a good starting point, real production load balancers often extend it with features such as:

* **weighted round robin**
* **health checks**
* **least connections**
* **latency-aware routing**

### In one sentence

This code cycles through a list of backend servers in order, using a mutex to keep the selection thread-safe, so that requests are distributed evenly across the available backends.
