# Observability, SLIs, SLOs, and Alerts (Fundamentals)

A system is not complete when it works in a diagram.
It is complete when operators can understand it, detect problems, and recover safely.

Observability is how you answer:
- what is happening?
- where is the bottleneck?
- why are users failing?
- is the system meeting its goals?

---

## 1) The three main pillars

### Metrics
Numeric time-series data.

Examples:
- RPS
- error rate
- p95/p99 latency
- CPU / memory
- queue depth
- cache hit ratio

Good for:
- dashboards
- alerts
- trends
- capacity planning

### Logs
Structured event records.

Examples:
- request received
- checkout failed
- user authentication denied
- consumer retried event

Good for:
- debugging specific incidents
- forensic analysis
- tracing exact failure paths

### Traces
Request-level journey across services.

Good for:
- microservices
- identifying slow hops
- following a request across many dependencies

Interview shorthand:
> metrics tell you that something is wrong, logs tell you what happened, traces tell you where it happened.

---

## 2) SLI, SLO, SLA

### SLI — Service Level Indicator
A measured signal.

Examples:
- successful request ratio
- p95 latency
- event processing delay

### SLO — Service Level Objective
A target for an SLI.

Examples:
- 99.9% successful requests per month
- p95 latency under 200 ms
- 95% of notifications delivered within 30 seconds

### SLA — Service Level Agreement
An external commitment, often contractual.

Important:
- SLOs are internal engineering targets
- SLAs are external promises
- good systems are designed and operated around SLOs

---

## 3) The golden signals

A very practical starting point:

- **Latency**
- **Traffic**
- **Errors**
- **Saturation**

### Latency
How long requests take, especially p95/p99.

### Traffic
RPS, QPS, bytes in/out, events/sec.

### Errors
5xx rate, timeout rate, failed jobs, failed DB queries.

### Saturation
How close the system is to resource limits:
- CPU
- memory
- DB connections
- queue backlog
- disk IOPS

---

## 4) RED and USE methods

### RED
For request-driven services:
- Rate
- Errors
- Duration

Great for:
- APIs
- microservices

### USE
For resources:
- Utilization
- Saturation
- Errors

Great for:
- hosts
- databases
- queues
- caches

In interviews, naming RED or USE is a nice plus.

---

## 5) What to monitor in common building blocks

### Load balancer
- request rate
- backend health
- 4xx / 5xx
- latency by backend
- dropped connections

### Database
- query latency
- replication lag
- slow queries
- connection pool usage
- CPU / memory / disk
- lock contention

### Cache
- hit ratio
- miss rate
- evictions
- memory pressure
- hot keys
- latency

### Queue / stream
- consumer lag
- queue depth
- retry rate
- DLQ growth
- end-to-end processing time

---

## 6) Good alerting vs bad alerting

### Good alerting
Alerts should be:
- actionable
- tied to user impact or important failure risk
- low-noise
- routed to the right team

### Bad alerting
Problems:
- too many alerts
- alerts on every small fluctuation
- alerts that do not explain severity
- alerts with no runbook or owner

Rule:
> alert on symptoms users feel and on imminent resource exhaustion, not on every internal event.

---

## 7) Error budgets

If an SLO is not 100%, there is an allowed amount of unreliability.

Example:
- SLO = 99.9% monthly availability
- error budget = 0.1% unavailability

Why it matters:
- balances reliability work vs feature velocity
- if error budget is exhausted, teams should reduce risky changes and focus on stability

This is a very mature concept to mention in interviews.

---

## 8) Correlation IDs and structured logs

In distributed systems:
- one user action may cross many services
- debugging without correlation is painful

Best practice:
- attach a request ID / trace ID
- propagate it across services
- log in structured format (JSON or equivalent)

This makes it much easier to join logs, traces, and incident timelines.

---

## 9) Dashboards and runbooks

A mature system should have:
- service overview dashboard
- dependency dashboard
- on-call alerts
- runbooks for common incidents

Example runbook sections:
- symptoms
- likely causes
- first checks
- rollback/failover steps
- escalation path

---

## 10) Interview checklist (quick)

When discussing observability, cover:
- key SLIs
- target SLOs
- latency percentiles
- error rate
- saturation metrics
- logs + trace IDs
- alerts and runbooks
- what “healthy” means for the system

---

## Mini template block (copy into case studies)

### Observability plan

- Main SLIs:
- Target SLOs:
- Key dashboards:
- Alert conditions:
- Correlation / tracing:
- Runbook notes: