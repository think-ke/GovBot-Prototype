# GovStack User Feedback Requirements

## Purpose
This document refines the user feedback stories into actionable, testable requirements for the GovStack platform. Each section captures the current gaps, scope, acceptance criteria, success metrics, technical considerations, and open questions to ensure end-to-end delivery.

---

## 1. Multi-format Document Ingestion

### Summary
Expand document ingestion beyond PDFs to support additional office formats without manual conversion. Ensure every accepted format is indexed and available to downstream experiences (search, chat, analytics).

### Current Gaps
- Upload endpoint (`app/api/fast_api_app.py::upload_document`) accepts any file but `SimpleDirectoryReader` in `download_and_process_documents` only processes `.pdf`, `.docx`, `.txt`, `.md`.
- Unsupported formats (e.g., `.doc`, `.xls/.xlsx`, `.csv`) are silently dropped during indexing, leaving users unaware of failures.
- The API buffers entire files in memory during upload, risking memory pressure for large batches.

### In Scope
- Accept, convert, and index Word (`.doc`, `.docx`), Excel (`.xls`, `.xlsx`), CSV, plain text, markdown, and PDF.
- Provide user-facing validation errors for unsupported or corrupted files.
- Preserve document metadata and link processed artifacts to collections/embeddings.

### Acceptance Criteria
1. Uploading any supported extension results in successful storage and `is_indexed=True` within one indexing cycle.
2. Unsupported files trigger a 4xx response with a clear reason before MinIO storage occurs.
3. Automated regression test covers each supported extension and validates availability through the chatbot or document listing.

### Success Metrics
- ≥95% of uploaded documents (by count) reach indexed status within 5 minutes.
- Zero silent ingestion failures for unsupported formats.

### Technical Notes
- Introduce streaming uploads to MinIO to prevent full in-memory buffering.
- Use format-specific parsers (e.g., `python-docx`, `pandas`, `unstructured`) or document conversion pipelines.
- Extend `required_exts` and ensure post-processing updates metadata consistently.

### Open Questions
- Maximum supported file size per type?
- Should spreadsheet ingestion flatten to CSV or extract each sheet separately?

---

## 2. Automatic Bot Refresh After Indexing

### Summary
Ensure bots use newly indexed content without manual restarts or cache invalidation.

### Current Gaps
- `tool_loader.get_index_dict()` caches `VectorStoreIndex` objects and is only invalidated when creating new collections.
- `start_background_document_indexing` uses `asyncio.run`, which conflicts with FastAPI's running event loop and can silently fail.
- Chat flows reuse stale indices, so new embeddings are ignored until the process restarts.

### In Scope
- Reliable indexing pipeline for uploads and crawls that updates vector stores and metadata.
- Automatic cache invalidation or live swapping of refreshed indices.
- Health and status reporting for indexing tasks.

### Acceptance Criteria
1. After an upload or crawl completes, the chatbot surfaces new content within 5 minutes without human intervention.
2. Indexing jobs execute within the existing event loop (e.g., via background tasks or worker queues) and log success/failure.
3. `/documents/indexing-status` and related endpoints reflect real-time progress and errors.

### Success Metrics
- 0% failed Live reload attempts due to event-loop conflicts.
- ≤5 minutes mean time to chatbot refresh after ingestion.

### Technical Notes
- Replace `asyncio.run` with `asyncio.create_task` or dispatch to a worker (Celery/RQ).
- Add hooks to refresh or swap the specific collection in `tool_loader` once indexing finishes.
- Emit structured events/logs for observability.

### Open Questions
- Do we need tenant-scoped cache invalidation when multiple bots share collections?

---

## 3. Scalable Ingestion & Collection Management

### Summary
Allow high-volume document uploads, concurrent crawls, and bulk collection creation without system instability.

### Current Gaps
- Uploads buffer entire files and kick off heavy indexing inline, leading to memory spikes and serialized processing.
- Crawl tracking (`crawl_tasks`) is in-memory only, lacks persistence, and does not enforce concurrency limits.
- Each collection creation triggers a full `refresh_collections()`, reloading every Chroma index and causing timeouts when creating more than a few collections.

### In Scope
- Robust ingestion pipeline capable of handling ≥10 documents (≤25 MB each) and ≥3 concurrent crawls.
- Bulk collection (“business”) creation or high-frequency single creation without reload thrashing.
- Persistent tracking for ingestion jobs and rate limiting/back-pressure.

### Acceptance Criteria
1. Uploading 10 documents concurrently completes without 5xx errors; indexing queue handles the load and reports progress.
2. Initiating 3 parallel crawls returns 202/200 responses and updates progress endpoints; additional requests beyond the limit receive a 429 with retry guidance.
3. Creating 20 collections sequentially or in batch succeeds within 30 seconds and maintains API availability.

### Success Metrics
- No process crashes or OOM events during load test (documents + crawls).
- p95 API latency < 2 s during ingestion bursts.
- Collection creation throughput ≥ 20/minute.

### Technical Notes
- Introduce background job queue (Celery/RQ/Arq) backed by Redis or Postgres for ingestion work.
- Stream uploads directly to storage and enqueue jobs referencing object metadata.
- Cache refresh should be incremental—only reload mutated collections.

### Open Questions
- Should crawl/task metadata persist in Postgres for historical analytics?
- Do we enforce per-tenant quotas or global limits?

---

## 4. User-visible Ingestion Progress

### Summary
Expose real-time or near-real-time feedback for uploads and crawls so users can monitor progress.

### Current Gaps
- Crawl status stored only in in-memory dict; lost on restart and not shareable across application instances.
- Document indexing status is aggregate and lacks phase/state tracking (e.g., queued, processing, completed, failed).
- No push mechanism (SSE/websocket) for progress updates.

### In Scope
- Persistent job records with state transitions for both uploads and crawls.
- Polling and/or streaming APIs for front-end consumption.
- UI affordances to surface progress, ETA, and next actions.

### Acceptance Criteria
1. Every ingestion job exposes an ID with a REST endpoint (`/ingestions/{id}`) returning status, progress %, timestamps, and latest message.
2. Data survives application restarts; users can resume monitoring after reconnecting.
3. Front-end e2e test confirms progress indicator updates through queued → processing → completed states for upload and crawl scenarios.

### Success Metrics
- Status updates available within ≤5 seconds of state change.
- ≤1% ingestion jobs end in “unknown” or “lost” states.

### Technical Notes
- Store job metadata in Postgres or Redis (with persistence); optionally emit events over WebSocket/SSE.
- Integrate with background job system to update status transitions.

### Open Questions
- Preferred communication channel for the front-end (poll vs. push)?
- Should the API support cancellation or retry operations?

---

## 5. Responsive Chat & Platform Performance

### Summary
Reduce perceived lag in chat interactions and keep the platform responsive under load.

### Current Gaps
- `run_llamaindex_agent` rebuilds `FunctionAgent` per request, reprocessing `collection_dict` and tool definitions, increasing latency.
- `refresh_collections()` reloads every index even when only one collection changes.
- Upload and crawl endpoints perform heavy lifting (embedding, logging) synchronously.

### In Scope
- Cache and reuse chat agent instances with safe invalidation.
- Offload heavy compute/IO to background workers.
- Establish performance monitoring with actionable thresholds.

### Acceptance Criteria
1. Chat requests return within 2 s on average (p95 < 5 s) during normal load and while ingestion tasks run.
2. Agent instantiation is cached; cold start < 500 ms, warm start near-instant.
3. Observability dashboards expose latency, queue depth, and error rates with alerts on SLA breaches.

### Success Metrics
- Chat p95 latency < 5 s, ingestion queue wait time < 2 min.
- CPU utilization < 80% during load test, memory usage stable (<75% of available RAM).

### Technical Notes
- Pre-initialize agents per agency and evict selectively when collections refresh.
- Employ asynchronous logging/batch operations; avoid blocking the request loop.
- Add Prometheus/Grafana metrics or integrate with existing monitoring stack.

### Open Questions
- Do we need multi-region deployment considerations for latency?
- Should we expose backpressure signals to clients (e.g., queue spot number)?

---

## General Dependencies & Risks
- Reliable task queue or background worker infrastructure is a prerequisite for stories 2–4.
- Enhanced format support may introduce new third-party library dependencies; ensure licensing and security reviews.
- Need coordinated UX updates to surface progress indicators and error messaging.
- Performance targets rely on adequate infrastructure sizing; revisit Docker Compose resources or cloud deployment limits.

---

## Next Steps
1. Align stakeholders on acceptance criteria and success metrics.
2. Prioritize implementation order (recommend: background job framework → ingestion pipeline → cache refresh → UX enhancements).
3. Produce engineering design docs for high-impact changes (task queue, agent caching).
4. Update automated tests and CI pipelines to cover new functionality.
