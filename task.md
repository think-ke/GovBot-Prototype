# Analytics Implementation Tasks (Sequenced with Dependencies)

This plan implements the focused analytics in `requirements.md` (no business analytics and no demographics/retention/geographic). Each task links back to the requirement it satisfies and lists dependencies.

## Progress (as of 2025-09-07)
- Phase 0 health check implemented and live at `/analytics/health/db`.
- Phase 1 schemas added in `analytics/schemas.py`.
- Phase 2 services implemented for latency, tool usage, collections health, no‑answer, citations, and answer length.
- Phase 3 routes added and live for usage and conversation analytics (see corrected paths below).
- Phase P replacements: System Health, Hourly Traffic, Response Time Trends, and Errors are now data‑backed and live.
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

---

## Phase P — Replace Placeholder Metrics with Data-Backed Implementations

This section lists concrete tasks to replace demo/placeholder endpoints using existing DB tables (chat_events, chat_messages, chats, documents, webpages, collections). Implement where feasible without external telemetry.

P1) Usage → System Health (data-backed)
- Goal: Populate P50/P95/P99 (reuse latency), error_rate, uptime approximation.
- Data: chat_events (message_received, agent_thinking, response_generation, error)
- Tasks:
   - [x] Service: `get_system_health(db, hours=24)` → compute response percentiles (from existing latency CTE), error_rate = errors/requests, uptime = % of 1‑min buckets in window with any activity.
   - [x] Router: use service (replace demo) and keep `SystemHealth` schema.
   - [ ] Swagger: document heuristics for uptime.
- Acceptance:
   - [x] Percentiles ≥ 0; error_rate, uptime_percentage in [0,100]; availability derived by thresholds.

P2) Usage → Hourly Traffic (data-backed)
- Goal: 24 UTC buckets with sessions and messages across N days.
- Data: chats.created_at, chat_messages.timestamp
- Tasks:
   - [x] Service: `get_hourly_traffic(db, days=7)` aggregating by extract(hour) with zero‑fill.
   - [x] Router: call service (replace demo).
- Acceptance:
   - [x] 24 buckets "00".."23"; integer counts; zero for empty hours.

P3) Usage → Response Time Trends (data-backed)
- Goal: Daily P50/P95/P99 (TTFA) for last N days.
- Data: chat_events (reuse latency join) grouped by date
- Tasks:
   - [x] Service: `get_response_time_trends(db, days=7)`.
   - [x] Router: call service (replace demo).
- Acceptance:
   - [x] N points with p50/p95/p99 or [] when no data.

P4) Usage → Errors (data-backed)
- Goal: error_rate, total_errors, error_types breakdown.
- Data: chat_events where event_type='error'
- Tasks:
   - [x] Service: `get_error_analysis(db, hours=24)` grouping by COALESCE(event_data->>'error_type', event_data->>'reason','error').
   - [x] Router: call service (replace demo).
- Acceptance:
   - [x] error_rate in [0,100]; total_errors integer; error_types map present when errors>0.

P5) Usage → Capacity (approximation)
- Goal: capacity_utilization, concurrent_sessions, scaling status.
- Data: chat_events intervals per message (received→first response start/end).
- Tasks:
   - [x] Service: `get_capacity_metrics(db, hours=24, max_capacity: int)` estimating 95th percentile concurrency vs max.
   - [x] Router: call service (replace demo).
   - [ ] Config: env var `MAX_CONCURRENCY_CAPACITY` with safe default.
- Acceptance:
   - [x] utilization in [0,100]; concurrent_sessions ≥ 0; status derived by thresholds.

P6) Conversation → Intents (heuristic)
- Goal: Basic intent labels without external NLP.
- Data: chat_messages (user); chat_events proximity for tool use
- Tasks:
   - [ ] Service: `get_intent_analysis(db, start, end, limit=20)` using ILIKE keyword patterns and tool_search_documents signals.
   - [ ] Router: replace demo; mark heuristic in description.
- Acceptance:
   - [ ] Non‑empty list when data exists; success_rate proxy via citation/no‑answer.

P7) Conversation → Document Retrieval (data-backed)
- Goal: Per‑collection access_frequency and success_rate.
- Data: chat_events where event_type='tool_search_documents'
- Tasks:
   - [ ] Service: `get_document_retrieval_analysis(db, start, end)` computing counts and success_rate = completed/(started+failed).
   - [ ] Router: replace demo.
- Acceptance:
   - [ ] Ordered by access_frequency; success_rate in [0,100].

P8) Conversation → Drop‑offs (data-backed)
- Goal: Abandonment by turn buckets.
- Data: chat_messages counts per chat
- Tasks:
   - [ ] Service: `get_drop_offs(db, start, end)` bucketing message counts (1‑2, 3‑5, 6‑10, 11‑20, 21+).
   - [ ] Router: replace demo; optional triggers from recent error/no‑answer keywords.
- Acceptance:
   - [ ] DropOffPoint list populated when data exists.

P9) Conversation → Sentiment Trends (data-backed)
- Goal: Distribution of positive/neutral/negative.
- Data: chat_messages (user) + existing `sentiment_analyzer`
- Tasks:
   - [ ] Service: `get_sentiment_trends(db, start, end)` aggregating analyzer outputs.
   - [ ] Router: replace demo.
- Acceptance:
   - [ ] Keys sum to ~100 when messages exist.

P10) Conversation → Knowledge Gaps (heuristic)
- Goal: Topics where answers underperform.
- Data: user messages preceding no‑answer or error; assistant citations
- Tasks:
   - [ ] Service: `get_knowledge_gaps(db, start, end, threshold=0.3)` with naive keyword extraction; success proxy via citations or no‑answer inverse.
   - [ ] Router: replace demo; mark heuristic.
- Acceptance:
   - [ ] Topics with query_frequency>0; success_rate in [0,100].

P11) Conversation → Flows average_response_time (data-backed)
- Goal: Replace placeholder 30.0 with real average per bucket.
- Data: chat_events; deltas from message_received → first agent_thinking/response_generation
- Tasks:
   - [ ] Enhance `get_conversation_turn_analysis` to compute `average_response_time`.
- Acceptance:
   - [ ] Non‑zero averages where events exist; buckets unchanged.


## Traceability Matrix (task → requirement)
- 2 → [R3]
- 3–10 → [R1], [R2], [R5]
- 11–13 → [R2]
- 14–15 → [R4]
- 16 → [R5]
- 17 → [R4]
