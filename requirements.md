# Analytics Requirements (Focused, Data‑Driven)

Purpose: finalize analytics with concrete, implementable metrics based on the current database and codebase. Exclude business analytics and exclude demographics, retention, and geographic from user analytics.

Scope (included)
- Usage metrics: traffic, latency, errors, tool usage (RAG), collection health.
- Conversation metrics: depth/flows, no‑answer rate, citation usage, answer length.
- User‑specific metrics: per‑user engagement, RAG usage, latency, no‑answer.

Out of scope (explicitly excluded now)
- Business analytics (ROI, containment dashboards, etc.).
- User demographics, retention, and geographic distribution.

Data sources discovered (govstackdb)
- chats(id, session_id, user_id, created_at, updated_at)
- chat_messages(id, chat_id, message_id, message_type, message_object JSON, timestamp)
- chat_events(id, session_id, message_id, event_type, event_status, event_data JSON, timestamp, processing_time_ms)
- documents(id, filename, object_name, size, collection_id, is_indexed, indexed_at, is_public, meta_data)
- webpages(id, url, status_code, collection_id, is_indexed, indexed_at, content_markdown, meta_data)
- collections(id, name, collection_type, api_key_name, created_at, updated_at)
- audit_logs(... minimal relevance)
- message_ratings exists but currently empty (0 rows) — keep optional.

Highlights from data scan
- 7,198 messages (user 4,167; assistant 3,031) across 3,567 chats.
- chat_events contains response_generation and tool_search_documents with shared message_id → enables latency and RAG metrics.
- tool_search_documents has event_data { collection, count } → per‑collection usage and retrieval counts.
- Assistant messages often include sources in message_object (sources key) → citation coverage and average citations.
- Collections present: kfcb, kfc, brs, odpc, THiNK, etc. Web crawl coverage and indexing health are trackable per collection.


## User Stories

- As a PM, I want to see system response latency percentiles so I can track performance regressions.
- As a PM, I want to monitor no‑answer/apology rate and top prompts that trigger it to improve answer coverage.
- As a PM, I want to know the percent of answers with citations and average citations per answer to verify RAG quality.
- As a Content Owner, I want to see collection usage and retrieval success/failures to prioritize curation.
- As a Content Owner, I want to see crawl/indexing health (4xx/5xx and indexed coverage) per collection to fix ingestion issues.
- As a User Success Lead, I want user‑specific metrics (sessions, messages, latency, RAG usage, no‑answer rate) to understand power users and issues.
- As an Engineer, I want error rates by type/status from chat_events to detect failing stages and tools.


## Metrics to Add (by area)

### Usage metrics
1) Request throughput
- Daily sessions and messages (already derivable; keep existing TrafficMetrics.growth_trend for sessions and add messages trend if needed).

2) Response latency percentiles (P50/P95/P99)
- From chat_events: time between message_received.completed and response_generation.started (TTFT proxy), and to response_generation.completed (TTFA).
- Also compute per‑stage processing_time_ms where present (e.g., agent_thinking).

3) Error rates and types
- Group by event_type, event_status with counts; surface failures (e.g., error.failed, tool_search_documents.failed).

4) Tool usage (RAG)
- Counts of tool_search_documents started/completed/failed; avg retrieval count (AVG(event_data.count)).
- Breakdown by collection.

5) Hourly traffic pattern (24 buckets UTC)
- Sessions and messages per hour across window.

6) Peak hours/days
- Top 3–5 hours by sessions.
- Optional: day‑of‑week distribution.

### Conversation metrics
1) Conversation depth and flows
- Distribution by message_count buckets; completion/abandonment heuristic (already implemented; keep/improve).

2) No‑answer/apology rate
- Share of assistant messages matching apology/no‑answer phrases (e.g., "I’m sorry, but I don’t have that information").
- Top user prompts leading to no‑answer.

3) Citation coverage
- Percent of assistant messages that include sources.
- Average citations per answered message; distribution by collection (if sources contain collection/object hints).

4) Answer length stats
- Average and distribution of assistant content length (words/characters);
- Optional: very‑short answers rate (<20 words) flagged.

5) Conversation summary KPIs
- Total conversations, average turns per conversation, estimated completion rate (already scaffolded).

### Content/Collection health and usage
1) Collection usage
- Unique sessions/messages using each collection via tool_search_documents event_data.collection.
- Unique users per collection (join session → chat.user_id).
- Retrieval successes vs failures per collection; avg items retrieved.

2) Crawl/indexing health (webpages)
- Per collection: pages, ok (2xx), client_err (4xx), server_err (5xx), indexed, %indexed, last indexed_at recency.

3) Document indexing
- Per collection: documents, total size, indexed count, public docs count, last indexed_at recency.

### User‑specific metrics (per user_id)
- sessions, total messages (+ split user/assistant), avg turns per session.
- average response latency (TTFT/TTFA as above).
- no‑answer/apology rate for that user’s conversations.
- RAG usage rate (# answers with sources / total answers) and tool usage counts.
- top collections used; last active timestamp.


## Proposed API Additions (no business, no demographics/retention/geographic)

Keep existing routes in analytics service and add the following. All accept optional start_date/end_date (ISO‑8601), defaulting to last 30 days.

Usage
- GET /analytics/usage/latency
  - Returns: { p50_ttfb_ms, p95_ttfb_ms, p99_ttfb_ms, p50_ttfa_ms, p95_ttfa_ms, p99_ttfa_ms, samples }
  - Method: compute diffs between chat_events message_received.completed → response_generation.started (TTFB) and → response_generation.completed (TTFA) per message_id.

- GET /analytics/usage/tool-usage
  - Returns: overall + per‑collection stats { started, completed, failed, avg_retrieved }
  - Source: chat_events where event_type='tool_search_documents'; parse event_data.collection and event_data.count.

- GET /analytics/usage/collections/health
  - Returns: array per collection with webpages and documents health: { collection_id, webpages: { pages, ok, 4xx, 5xx, indexed }, documents: { count, indexed, public, total_size }, freshness: { last_indexed_at } }
  - Source: webpages, documents.

Conversation
- GET /analytics/conversation/no-answer-rate
  - Returns: { rate, examples: [ {chat_id, message_id, snippet} ], top_triggers: [phrases] }
  - Method: text match in assistant message_object.content for apology/no‑answer patterns.

- GET /analytics/conversation/citation-stats
  - Returns: { coverage_pct, avg_citations, by_collection: [ {collection_id, coverage_pct, avg_citations} ] }
  - Method: check message_object.sources array; infer collection_id from source metadata if available.

- GET /analytics/conversation/answer-length
  - Returns: distribution buckets by word count, plus avg/median.

User
- GET /analytics/user/top
  - Returns: top users by sessions/messages: [ { user_id, sessions, messages } ]

- GET /analytics/user/metrics?user_id=...
  - Returns per‑user metrics: { sessions, messages_user, messages_assistant, avg_turns, avg_ttfb_ms, avg_ttfa_ms, no_answer_rate, rag_coverage_pct, top_collections: [...], last_active }

Note: Do not add business endpoints in this phase.


## Implementation Notes (SQL/ORM sketches)

Latency (TTFB/TTFA)
- Pair events by message_id:
  - first message_received.completed ts as user_ts
  - response_generation.started ts as gen_start_ts (TTFB)
  - response_generation.completed ts as gen_end_ts (TTFA)
- Compute EXTRACT(EPOCH FROM (gen_start_ts - user_ts))*1000 for TTFB; similarly for TTFA.

Tool usage & per‑collection
- SELECT event_status, event_data->>'collection' AS collection_id, COUNT(*), AVG((event_data->>'count')::int)
  FROM chat_events WHERE event_type='tool_search_documents' GROUP BY 1,2;

Citation coverage
- In chat_messages where message_type='assistant':
  - CASE WHEN jsonb_typeof(message_object::jsonb)='object' AND (message_object::jsonb ? 'sources') THEN TRUE ELSE FALSE END
  - Optionally, sources array length as citation count.

No‑answer rate
- Text match on assistant content (lower(content) LIKE patterns: 'i\'m sorry', 'i do not have that information', 'i don’t have', etc.).

Answer length
- Word count: array_length(regexp_split_to_array(content, '\s+'), 1)

Collection health
- documents grouped by collection_id; webpages grouped by collection_id with status_code ranges and is_indexed.

User‑specific
- sessions/messages by joining chats → chat_messages; latency via chat_events filtered to those sessions; RAG coverage for that user from assistant messages in those chats.


## Response Models (Pydantic)

Add small schemas aligned to the above (examples):
- LatencyStats: p50_ttfb_ms, p95_ttfb_ms, p99_ttfb_ms, p50_ttfa_ms, p95_ttfa_ms, p99_ttfa_ms, samples
- ToolUsageItem: collection_id, started, completed, failed, avg_retrieved
- CollectionHealthItem: collection_id, webpages: { pages, ok, redirects, client_err, server_err, indexed }, documents: { count, indexed, public, total_size }, freshness: { last_indexed_at }
- NoAnswerStats: rate, examples[], top_triggers[]
- CitationStats: coverage_pct, avg_citations, by_collection[]
- AnswerLengthStats: avg_words, median_words, distribution[]
- UserTopItem: user_id, sessions, messages
- UserMetrics: as listed above

These can live in analytics/schemas.py and be returned by new endpoints in usage_analytics.py, conversation_analytics.py, and user_analytics.py.


## Acceptance Criteria
- All new endpoints return 200 with correctly shaped data on current dataset.
- No business analytics endpoints introduced in this phase.
- No demographics/retention/geographic endpoints changed or required by the dashboard now.
- Percentages use 0–100 scale; times are in milliseconds; dates UTC.
- OpenAPI docs describe each metric clearly; examples included.


## Quick Validation on Current Data (evidence)
- tool_search_documents present with event_data.collection (e.g., odpc) and event_data.count → collection usage feasible.
- response_generation and message_received share message_id → latency feasible.
- Assistant messages include sources → citation metrics feasible.
- Webpages/documents per collection with indexed and status_code → health metrics feasible.
- chats.user_id populated for many sessions → user‑specific metrics feasible.


## Next Steps
- Implement endpoints and schemas; wire into admin dashboards where relevant.
- Add unit tests for empty data and normal data paths.
- Consider backfilling message_ratings for composite satisfaction later.
