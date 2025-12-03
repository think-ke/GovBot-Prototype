# Analytics Module Requirements

Purpose: finalize the Analytics microservice so the Admin Dashboard’s analytics screens can be fully data-driven (no hardcoded UI values). This document specifies the APIs, models, and behaviors required, aligned to the current frontend components under `admin-dashboard/components/analytics`.

Scope:
- Ensure all metrics and charts in Executive, User, Usage, and Conversation dashboards can be powered entirely by the analytics API.
- Add missing endpoints and schemas; standardize units and payload shapes.
- Maintain consistency across date filtering and response contracts.

Out of scope (for now):
- Deep infra metrics (CPU/memory/network) backed by Prometheus/Grafana.
- Authentication and RBAC for analytics endpoints (can be added later if needed).


## 1. Current State Summary

Backend services exist with these routers and baseline endpoints:
- User Analytics: `/analytics/user/{demographics, session-frequency, sentiment, retention, geographic}` (note: `geographic` is currently a stub; `retention` returns a raw dict, no schema)
- Usage Analytics: `/analytics/usage/{traffic, session-duration, system-health, peak-hours, errors}` (time-series gaps remain; several are placeholders)
- Conversation Analytics: `/analytics/conversation/{flows, intents, document-retrieval, drop-offs, sentiment-trends, knowledge-gaps}` (some endpoints return raw dicts; success_rate units differ from UI expectations)
- Business Analytics: `/analytics/business/{roi, containment, business-flow-success, cost-analysis, performance-benchmarks, dashboard/executive, dashboard/*}`

Frontend usage expectations (from Admin Dashboard UI):
- Executive dashboard needs: Executive KPIs, intent-based service distribution, growth trends for sessions (and ideally users), system health highlights.
- User dashboard needs: demographics, session-frequency distribution, retention (D1/D7/D30), user sentiment, device distribution, geographic distribution.
- Usage dashboard needs: hourly traffic series (sessions/messages), response time trends (p50/p95/p99 over time), peak hours and peak days, session duration, error analysis.
- Conversation dashboard needs: conversation flows (chartable by turn buckets), top intents, document retrieval performance, drop-off points, sentiment trends over time, knowledge gaps (with percent), conversation summary KPIs.


## 2. Gaps and Requirements

2.1 Standardize schemas for dict-returning endpoints
- Add Pydantic models in `schemas.py` for the following:
  - RetentionData
  - PeakHoursResponse
  - ErrorAnalysis
  - DropOffData
  - SentimentTrends
  - KnowledgeGaps
  - ConversationSummary (new)
  - HourlyTrafficPoint (new), ResponseTimesPoint (new)
  - GeographicDistribution (new)
  - DeviceDistribution (optional)

2.2 Unit normalization
- Knowledge gaps success_rate currently shown in UI as percentage; backend returns fractions (e.g., 0.25). Standardize on percentage [0-100] in API responses.

2.3 Time-series additions
- Usage hourly traffic: add endpoint returning aggregated 24-hour series for sessions and messages.
- Usage response time trends: add endpoint returning p50/p95/p99 over a time window.
- Peak days: either derive server-side from sessions by weekday or add endpoint.
- (Optional) User growth trend (daily new/active users) to power multi-line “Growth Trends”. Alternatively, Executive “Growth Trends” can show sessions-only for now.

2.4 Conversation summary KPIs
- Add conversation summary endpoint with total conversations, average turns, and completion rate to feed Conversation overview cards accurately.

2.5 Implement geographic and device distributions
- Implement `/analytics/user/geographic` to provide top locations and percentages.
- (Optional) Implement `/analytics/user/devices` if user-agent/device data is available; otherwise postpone and hide the UI section.


## 3. API Specifications (New/Updated)

All endpoints accept optional `start_date` and `end_date` (ISO 8601) unless noted. Defaults: last 30 days when dates omitted.

### 3.1 User Analytics

3.1.1 Retention model (new model)
- Route: `GET /analytics/user/retention`
- Response model: `RetentionData`
```json
{
  "day_1_retention": 65.5,
  "day_7_retention": 42.3,
  "day_30_retention": 28.7,
  "cohort_analysis": []
}
```

3.1.2 Geographic distribution (implement)
- Route: `GET /analytics/user/geographic`
- Response model: `List[GeographicDistribution]`
```json
[
  { "location": "Capital Region", "users": 485, "percentage": 26.2 },
  { "location": "Northern Province", "users": 320, "percentage": 17.3 },
  { "location": "Other Regions", "users": 310, "percentage": 16.8 }
]
```

3.1.3 Device distribution (optional)
- Route: `GET /analytics/user/devices`
- Response model: `List[DeviceDistribution]`
```json
[
  { "name": "Mobile", "value": 65 },
  { "name": "Desktop", "value": 28 },
  { "name": "Tablet", "value": 7 }
]
```

3.1.4 (Optional) User growth trend
- Route: `GET /analytics/user/growth-trend`
- Response model: `List[TrendData]` (date, value for users)

### 3.2 Usage Analytics

3.2.1 Hourly traffic (new)
- Route: `GET /analytics/usage/hourly-traffic`
- Query: `days` (int, default 7)
- Response model: `List[HourlyTrafficPoint]`
```json
[
  { "hour": "00", "sessions": 45, "messages": 120 },
  { "hour": "01", "sessions": 32, "messages": 89 }
]
```

3.2.2 Response time trends (new)
- Route: `GET /analytics/usage/response-times`
- Query: `days` (int, default 7)
- Response model: `List[ResponseTimesPoint]`
```json
[
  { "day": "2025-08-25", "p50": 180, "p95": 450, "p99": 680 },
  { "day": "2025-08-26", "p50": 165, "p95": 420, "p99": 650 }
]
```

3.2.3 Peak days (optional)
- Route: `GET /analytics/usage/peak-days`
- Query: `days` (int, default 7)
- Response: `[{ "day": "Wednesday", "load": 92 }, ...]`

3.2.4 Peak hours (keep, formalize model)
- Route: `GET /analytics/usage/peak-hours`
- Query: `days` (int, default 7)
- Response model: `PeakHoursResponse`
```json
{
  "peak_hours": [ { "hour": 14, "sessions": 225 } ],
  "analysis_period": "7 days",
  "timezone": "UTC"
}
```

3.2.5 Error analysis (keep, formalize model)
- Route: `GET /analytics/usage/errors`
- Query: `hours` (int, default 24)
- Response model: `ErrorAnalysis`

### 3.3 Conversation Analytics

3.3.1 Conversation summary (new)
- Route: `GET /analytics/conversation/summary`
- Response model: `ConversationSummary`
```json
{ "total_conversations": 2450, "avg_turns": 3.2, "completion_rate": 82.4 }
```

3.3.2 Knowledge gaps (unit update + model)
- Route: `GET /analytics/conversation/knowledge-gaps`
- Response model: `KnowledgeGaps`
- Success rate: return percentages (e.g., 62.3) instead of fractions.
```json
{
  "knowledge_gaps": [
    {
      "topic": "tax_exemption_process",
      "query_frequency": 45,
      "success_rate": 62.3,
      "example_queries": ["How to apply for tax exemption?", "Tax exemption eligibility criteria"]
    }
  ],
  "recommendations": ["Add more content about tax exemption processes"]
}
```

3.3.3 Conversation flows (unchanged, ensure mapping)
- Model: `ConversationFlow` with fields `{ turn_number, completion_rate, abandonment_rate, average_response_time }`.
- Frontend will map to chart fields `turn`, `completion`, `abandonment`.

3.3.4 Sentiment trends (model)
- Route: `GET /analytics/conversation/sentiment-trends`
- Response model: `SentimentTrends`
- Optional: extend to include historical buckets if available later; for now snapshot distribution is acceptable.

3.3.5 Drop-offs (model)
- Route: `GET /analytics/conversation/drop-offs`
- Response model: `DropOffData`


## 4. Models to Add to `schemas.py`

Add the following Pydantic models:

```python
class RetentionData(BaseModel):
    day_1_retention: float
    day_7_retention: float
    day_30_retention: float
    cohort_analysis: List[Dict[str, Any]] = []

class GeographicDistribution(BaseModel):
    location: str
    users: int
    percentage: float

class DeviceDistribution(BaseModel):
    name: str
    value: float  # percentage 0-100

class HourlyTrafficPoint(BaseModel):
    hour: str  # "00".."23"
    sessions: int
    messages: int

class ResponseTimesPoint(BaseModel):
    day: datetime | str  # ISO date or date string
    p50: float
    p95: float
    p99: float

class PeakHoursResponse(BaseModel):
    peak_hours: List[Dict[str, int]]  # {hour, sessions}
    analysis_period: str
    timezone: str

class ErrorAnalysis(BaseModel):
    error_rate: float
    total_errors: int
    error_types: Dict[str, int]
    analysis_period: str

class DropOffPoint(BaseModel):
    turn: int
    abandonment_rate: float

class DropOffData(BaseModel):
    drop_off_points: List[DropOffPoint]
    common_triggers: List[str]

class SentimentTrends(BaseModel):
    sentiment_distribution: Dict[str, float]  # {positive, neutral, negative} as percentages
    satisfaction_indicators: List[str]

class KnowledgeGap(BaseModel):
    topic: str
    query_frequency: int
    success_rate: float  # percentage 0-100
    example_queries: List[str]

class KnowledgeGaps(BaseModel):
    knowledge_gaps: List[KnowledgeGap]
    recommendations: List[str] | None = None

class ConversationSummary(BaseModel):
    total_conversations: int
    avg_turns: float
    completion_rate: float
```

Note: maintain existing models; only add the above. Where dates are returned as strings, ensure JSON serialization is consistent.


## 5. Endpoint Implementation Notes

- Date filtering: Default to last 30 days if `start_date`/`end_date` are absent. Use UTC.
- Derivations:
  - Hourly traffic: aggregate Chats and ChatMessages by hour (UTC), return 24 buckets with summed sessions/messages over the period.
  - Response time trends: If real monitoring data isn’t available, approximate from SystemHealth snapshots or compute server-side response time percentiles by day (if feasible), else return placeholders now with the trend shape and clearly mark in code.
  - Peak days: derive from `TrafficMetrics.growth_trend` grouped by weekday; return top 3-4 days with relative load%.
  - Conversation summary: compute total conversation count over range; avg turns from ChatMessage counts per Chat; completion_rate heuristic can reuse existing flow analysis logic.
  - Geographic/device distributions: only implement if data exists in DB (e.g., user metadata or message headers). Otherwise, return `status: not_implemented` with 501 status or keep excluded until data is available.
- Units: Return percentages as 0–100 floats with one decimal where sensible.
- Performance: Index by `created_at`, `user_id`, and joins across `Chat` and `ChatMessage` used in aggregation.
- Pagination: Not required for these summaries; ensure limits where arrays may grow (e.g., intents `limit` param already exists).
- CORS: Already enabled; keep wildcard for dev; tighten in production.


## 6. Frontend Alignment Notes (FYI)

- Executive dashboard:
  - Growth Trends can initially show sessions-only from `TrafficMetrics.growth_trend` if user growth trend isn’t added yet.
  - Satisfaction score for achievements can use `/analytics/user/sentiment` → `satisfaction_score`.
- User dashboard:
  - Retention: `/analytics/user/retention` → `RetentionData`.
  - Devices/Geographic: wire only when endpoints implemented; hide otherwise.
- Usage dashboard:
  - Hourly AreaChart: `/analytics/usage/hourly-traffic`.
  - Response Time LineChart: `/analytics/usage/response-times`.
  - Peak Hours: `/analytics/usage/peak-hours`.
  - Peak Days: `/analytics/usage/peak-days` or derive.
- Conversation dashboard:
  - Use `/analytics/conversation/flows` mapped to chart fields (turn/ completion/ abandonment).
  - Use `/analytics/conversation/summary` for KPIs (total conversations, avg turns, completion rate).
  - Knowledge gaps success_rate assumed as percentage (post-change).


## 7. Testing & Quality Gates

- Unit tests in `analytics/`:
  - Test each new endpoint returns correctly shaped data and handles empty datasets.
  - Validate percentage unit conversions (knowledge gaps).
  - Validate date window defaults and parameter parsing.
- Lint/typecheck: run flake8/ruff and mypy if configured.
- Smoke test: `GET /analytics/health` returns healthy; each new route returns 200 with default data.
- Performance sanity: endpoints complete under ~500ms on dev data; if not, add indexes or reduce default ranges.


## 8. Definition of Done (DoD)

- All specified endpoints implemented with Pydantic models; OpenAPI docs render correctly at `/analytics/docs`.
- Admin Dashboard charts and KPIs load without hardcoded fallbacks in production mode.
- Unit tests for new endpoints pass in CI.
- Readme updated with base URL and available routes (this file + `analytics/README.md`).


## 9. Implementation Checklist (Prioritized)

1) Schemas
- [x] Add new Pydantic models listed in Section 4 to `schemas.py`.
- [x] Update existing endpoints to use these models where applicable (retention, errors, peak-hours, sentiment-trends, knowledge-gaps, drop-offs).
- [x] Normalize `knowledge_gaps.success_rate` to percentage.

2) Conversation
- [x] Implement `GET /analytics/conversation/summary` using DB aggregations.
- [x] Ensure `/analytics/conversation/flows` still returns buckets; no change to model.

3) Usage time-series
- [x] Implement `GET /analytics/usage/hourly-traffic?days=N` (aggregate by hour).
- [x] Implement `GET /analytics/usage/response-times?days=N` (real or approximated series).
- [ ] (Optional) Implement `GET /analytics/usage/peak-days?days=N` or derive in code.

4) User enrichments
- [ ] Implement `GET /analytics/user/geographic` if data exists; else mark intentionally unimplemented (501) and hide UI.
- [ ] (Optional) Implement `GET /analytics/user/devices` if UA/device data exists.
- [ ] (Optional) Implement `GET /analytics/user/growth-trend` for executive growth chart.

5) Docs & tests
- [ ] Update `analytics/README.md` with new routes and examples.
- [ ] Add unit tests for all new endpoints and edge cases.
- [ ] Verify OpenAPI shows correct models and fields.

6) Non-functional
- [ ] Ensure CORS covers Admin Dashboard origin.
- [ ] Confirm indexes exist on `Chat.created_at`, `Chat.user_id`, `ChatMessage.timestamp` for aggregation queries.


## 10. Appendix: Example Queries (Dev)

- Check health: `GET /analytics/health`
- User: `GET /analytics/user/demographics`, `GET /analytics/user/retention`
- Usage: `GET /analytics/usage/traffic`, `GET /analytics/usage/hourly-traffic?days=7`
- Conversation: `GET /analytics/conversation/summary`, `GET /analytics/conversation/flows`

Note: base URL is the analytics service (e.g., `http://localhost:8005`). Admin Dashboard should use `NEXT_PUBLIC_ANALYTICS_API_URL`.
