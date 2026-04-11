# Exercise 05 — Design a URL Shortener (Q&A + Suggested Solution)

## Scenario

Design a URL shortener similar to `short.ly/abc123`.

Users can:
- create short links for long URLs
- redirect from short URL to long URL
- optionally set expiration time
- view basic click analytics

## Requirements

- Redirect p95 < 80ms
- Peak read traffic: 200k RPS redirects
- Write traffic: 5k RPS new short links
- High availability for redirect path
- Avoid key collisions
- Basic abuse prevention (malicious/spam links)

---

## Questions

1. What clarifying questions do you ask first?
2. How do you generate short codes and avoid collisions?
3. What data model and storage would you choose?
4. How do you design the redirect path for very low latency?
5. How do you handle expiration and deletion?
6. What failure modes do you expect and how do you mitigate them?

---

## Suggested Answers

### A1) Clarifying questions

- Is custom alias supported (`/summer-sale`)?
- Is link edit allowed after creation?
- Do we need per-tenant quotas and auth?
- Is geo-based routing required?
- What analytics granularity is needed (real-time vs batch)?

Assumption: no custom alias initially; link is immutable; single region first.

### A2) Code generation

Approaches:

- **ID + Base62 encoding** (simple, deterministic)
- random code + collision check (works, but extra write checks)

Recommended: global ID generator (or DB sequence block allocation) then Base62 encode.

Benefits:
- predictable uniqueness
- no repeated collision retries under load

### A3) Data model

`short_link(code, long_url, created_at, expires_at, owner_id, status)`

`click_event(code, ts, ua, referrer, country)` (async pipeline)

Storage:
- primary KV/SQL table for `code -> URL metadata`
- analytics stream + warehouse for reporting

### A4) Redirect path

1. receive `GET /{code}`
2. check hot cache (Redis/CDN edge cache for popular codes)
3. on miss, read primary store
4. validate status/expiration
5. return HTTP 301/302 to long URL

Use negative caching for unknown codes to reduce repeated DB misses.

### A5) Expiration & deletion

- Store `expires_at` in metadata
- Validate during redirect (authoritative)
- Background job for cleanup/archival
- Soft delete for abuse/legal workflows

### A6) Failure modes + mitigations

1. Cache outage:
   - fallback to primary store
   - autoscale read replicas
2. Hot key storm:
   - edge caching + request coalescing
3. Abuse campaigns:
   - URL reputation checks + rate limits + blocklist
