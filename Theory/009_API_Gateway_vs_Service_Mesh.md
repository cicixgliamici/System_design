# API Gateway vs Service Mesh

## Why this topic matters

As systems grow from a single backend to many services, teams need two distinct control points:

- **north-south traffic** (client ↔ platform)
- **east-west traffic** (service ↔ service)

API Gateways and Service Meshes solve related but different problems.

---

## API Gateway (edge control plane)

An **API Gateway** sits at the platform edge and handles external API traffic.

Typical responsibilities:

- authentication and authorization (JWT, OAuth, API keys)
- rate limiting and quota enforcement
- request routing and versioning (`/v1`, `/v2`)
- request/response transformation
- WAF integration, TLS termination, CORS
- usage analytics and developer portal integration

Think: *"front door for external consumers"*.

---

## Service Mesh (internal traffic layer)

A **Service Mesh** manages internal service-to-service communication, often via sidecar or node proxies.

Typical responsibilities:

- mTLS between services
- service discovery and traffic routing
- retries, timeouts, circuit breaking
- canary/blue-green internal rollouts
- distributed tracing and golden signals
- policy enforcement between internal services

Think: *"traffic and reliability fabric for microservices"*.

---

## Quick comparison

| Dimension | API Gateway | Service Mesh |
|---|---|---|
| Primary scope | External (north-south) | Internal (east-west) |
| Main owner | API platform team | Platform/SRE team |
| Common features | Auth, quotas, API lifecycle | mTLS, retries, traffic shaping |
| Client awareness | Public/partner/mobile clients | Internal services only |
| Deployment point | Edge ingress | Across service network |

---

## How they work together

A common architecture is:

1. client traffic enters via API Gateway
2. Gateway authenticates + applies edge policies
3. request reaches internal services
4. service-to-service calls are governed by mesh policies

This avoids overloading the gateway with all internal reliability concerns.

---

## Trade-offs

Benefits:

- strong separation of concerns
- better security posture (edge auth + internal mTLS)
- clearer ownership for API and platform teams

Costs:

- higher operational complexity
- more observability surfaces to monitor
- policy sprawl risk if governance is weak

---

## Interview angle

When asked "do we need gateway or mesh?", a strong answer is:

- gateway first for external APIs
- mesh when internal service communication and reliability policies become hard to manage manually
- avoid introducing both too early in a small system
