# Exercise 08 — Design a Multi-Tenant File Upload Service (Q&A + Suggested Solution)

## Scenario

Design a service where users upload files (images/docs) and later download/share them.

## Requirements

- peak upload: 25k req/s
- max file size: 500 MB
- antivirus scan before file becomes public
- signed URL access
- tenant quota + billing metrics
- durable storage and high availability

---

## Questions

1. Which clarifying questions do you ask first?
2. How do you design upload and download flows?
3. Where do you run scanning and metadata enrichment?
4. How do you enforce tenant quotas and abuse controls?
5. Which storage and metadata model do you choose?
6. What are key failure modes and mitigations?

---

## Suggested Answers

### A1) Clarifying questions

- Are files immutable after upload?
- Need resumable/chunked upload?
- Is cross-region replication required at launch?
- Any legal retention/deletion constraints?

Assumption: immutable objects, resumable upload required, single region at first.

### A2) Upload/download flow

Upload:
1. client requests upload session
2. service validates auth/quota
3. service returns pre-signed multipart upload URLs
4. client uploads directly to object storage
5. completion event triggers processing pipeline

Download:
1. client requests file access
2. authZ check on metadata service
3. service issues short-lived signed download URL

### A3) Async processing

- object-created event -> scanning queue
- scanner workers run AV + MIME validation
- metadata status changes from `pending` to `available` only after successful checks

### A4) Quotas/abuse

- per-tenant total bytes and object count quotas
- per-user upload rate limits
- block dangerous file types and suspicious patterns

### A5) Data model

`file_metadata(file_id, tenant_id, owner_id, storage_key, size, checksum, status, created_at)`

`tenant_usage(tenant_id, used_bytes, object_count, updated_at)`

### A6) Failure modes

1. scanner backlog growth:
   - autoscale workers + priority queues
2. object store temporary errors:
   - retries with jitter + idempotent completion
3. quota race conditions:
   - atomic quota reservation before upload finalization
