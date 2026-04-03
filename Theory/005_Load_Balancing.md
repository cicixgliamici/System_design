# Load Balancing (Fundamentals): traffic distribution, health checks, stickiness, and HA

Load balancing is one of the first building blocks you introduce when a system must serve traffic through multiple instances.

It helps:
- distribute requests across instances
- improve availability
- enable horizontal scaling
- reduce overload on individual nodes

But it also introduces design questions:
- how do we choose the backend?
- what happens when a backend becomes slow but not fully down?
- do we need sticky sessions?
- can the load balancer itself become a single point of failure?

---

## 1) What a load balancer does

A load balancer sits between clients and backend servers and decides where to send each request.

Typical goals:
- spread traffic fairly
- route only to healthy instances
- terminate TLS if needed
- provide a stable endpoint even as backend instances change

Mental model:
> one public entry point, many backend instances behind it.

---

## 2) Why it matters in system design

Without load balancing:
- one server becomes a bottleneck
- scaling out is harder
- failures are more visible to users
- deployments and maintenance are riskier

With load balancing:
- you can add/remove instances more easily
- unhealthy instances can be removed from rotation
- the system becomes more elastic

---

## 3) L4 vs L7 load balancing

### L4 (Transport layer)
Routes traffic based on:
- IP
- port
- TCP/UDP metadata

**Pros**
- simpler
- very fast
- good for raw TCP/UDP services

**Cons**
- less application awareness
- cannot easily route by URL path, header, or host

### L7 (Application layer)
Routes traffic based on:
- HTTP path
- host
- headers
- cookies
- sometimes user identity / request metadata

**Pros**
- smarter routing
- can support canary releases, path-based routing, auth-aware logic
- better observability for HTTP services

**Cons**
- more overhead
- more complexity

Interview rule of thumb:
> for web APIs and microservices, L7 is usually the more interesting design choice.

---

## 4) Common balancing algorithms

### Round Robin
Send requests in order across backends.

**Pros**
- simple
- often good enough when instances are similar

**Cons**
- ignores current load
- can behave poorly if requests have very different cost

### Weighted Round Robin
Like round robin, but stronger instances get more traffic.

Good when:
- some nodes have more CPU/RAM
- clusters are heterogeneous

### Least Connections
Route to the backend with the fewest active connections.

**Pros**
- adapts better to uneven request durations

**Cons**
- “few connections” does not always mean “low load”

### Least Response Time / latency-aware
Prefer instances that are responding faster.

**Pros**
- helps avoid routing to degraded nodes

**Cons**
- more complex and more sensitive to noisy measurements

Interview default:
> start with round robin if instances are homogeneous; mention least-connections when request cost is uneven.

---

## 5) Health checks

A load balancer must know which backends are healthy.

### Types
- **TCP health check**: can I open a connection?
- **HTTP health check**: does `/health` or `/ready` return success?
- **Deep health check**: can the service reach critical dependencies?

### Readiness vs liveness
- **Liveness**: is the process alive?
- **Readiness**: is it ready to serve traffic?

Important distinction:
- a service may be alive but not ready
- sending production traffic too early causes errors and bad tail latency

---

## 6) Stateless services vs sticky sessions

### Stateless services
Each request can go to any backend because state is stored externally:
- DB
- cache
- object storage
- session store

**Pros**
- easiest to scale horizontally
- simplest with load balancing
- failure handling is cleaner

### Sticky sessions
A client is routed to the same backend repeatedly.

Useful when:
- session state is stored locally on the instance
- websocket affinity matters
- legacy applications depend on local session memory

**Cons**
- uneven load
- harder failover
- worse elasticity

Rule of thumb:
> prefer stateless services; use stickiness only when really necessary.

---

## 7) Connection draining and graceful shutdown

When removing an instance from service:
- stop sending new requests to it
- allow in-flight requests to finish
- then terminate it

This avoids:
- dropped user requests
- partial writes
- ugly deployment behavior

This matters during:
- rolling deploys
- autoscaling down
- maintenance operations

---

## 8) Failure modes and mitigations

### 1) Load balancer becomes a single point of failure
Mitigation:
- deploy multiple LBs
- use managed HA balancers or active-active setup
- use DNS / anycast / cloud-managed front doors

### 2) Slow backend still passes health check
Mitigation:
- use latency-aware routing
- outlier detection
- circuit breakers at service level
- richer readiness checks

### 3) One backend gets “sticky” hot traffic
Mitigation:
- reduce session affinity
- externalize state
- rebalance traffic periodically

### 4) Sudden traffic surge overwhelms all backends
Mitigation:
- autoscaling
- rate limiting
- queueing / async offload
- graceful degradation

---

## 9) Interaction with other building blocks

Load balancing rarely lives alone.

It works together with:
- **rate limiting** to protect the fleet from overload
- **caching** to reduce backend traffic
- **autoscaling** to add capacity
- **service discovery** to know current healthy backends
- **observability** to track p95/p99, error rate, and backend saturation

---

## 10) Interview checklist (quick)

When proposing a load balancer, mention:
- L4 or L7?
- routing algorithm
- health checks
- stateless vs sticky sessions
- HA setup (avoid SPOF)
- graceful deploy / draining
- what metrics drive scaling?

---

## Mini template block (copy into case studies)

### Load balancing plan

- LB type:
- Routing algorithm:
- Health checks:
- Sticky sessions:
- Autoscaling interaction:
- Failure handling:
- HA notes: