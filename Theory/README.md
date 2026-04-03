## Why it matters

A system can fail not only because of bugs, but because of success. A good architecture must anticipate growth in users, data, and operational complexity.

## Common techniques

- Load balancing
- Stateless services
- Caching
- Database replication
- Database sharding
- Asynchronous processing with queues
- CDN for static content

## Trade-offs

Improving scalability often increases:
- system complexity
- infrastructure cost
- debugging difficulty
- coordination overhead

## Real-world example

A simple web application may start with one server and one relational database. As traffic grows, the first steps are usually:

1. add a load balancer
2. scale application servers horizontally
3. add a cache
4. introduce read replicas
5. partition data if needed

## Interview angle

When asked about scalability, always clarify:
- expected traffic
- read/write ratio
- latency targets
- consistency needs
- failure assumptions