# BS Detector: Production Readiness & System Architecture Plan

## 1. Prototype Justification:
The core philosophy behind the prototype was prioritizing strict data contracts and zero-hallucination over broad, speculative AI capabilities. In legal tech, especially tools designed for the judiciary, a false positive or an unhandled JSON parsing error is catastrophic. 

Key architectural choices made in the prototype:
* **Structured Outputs over Regex:** The prototype eschews brittle regex parsing in favor of strict Pydantic `BaseModels` paired with OpenAI's Structured Outputs. This guarantees type-safe data handoffs between autonomous agents, preventing pipeline crashes caused by LLM structural hallucinations.
* **Sequential Agent Decomposition:** The system routes tasks through specialized agents (Intake -> Quote Extraction -> Citation Checking -> Cross-Document Consistency). This isolates failures and allows for granular confidence scoring.
* **Context Stuffing (for now):** For this limited MVP, full document texts are passed into the context window. This ensures 100% retrieval accuracy for the current scale, avoiding the false negatives inherent in vector search over small datasets.
* **Automated Evals as a First-Class Citizen:** The `run_evals.py` harness is built to measure precision, recall, and hallucination rates explicitly using fuzzy matching. This helps to ensure that any future prompt tuning can be measured against a baseline ground truth.

## 2. Production Assumptions & Constraints
Moving from a local prototype to a production MVP requires shifting from synchronous, local execution to a distributed, secure, and asynchronous architecture.

* **Workload:** A single legal matter may contain hundreds of documents (motions, exhibits, thousands of pages). Analysis will take minutes to hours, requiring asynchronous, long-running background jobs.
* **Security & Compliance:** Customers (courts and litigation teams) require strict SOC2-compliant handling of privileged information, data encryption, and verifiable audit trails.
* **Concurrency:** The system must support hundreds of simultaneous jobs at launch without hitting API rate limits or dropping tasks.
* **Tech Stack:** The MVP will leverage cloud-managed components to minimize operational overhead, utilizing Python for the AI worker nodes and TypeScript/Node for the API gateway and client interfaces.

## 3. High-Level System Architecture
To decouple user-facing request handling from long-running AI orchestration, the production system will adopt an asynchronous, event-driven architecture.

1. **API Gateway & Ingestion Layer:** Handles authentication, rate limiting, and initial file validation.
2. **Durable Document Store:** Encrypted object storage for raw legal documents.
3. **Relational Metadata & Audit DB:** A PostgreSQL database to store tenant identities, job states, intermediate agent structured outputs, and audit logs.
4. **Task Queue & Orchestrator:** A robust job queue (e.g., Temporal, Celery, or AWS SQS) to manage distributed workers, handle retries, and track state.
5. **AI Worker Nodes:** Scalable Python containers executing the agent pipelines and managing LLM API calls.
6. **Observability:** Metrics and tracing (e.g., Datadog, LangSmith) to monitor AI quality (latency, token usage, hallucination rates) and system health.

## 4. Lifecycle of a Legal Analysis Job
1. **Ingestion:** User uploads documents. The API validates the payload, verifies tenant authorization, and stores the files in the encrypted Document Store.
2. **Dispatch:** The API creates a "Pending" job record in the database and dispatches an event to the Task Queue.
3. **Execution:** An available AI Worker picks up the job. The orchestration logic runs the pipeline sequentially or in parallel where applicable (e.g., extracting quotes and checking cross-document consistency simultaneously).
4. **State Management:** Every time an agent completes a task, the intermediate JSON artifact is persisted to the database. This allows the job to be resumed from the exact point of failure if a worker crashes.
5. **Completion:** The `SummaryAgent` synthesizes the final report. The job is marked as "Completed," and a webhook or WebSocket event notifies the frontend.

## 5. Scaling the AI: The Path to Agentic RAG
The prototype’s "Context Stuffing" approach will fail when faced with a 15,000-page case file (requires massive context). For production, the ingestion pipeline could evolve into an Agentic RAG architecture:
* **Legal-Semantic Chunking:** Documents will not be chunked by arbitrary character limits, but by structural legal boundaries (e.g., articles, paragraphs, exhibits).
* **Routing Agents:** Instead of passing all documents to the verification agents, a "Domain Plan Agent" will parse the claim and query the vector database iteratively to retrieve only the relevant evidence (e.g., querying only the medical records to verify a fracture claim).
* **Self-Correction:** If the initial retrieval yields no results, the agent will have fallback tools to rewrite the search query before resorting to a `could_not_verify` status.

## 6. Resilience and Failure Handling
AI APIs are inherently volatile. The architecture must anticipate and absorb failures gracefully:
* **Exponential Backoff:** Transient errors (e.g., HTTP 429 Rate Limits, 502 Bad Gateways) from the LLM provider will trigger automatic retries at the worker level.
* **Idempotency:** All agent operations must be idempotent. If a worker dies mid-task and another picks it up, it should overwrite the previous state without duplicating findings.
* **Degraded Gracefully:** If a specific agent fails permanently (e.g., context window exceeded), the pipeline should flag that specific subsystem as failed in the final report, rather than crashing the entire job.

## 7. Tenant Isolation and Security
Legal documents are highly privileged. The MVP must protect them through:
* **Strict Tenant Scoping:**
* **Encryption:** 
* **Ephemeral Context:**

## 8. Rollout Strategy (What to Build First)
To avoid premature optimization, the deployment sequence should be:
1. **Core Reliability:** Stand up the async worker queue and database to safely run the current prototype asynchronously.
2. **Security Foundation:** Implement tenant-aware routing and encrypted storage.
3. **Observability:** Deploy pipelines incorporating the `run_evals.py` suite as a mandatory gating check to prevent regressions in AI precision and recall.
4. **Scale:** Implement Agentic RAG and vector storage only when customer payload sizes consistently breach the 128k/200k token context windows.
