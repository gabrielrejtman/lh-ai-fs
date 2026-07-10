# BS Detector Production Readiness and Architecture

## Assumptions

The following assumptions shape the proposed architecture:

- Primary users are legal reviewers and litigation teams who upload confidential case documents and expect reliable verification reports.
- A single matter may contain dozens of documents, and an analysis may require minutes of processing due to multiple model calls, evidence retrieval, and cross-document checks.
- Customers require auditability, status tracking, and safe handling of privileged information.
- The first production target is a single-tenant or lightly multi-tenant MVP with clear tenant separation, not a massive enterprise platform.
- The system should be able to support hundreds of simultaneous users at launch and be architected to scale to thousands over time.
- The initial MVP can be built on cloud-managed components with a strong preference for low operational burden.

If these assumptions change, the architecture would shift toward stronger isolation, higher concurrency, and more failover redundancy.

## High-level system components

The proposed production architecture has these major components:

1. Ingestion/API layer
2. Workflow orchestrator and job queue
3. Agent pipeline service
4. Document/evidence store
5. Metadata and audit database
6. Monitoring and quality observability
7. Tenant and security controls

These boundaries are intentional because they separate user-facing request handling from long-running AI work and from durable audit storage.

## How analysis moves through the system

1. User uploads documents through the frontend or API.
2. The ingestion service validates file types, metadata, and tenant identity.
3. Documents are stored encrypted in a document store.
4. A job record is created in a durable metadata store, and a job is dispatched to a queue.
5. A worker picks up the job and executes the agent pipeline:
   - document normalization
   - quote extraction and fidelity check
   - citation extraction
   - citation validation
   - cross-document consistency review
   - summary generation
6. Each stage writes intermediate structured artifacts to the metadata store and appends audit entries.
7. When the job completes, the final structured report is stored and the job status is updated.
8. The frontend polls or receives a webhook notification and presents the verified report.

This flow keeps the external API responsive and makes the analysis resumable and auditable.

## What data is stored durably

The system should store the following data:

- Raw uploaded documents (encrypted at rest)
- Normalized document metadata (name, type, length, tenant, upload time)
- Intermediate agent outputs and structured findings
- Final report JSON, including citation status, quote fidelity flags, and cross-document findings
- Prompt versions and model metadata used for each analysis
- Job lifecycle events, timestamps, and error/retry records
- Tenant and access control metadata

Data that can be recomputed and should not be stored for long-term retention in the MVP includes:

- temporary model context and ephemeral request payloads,
- token-level model request/response bodies, unless needed for audit or debugging,
- transient in-memory caches used during a single job.

## Where the system is likely to fail first

The highest-risk areas are:

- model/API failures and rate limits
- long-running job timeouts or worker crashes
- corrupted or malformed document uploads
- noisy or incomplete model outputs leading to hallucinated findings
- misconfigured tenant isolation or leaked audit data

Recovery strategy:

- add retries with exponential backoff for retriable model failures,
- classify failures as transient or permanent and preserve error metadata,
- implement idempotent job processing so retries do not produce duplicate reports,
- validate document schema before analysis begins,
- surface a human-interpretable failure state and log the root cause.

## Production-grade orchestration and failure handling

The current prototype now includes a lightweight orchestrator in `backend/agents/orchestrator.py`. In production, the orchestration layer should be strengthened by:

- using a durable job queue (e.g. Redis streams, SQS, or managed task queue)
- storing job state and retries in a database
- retrying only retriable failures such as transient model errors or temporary service outages
- failing fast on invalid input and preserving structured error state for debugging
- capturing step-level success/failure metadata so the system can report where the pipeline broke
- supporting manual intervention or human-in-the-loop review for high-risk findings

This is the first major production hardening step, because a legal verification pipeline must not silently lose work or return misleading results.

## Tenant isolation and document security

Legal documents are sensitive. The MVP must protect them through:

- tenant-scoped storage and access control at every layer
- encryption in transit and at rest for document storage and metadata stores
- least-privilege service roles and secrets management for model/API keys
- audit logging of upload, access, analysis, and result retrieval events
- per-tenant job records and strict authorization checks on report access

For the prototype, simple tenant separation can be implemented using tenant IDs in the database and storage prefixes. For a later stage, this should evolve into stronger isolation boundaries such as separate storage buckets or dedicated database schemas.

## Observability and correctness metrics

The system should measure both health and quality.

Health metrics:

- job queue length and worker throughput
- analysis latency and stage timing
- model API error rates and retry counts
- host/service CPU, memory, and request error rate
- audit logs for job failures

Quality metrics:

- precision and recall for known flaw types
- hallucination rate for unsupported findings
- quote fidelity coverage and accuracy
- confidence calibration across jobs
- regression tests on annotated sample documents

The current eval harness (`python run_evals.py`) is the first step toward quality measurement. In production, that harness should be extended into an automated regression suite and baked into CI.

## What to build first

The most valuable first production increment is:

1. Durable ingestion + document store
2. Job queue + worker orchestration
3. Structured report persistence and audit logging
4. Simple tenant-aware API and UI status polling
5. Retry/failure handling for common model errors
6. Eval metrics and CI regression tests

This sequence prioritizes reliability and auditability over premature scaling. It preserves the current prototype’s modular agent design while making the workflow safe enough for early customers.

## Tradeoffs and what is deferred

Deliberate deferrals for the MVP:

- separate multi-tenant cluster isolation. Start with tenant metadata and move to stronger separation later.
- full RAG with vector store retrieval. Keep the current document-centric pipeline and add retrieval once corpus size demands it.
- rewriting agents into a distributed microservices mesh. Start with a single worker pool and split services only when scaling dictates it.
- customer-facing explainability beyond structured findings. The MVP should focus on accurate, auditable outputs first.

## Bottom line

BS Detector should evolve from the current prototype by hardening workflow orchestration, preserving structured intermediate outputs, and protecting sensitive legal documents.

The first production-ready MVP is a job-driven pipeline with durable document and audit storage, tenant-aware APIs, explicit failure handling, and objective quality metrics. That keeps the current architecture intact while making it safe enough for legal teams to rely on.

### Evaluation

Run the evaluation suite from the repository root:

```bash
python run_evals.py
```

The eval harness reports precision, recall, and hallucination rate for citations, quotes, and cross-document findings. The current prototype is intentionally conservative about quote extraction and may report lower quote precision than a cherry-picked demo, but it surfaces the tradeoff clearly rather than hiding it.

