# Analytics Implementation Tasks (Sequenced with Dependencies)

This plan implements the focused analytics in `requirements.md` (no business analytics and no demographics/retention/geographic). Each task links back to the requirement it satisfies and lists dependencies.

## Progress (as of 2025-09-07)
- Phase 0 health check implemented and live at `/analytics/health/db`.
- Phase 1 schemas added in `analytics/schemas.py`.
- Phase 2 services implemented for latency, tool usage, collections health, no‑answer, citations, and answer length.
- Phase 3 routes added and live for usage and conversation analytics (see corrected paths below).
- Remaining: per‑user metrics and user routes; unit tests; docs polish; perf/index review; final quality gates.

Legend:
- [R1] Metrics to Add → see requirements.md § “Metrics to Add (by area)”
- [R2] API Additions → requirements.md § “Proposed API Additions (no business, no demographics/retention/geographic)”
- [R3] Models → requirements.md § “Response Models (Pydantic)”
- [R4] Acceptance → requirements.md § “Acceptance Criteria”
- [R5] Notes → requirements.md § “Implementation Notes (SQL/ORM sketches)”


## Phase 0 — Environment Sanity (optional, fast)
1. [x] Verify analytics DB connectivity from service (ping query)
   - Link: [R4], [R5]
   - Depends: docker compose up (postgres healthy)
   - Implemented: `/analytics/health/db` executes `SELECT 1` and returns latency_ms


## Phase 1 — Schemas (must be first)
2. [x] Add new Pydantic models in `analytics/schemas.py`
   - LatencyStats {p50_ttfb_ms, p95_ttfb_ms, p99_ttfb_ms, p50_ttfa_ms, p95_ttfa_ms, p99_ttfa_ms, samples}
   - ToolUsageItem {collection_id, started, completed, failed, avg_retrieved}
   - ToolUsageResponse {overall: ToolUsageItem, by_collection: ToolUsageItem[]}
   - CollectionHealthItem {collection_id, webpages:{pages,ok,redirects,client_err,server_err,indexed}, documents:{count,indexed,public,total_size}, freshness:{last_indexed_at}}
   - NoAnswerStats {rate, examples[{chat_id,message_id,snippet}], top_triggers[]}
   - CitationStats {coverage_pct, avg_citations, by_collection[{collection_id,coverage_pct,avg_citations}]}
   - AnswerLengthStats {avg_words, median_words, distribution[{bucket,count,percentage}]}
   - UserTopItem {user_id, sessions, messages}
   - UserMetrics {sessions, messages_user, messages_assistant, avg_turns, avg_ttfb_ms, avg_ttfa_ms, no_answer_rate, rag_coverage_pct, top_collections[], last_active}
   - Link: [R3]
   - Depends: None


## Phase 2 — Service Layer (core logic)
3. [x] Implement `AnalyticsService.get_latency_stats(db, start, end)`
   - Pair chat_events by message_id for TTFB (received → response start) and TTFA (received → response completed)
   - Return percentiles
   - Link: [R1], [R2], [R5]
   - Depends: 2

4. [x] Implement `AnalyticsService.get_tool_usage(db, start, end)`
   - Summarize tool_search_documents by status and collection; compute avg retrieved from event_data.count
   - Link: [R1], [R2], [R5]
   - Depends: 2

5. [x] Implement `AnalyticsService.get_collections_health(db)`
   - Aggregate webpages and documents per collection (status breakdown, indexed, sizes, last indexed)
   - Link: [R1], [R2], [R5]
   - Depends: 2

6. [x] Implement `AnalyticsService.get_no_answer_stats(db, start, end)`
   - Scan assistant message_object.content for apology/no‑answer phrases; provide examples
   - Link: [R1], [R2], [R5]
   - Depends: 2

7. [x] Implement `AnalyticsService.get_citation_stats(db, start, end)`
   - Detect messages with `sources`; compute coverage and avg citation count; optional grouping by collection if inferable
   - Link: [R1], [R2], [R5]
   - Depends: 2

8. [x] Implement `AnalyticsService.get_answer_length_stats(db, start, end)`
   - Compute word counts and distribution buckets
   - Link: [R1], [R2], [R5]
   - Depends: 2

9. [ ] Implement `AnalyticsService.get_user_top(db, limit)`
   - Top users by sessions/messages
   - Link: [R1], [R2]
   - Depends: 2

10. [ ] Implement `AnalyticsService.get_user_metrics(db, user_id, start, end)`
    - Per‑user engagement, latency (restrict events to that user’s sessions), RAG coverage, no‑answer rate, top collections
    - Link: [R1], [R2], [R5]
    - Depends: 2, 3–8


## Phase 3 — Routers (API surface)
11. [x] Usage endpoints in `analytics/routers/usage_analytics.py`
   - GET /analytics/usage/latency → LatencyStats
   - GET /analytics/usage/tool-usage → ToolUsageResponse
   - GET /analytics/usage/collections-health → CollectionHealthItem[]
    - Link: [R2]
    - Depends: 3–5

12. [x] Conversation endpoints in `analytics/routers/conversation_analytics.py`
   - GET /analytics/conversation/no-answer → NoAnswerStats
   - GET /analytics/conversation/citations → CitationStats
   - GET /analytics/conversation/answer-length → AnswerLengthStats
    - Link: [R2]
    - Depends: 6–8

13. [ ] User endpoints in `analytics/routers/user_analytics.py`
    - GET /analytics/user/top → UserTopItem[]
    - GET /analytics/user/metrics?user_id=… → UserMetrics
    - Link: [R2]
    - Depends: 9–10


## Phase 4 — Tests (unit + edge cases)
14. [ ] Add tests under `analytics/tests/` for each endpoint
    - Happy path on current data; empty‑data returns zeros/empty arrays
    - Validate percentage units (0–100) and ms units for times
    - Link: [R4]
    - Depends: 11–13


## Phase 5 — Docs and OpenAPI polish
15. [ ] Update `analytics/README.md` with new routes and examples
    - Ensure swagger shows models with examples
    - Link: [R4]
    - Depends: 11–13


## Phase 6 — Performance and Indexes (review only)
16. [ ] Verify indexes used by queries (chat_events: message_id, session_id; chats: created_at,user_id; chat_messages: message_id, chat_id)
    - Add migration only if needed (current DB already has the critical ones)
    - Link: [R5]
    - Depends: 3–10


## Phase 7 — Quality Gates
17. [ ] Run lint/type and unit tests; smoke test `/analytics/docs`
    - Ensure shapes, units, and examples match
    - Link: [R4]
    - Depends: 14–16


## Optional Follow‑ups (not in this phase)
- Backfill `message_ratings` and add composite satisfaction.
- Day‑of‑week trends and message growth trend.

## Next Steps
- Implement per‑user service methods (tasks 9–10) and wire `/analytics/user/top` and `/analytics/user/metrics`.
- Add unit tests for all new endpoints (task 14) and update README with example responses (task 15).
- Quick index review (task 16) and final quality gates including `/analytics/docs` smoke (task 17).


## Traceability Matrix (task → requirement)
- 2 → [R3]
- 3–10 → [R1], [R2], [R5]
- 11–13 → [R2]
- 14–15 → [R4]
- 16 → [R5]
- 17 → [R4]
