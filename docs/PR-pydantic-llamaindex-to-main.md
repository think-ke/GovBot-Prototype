## Merge pydantic-llamaindex into main

### Summary

This PR delivers a major platform upgrade focused on: 
- Migrating the AI orchestration from Pydantic-AI to LlamaIndex FunctionAgent with a backward-compatibility layer.
- Introducing a first-class Analytics microservice with data-backed metrics and an integrated admin UI.
- Strengthening privacy and security with Presidio-backed PII detection/redaction, sanitized event payloads, and audit trails.
- Adding collections persistence, improved RAG tooling, document/webpage lifecycle endpoints, and capacity/latency metrics.

These changes prepare GovStack for production workloads with clearer observability, safer data handling, and more maintainable architecture.


## What’s changed

### 1) AI Orchestration and RAG
- New LlamaIndex orchestrator and tools
  - `app/core/llamaindex_orchestrator.py` (primary agent)
  - `app/core/compatibility_orchestrator.py` (shim to preserve existing interfaces)
  - `app/core/rag/tool_loader.py` (configurable function tools per collection; alias mapping)
  - `app/core/rag/indexer.py` (batch indexing, background jobs, stats)
  - `app/core/rag/vectorstore_admin.py` (delete embeddings for documents; refresh RAG cache post-ops)
- Event tracking for LlamaIndex agent and tools (`app/core/event_orchestrator.py`, `app/utils/chat_event_service.py`)
- System prompt refined with privacy disclaimers and domain-specific guidance (`app/utils/prompts.py`)

Impact: Better retrieval quality, richer tool telemetry, and smoother migration path from legacy orchestrator.


### 2) Privacy, Security, and Compliance
- PII detection and redaction end-to-end
  - Presidio integration with safe fallback: `app/utils/presidio_pii.py` and `app/utils/pii.py`
  - Redaction applied before LLM use, before persistence, and when emitting events (defense-in-depth)
- Chat/event payload sanitization to prevent leakage of sensitive data (`app/utils/chat_event_service.py`, `app/utils/chat_persistence.py`)
- Message rating endpoints and models for explicit feedback (`app/db/models/message_rating.py`, `app/api/endpoints/rating_endpoints.py`)
- Audit trail models and endpoints (`app/db/models/audit_log.py`, `app/api/endpoints/audit_endpoints.py`)
- Documentation updates: PRIVACY_FIRST_CHATBOT_COMPLIANCE_ANALYSIS, PII_PRESIDIO_SETUP, SECURITY, RISK docs

Impact: Stronger privacy posture aligned with KDPA 2019 guidance and clearer operational controls.


### 3) Analytics (new microservice + richer metrics)
- Analytics API (separate FastAPI app under `analytics/`)
  - Usage analytics: traffic, session duration, system health, peak hours, capacity, hourly traffic, response time trends, error analysis, latency percentiles, tool usage, collections health
  - Conversation analytics: summary KPIs, flows, intents, document retrieval, drop-offs, sentiment trends, knowledge gaps, no‑answer stats, citation coverage, answer length distribution
  - User analytics: session frequency, composite sentiment (VADER + explicit ratings), top users, per-user metrics
  - Date parameters accept ISO 8601 UTC timestamps, e.g., `2025-09-01T00:00:00Z`
- Sentiment analysis with VADER and composite metrics (VADER blended with ratings)
- Extensive tests and examples under `analytics/tests` and docs (`analytics/*.md`)

Impact: Data-backed dashboards and KPIs; production-ready observability with clear schemas and examples.


### 4) Collections, Documents, and Webpages
- Collections persisted to the DB: `app/db/models/collection.py` (+ Alembic migrations)
- Document lifecycle improvements:
  - Update & optional file replacement endpoint (triggers vector cleanup + reindex)
  - Delete embeddings for a document via `vectorstore_admin.py`
- Webpage lifecycle:
  - Delete webpage endpoint and recrawl support
  - Indexing status retrieval for collections

Impact: Consistent lifecycle management with vectors kept in sync.


### 5) Admin UI and Dashboards
- Consolidated analytics UI into `admin-dashboard` (moved components and pages); removed old `analytics-dashboard` folder
  - New Next.js pages/components under `admin-dashboard/app/analytics` and `admin-dashboard/components/analytics`
  - Executive, conversation, usage, and user analytics dashboards

Impact: Single dashboard surface for administrators; simpler deployment footprint.


### 6) Deployment and Ops
- Docker Compose updates
  - New `analytics` service (FastAPI) with healthchecks
  - Upgraded images: Postgres 17.5, MinIO April 2025 build
  - Optional `analytics-dashboard` service retained under a profile but source directory was removed; see “Follow‑ups” below
- Alembic introduced for DB migrations; optional auto-create in dev behind `DB_AUTO_CREATE=true`
- Scripts: retention cleanup (90-day default), audit trail tooling, seeding collections, adding message rating tables

Impact: Clearer infra separation and smoother migrations.


## API surface (highlights)

### Core service (selected)
- Chat
  - Persistent chat endpoints with agency scoping and history retrieval
  - PII redaction applied to inbound user messages and event payloads
- Documents
  - POST /documents (upload)
  - PUT /documents/{id} (metadata update and optional file replace; triggers vector clean + reindex)
- Webpages/Collections
  - DELETE webpage
  - Collection indexing status retrieval
  - Collection stats
- Ratings (new)
  - CRUD: POST/GET/PUT/DELETE /ratings and /ratings/{id}
  - GET /ratings/stats
- Audit (new)
  - GET /audit-logs
  - GET /audit-logs/summary
  - GET /audit-logs/user/{user_id}
  - GET /audit-logs/resource/{resource_type}/{resource_id}

Security: All sensitive endpoints guarded by API key permissions (read/write/delete). OpenAPI enriched with summaries and examples.


### Analytics service (paths are prefixed by `/analytics`)
- Usage
  - GET /traffic
  - GET /session-duration
  - GET /system-health
  - GET /peak-hours
  - GET /capacity
  - GET /hourly-traffic
  - GET /response-times
  - GET /errors
  - GET /latency
  - GET /tool-usage
  - GET /collections-health
- Conversation
  - GET /summary
  - GET /flows
  - GET /intents
  - GET /document-retrieval
  - GET /drop-offs
  - GET /sentiment-trends
  - GET /knowledge-gaps
  - GET /no-answer
  - GET /citations
  - GET /answer-length
- User
  - GET /session-frequency
  - GET /sentiment
  - GET /top
  - GET /{user_id}/metrics

Notes
- Date query params accept ISO 8601 (UTC) e.g. `2025-09-01T00:00:00Z`
- Some demo endpoints were removed or replaced with data-backed versions
- Business analytics and demographic endpoints removed per scope adjustment


## Database and Migrations

Alembic is now the primary migration mechanism.

- New migrations added under `alembic/versions/`:
  - `0a20158039f4_initial_schema.py`
  - `dc617fa8ae20_add_collections_table.py`
  - `8c96491a4f7c_create_collections_table_actual.py`
- Alembic config: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`
- Env var resolution in Alembic: `DATABASE_MIGRATIONS_URL` or fallback to `DATABASE_URL`

Operational notes
- For local/dev bootstrap only, you may set `DB_AUTO_CREATE=true` to have tables created at startup. For all other environments, apply Alembic migrations explicitly.

Suggested commands (optional)

```bash
# Prepare (one‑time)
alembic upgrade head
```


## Configuration and environment

- API service (`docker-compose.yml`):
  - `DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD:-postgres}@postgres:5432/govstackdb`
  - `USE_UVLOOP` (default false)
  - `SENTRY_DSN` optional
- Analytics service: uses the same `DATABASE_URL`; exposes health check at `/analytics/health`
- Chroma: `CHROMA_HOST`, `CHROMA_PORT` set for API service; auth enabled via htpasswd
- MinIO bumped to April 2025 release; console exposed on `${MINIO_CONSOLE_PORT:-9001}`
- LLM/Embeddings configured via LlamaIndex Settings (OpenAI or Groq); see `docs/LLAMAINDEX_ORCHESTRATOR.md`


## Backward compatibility and breaking changes

- AI orchestration: legacy orchestrator kept via compatibility wrapper; default path uses LlamaIndex.
- Analytics API:
  - Several demo endpoints replaced with data-backed implementations.
  - Business analytics and demographic endpoints removed per updated scope.
  - Date params standardized to ISO 8601 strings; clients using other formats must update.
- Dashboard:
  - `analytics-dashboard/` folder removed; analytics UIs moved under `admin-dashboard/`.
  - The `analytics-dashboard` service remains in docker-compose under a profile but the source folder no longer exists.
    - If you use that profile, switch to the admin dashboard or remove the service.


## Testing and quality

- Expanded unit tests for analytics, PII redaction, and endpoints (`analytics/tests`, `tests/`)
- New pytest configs at repo root and under `analytics/`
- Manual smoke testing recommended around:
  - PII detection/redaction edge cases
  - Rating endpoints and stats
  - Audit log filters and summaries
  - Collections health, tool usage, latency/response-time trends


## How to verify (suggested)

```bash
# Run core API & dependencies
docker compose up -d --build

# Optionally run the analytics service (included in compose)
# Then visit: http://localhost:${ANALYTICS_PORT:-8005}/docs

# Admin dashboard (if enabled in compose)
# Visit: http://localhost:${ADMIN_DASHBOARD_PORT:-3010}
```


## Follow‑ups (tracked post‑merge)

1) Docker Compose clean‑up
   - Remove or repoint the `analytics-dashboard` service (source directory removed; analytics UI now in `admin-dashboard`).
   - Consider enabling the `admin-dashboard` service by default in compose.
2) Analytics privacy
   - Hash/anonymize `user_id` for analytics (e.g., `SHA256(user_id + salt)`) to strengthen privacy guarantees.
3) Retention policy
   - Schedule chat/event retention cleanup (90‑day default) and document policy.
4) Observability
   - Validate Logfire/OT instrumentation in staging; configure Sentry DSN if used.
5) Content governance
   - Iterate knowledge gaps and no‑answer heuristics using real usage data.


## Reviewer checklist

- [ ] Migrations apply on a fresh database (Alembic)
- [ ] API docs render and reflect the new endpoints (core + analytics)
- [ ] PII redaction evident in chat flows, events, and ratings feedback
- [ ] Collections lifecycle: doc update → vectors cleaned → background reindex kicks off
- [ ] Audit and rating endpoints function as documented
- [ ] Docker Compose starts core services; analytics service health passes
- [ ] Follow‑ups created to remove/repoint `analytics-dashboard` service and enable admin UI


## References

- docs/LLAMAINDEX_ORCHESTRATOR.md
- docs/PII_PRESIDIO_SETUP.md
- docs/ANALYTICS_INTEGRATION.md
- docs/ANALYTICS_MODULE_DOCUMENTATION.md
- docs/PRIVACY_FIRST_CHATBOT_COMPLIANCE_ANALYSIS.md
- docs/SECURITY.md, docs/RISK_MITIGATION_* and related


---
Completion notes
- Target branch: main
- Source branch: pydantic-llamaindex
- Type: Feature + Architecture + Privacy/Compliance


## Review feedback addressed (delta)

- app/core/rag/indexer.py
  - Clarified that indexing_progress is a percentage and kept the correct multiplier (×100) with an inline comment to avoid confusion. The earlier ×20 looked like an accidental remnant.
- app/core/rag/tool_loader.py
  - Deduplicated imports at the top of the file.
- app/api/fast_api_app.py
  - Extracted a small helper `_get_file_extension()` and reused it to remove duplicated/branchy extension parsing.
- app/utils/chat_persistence.py
  - Kept `setattr(chat, "updated_at", ...)` with a short comment, as strict SQLAlchemy typings in some stubs complain about direct assignment; this pattern is used elsewhere in the codebase and avoids false positives.
- app/core/orchestrator_clean.py
  - Deprecated placeholder slated for removal post-merge to avoid confusion; tracked in follow-ups. If no external references are found, it can be safely deleted.

No behavior changes apart from the clarified percentage output and trivial refactors above.
