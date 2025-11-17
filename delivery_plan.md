# GovStack Delivery Plan

This plan breaks the requirements into executable tasks and sub-tasks, ordered by dependencies so progress can be tracked incrementally.

## Requirement References
- **R1** – Multi-format Document Ingestion
- **R2** – Automatic Bot Refresh After Indexing
- **R3** – Scalable Ingestion & Collection Management
- **R4** – User-visible Ingestion Progress
- **R5** – Responsive Chat & Platform Performance

## Phase 0 – Alignment & Architecture (Foundational)

### T0 – Delivery Kick-off & Architecture Alignment
- **Depends on:** —
- **Linked requirements:** R1–R5
- **Purpose:** Confirm scope, architecture choices (task queue, streaming uploads, cache strategy), success metrics, and sequencing with stakeholders.
- **Sub-tasks:**
  - **T0.1** Confirm ownership, delivery cadence, and success metrics per requirement.
  - **T0.2** Produce a lightweight architecture decision record covering background job framework, ingestion data flow, and cache refresh strategy.
  - **T0.3** Update observability plan (metrics, dashboards) to align with performance and visibility requirements.

## Phase 1 – Background Job Tracking Baseline

### T1 – In-memory Indexing Job Registry
- **Status:** ✅ Done
- **Depends on:** T0
- **Linked requirements:** R2, R3, R4
- **Purpose:** Stand up lightweight job tracking without introducing new infrastructure.
- **Sub-tasks:**
  - **T1.1** Add in-memory job data structure with lifecycle timestamps.
  - **T1.2** Emit progress updates from indexing batches and cache refresh hook.
  - **T1.3** Ensure background scheduling reuses the running event loop when available.

### T2 – API Integration for Indexing Job Visibility
- **Status:** 🛠️ In Progress
- **Depends on:** T1
- **Linked requirements:** R1, R2, R4
- **Purpose:** Surface job identifiers and status endpoints so clients can poll progress.
- **Sub-tasks:**
  - **T2.1** ✅ Attach `index_job_id` to upload/update responses.
  - **T2.2** ✅ Provide `/documents/indexing-jobs` and `/documents/indexing-jobs/{job_id}` endpoints.
  - **T2.3** ⏳ Add unit/API tests for new responses (pending once auth fixtures ready).

## Phase 2 – Ingestion Pipeline Improvements

### T3 – Streaming Upload & Validation Layer
- **Status:** ✅ Done
- **Depends on:** T2
- **Linked requirements:** R1, R3, R4
- **Purpose:** Support large files without memory pressure and fail fast on unsupported types.
- **Sub-tasks:**
  - **T3.1** ✅ Swap `upload_document` buffering for streaming uploads to MinIO.
  - **T3.2** ✅ Add server-side validation for supported extensions with descriptive 4xx responses.
  - **T3.3** ✅ Emit ingestion job record tied to upload for downstream progress reporting (feeds R4).

### T4 – Multi-format Parsing & Indexing Enhancements
- **Status:** 🛠️ In Progress
- **Depends on:** T3
- **Linked requirements:** R1, R2
- **Purpose:** Convert additional office formats and guarantee they reach the embedding pipeline.
- **Sub-tasks:**
  - **T4.1** ✅ Integrate converters/parsers for `.doc`, `.docx`, `.xls`, `.xlsx`, `.csv`, `.txt`, `.md`, `.pdf`.
  - **T4.2** ✅ Extend ingestion pipeline configuration and metadata enrichment to handle new formats.
  - **T4.3** ⏳ Add regression tests verifying each format is indexed and visible via chat/doc listings.

## Phase 3 – Cache Refresh & Collection Scalability

### T5 – Intelligent Index Cache Invalidation
- **Status:** 🛠️ In Progress
- **Depends on:** T2
- **Linked requirements:** R2, R5
- **Purpose:** Ensure bots use fresh embeddings without full process restarts.
- **Sub-tasks:**
  - **T5.1** ✅ Replace global `index_dict` cache with per-collection handles that can be swapped post-indexing.
  - **T5.2** ✅ Hook indexing job completion events to trigger targeted cache refresh.
  - **T5.3** ⏳ Add integration tests verifying bots surface new content within SLA.

### T6 – Collection Management Performance & Bulk Operations
- **Status:** 🛠️ In Progress
- **Depends on:** T5
- **Linked requirements:** R3
- **Purpose:** Allow high-volume collection (“business”) creation without blocking the API.
- **Sub-tasks:**
  - **T6.1** ✅ Implement bulk-create endpoint or batching logic that performs a single cache refresh per request.
  - **T6.2** ✅ Make cache refresh incremental so only affected collections reload.
  - **T6.3** ⏳ Load-test collection creation to validate throughput and latency targets.

## Phase 4 – Visibility & UX Enhancements

### T7 – Persistent Ingestion Progress APIs
- **Depends on:** T2
- **Linked requirements:** R4
- **Purpose:** Give users durable status endpoints for uploads and crawls.
- **Sub-tasks:**
  - **T7.1** Implement `/ingestions/{job_id}` REST endpoint backed by job store.
  - **T7.2** Add job-event publication (polling + optional SSE/WebSocket) for near-real-time updates.
  - **T7.3** Ensure progress data survives restarts and integrates with audit logs.

### T8 – Front-end Progress & Admin Tooling
- **Depends on:** T7
- **Linked requirements:** R1, R3, R4
- **Purpose:** Surface progress and alerts in the user interface.
- **Sub-tasks:**
  - **T8.1** Update UI to show upload/crawl progress bars, ETA, and retry guidance.
  - **T8.2** Add admin dashboard widgets for queue depth, job status, and alerts.
  - **T8.3** Add e2e tests verifying progress indicators across happy/failed paths.

## Phase 5 – Performance & Observability Hardening

### T9 – Chat Agent Caching & Latency Optimization
- **Depends on:** T5
- **Linked requirements:** R2, R5
- **Purpose:** Reduce response latency by reusing pre-built agents and minimizing redundant work.
- **Sub-tasks:**
  - **T9.1** Introduce agent cache keyed by agency scope with graceful invalidation hooks.
  - **T9.2** Warm caches on startup and measure cold vs. warm latency.
  - **T9.3** Add performance tests ensuring chat p95 stays < 5 s under load.

### T10 – End-to-end Load & Resiliency Testing
- **Depends on:** T3–T9
- **Linked requirements:** R1–R5
- **Purpose:** Validate the platform meets ingestion, refresh, progress, and performance SLAs under realistic workloads.
- **Sub-tasks:**
  - **T10.1** Build load-test scenarios combining uploads, crawls, and chat traffic.
  - **T10.2** Monitor metrics dashboards to confirm success metrics are met.
  - **T10.3** Document remediation steps for any identified bottlenecks or failures.

### T11 – Release Readiness & Roll-out Plan
- **Depends on:** T10
- **Linked requirements:** R1–R5
- **Purpose:** Prepare operations, documentation, and rollout sequencing.
- **Sub-tasks:**
  - **T11.1** Update runbooks, deployment scripts, and rollback procedures.
  - **T11.2** Provide stakeholder demos highlighting new capabilities.
  - **T11.3** Schedule phased rollout with monitoring checkpoints and success validation.
