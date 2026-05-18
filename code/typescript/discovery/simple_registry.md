# In-Memory Service Registry

This module implements a basic Service Registry (Discovery) pattern, which is crucial for dynamic, distributed architectures like microservices.

## How it works

In a cloud environment, instances of services start up, shut down, or crash dynamically. Their IP addresses are not static. A Service Registry acts as a centralized "phone book" for the system:
1.  **Registration:** When a service instance starts, it registers its address and metadata with the registry.
2.  **Heartbeats:** The instance periodically sends a "heartbeat" to let the registry know it is still alive.
3.  **Discovery:** Other services query the registry to find the current, healthy instances of a target service.
4.  **Eviction:** If the registry misses multiple heartbeats from an instance, it evicts (deregisters) it, assuming the instance has crashed or become partitioned.

## Trade-offs

**Pros:**
*   **Dynamic Scaling:** Automatically handles instances joining and leaving the cluster.
*   **Resilience:** Prevents routing traffic to dead nodes.

**Cons:**
*   **Complexity:** Introduces a new moving part that must itself be highly available.
*   **Eventual Consistency:** There is often a slight delay between an instance crashing and the registry evicting it. During this window, clients might still attempt to route to the dead instance (which is why clients must still implement retries and circuit breakers).

## Implementation Details

*   This is a simplified, in-memory TypeScript implementation. In production, tools like Consul, ZooKeeper, or etcd are used to ensure the registry itself is highly available and strictly consistent (or eventually consistent like Eureka).
*   The eviction loop runs periodically, checking the last seen timestamp of every registered instance against a configured TTL (Time To Live).

## See Also
*   [Theory: Service Discovery & API Gateways](../../../Theory/009_API_Gateway_vs_Service_Mesh.md)
