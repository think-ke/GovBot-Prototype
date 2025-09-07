# Analytics Microservice

This microservice provides comprehensive analytics capabilities for the GovStack AI-powered eCitizen Services platform.

## Overview

The analytics service is organized into four key analytics categories based on the dashboard specification:

1. **User Analytics** - Understanding citizen demographics, behavior patterns, and satisfaction
2. **Usage Analytics** - Monitoring system health, traffic patterns, and operational metrics  
3. **Conversation Analytics** - Analyzing dialogue flows, intent patterns, and conversation quality
4. **Business Analytics** - Measuring ROI, automation rates, and business-critical objectives

## API Endpoints

### User Analytics (`/analytics/user`)
- `GET /demographics` - User demographics and growth metrics
- `GET /session-frequency` - Session frequency analysis
- `GET /sentiment` - User sentiment and satisfaction metrics
- `GET /retention` - User retention analysis by cohorts
- `GET /geographic` - Geographic distribution of users

### Usage Analytics (`/analytics/usage`)
- `GET /traffic` - Traffic and volume metrics
# Analytics Microservice

FastAPI service that powers the GovStack analytics dashboards. It aggregates traffic, usage, and conversation insights from the shared database and exposes typed APIs for the frontend.

## What’s included

- FastAPI app with OpenAPI docs at `/analytics/docs`
- Routers: User, Usage, Conversation (business analytics code exists but is not wired by default)
- Pydantic schemas aligned with the analytics dashboard UI
- Service health checks (app and DB)
- Optional composite user sentiment using VADER + explicit ratings

## Service base and health

- Service root: `GET /analytics` (lists base paths and version)
- Liveness: `GET /analytics/health`
- DB connectivity: `GET /analytics/health/db`
- Docs: Swagger `/analytics/docs`, ReDoc `/analytics/redoc`

## Active API endpoints

The app includes three routers by default (see `analytics/main.py`). Dates accept ISO 8601 UTC, e.g., `2025-09-01T00:00:00Z`.

### User Analytics (`/analytics/user`)
- `GET /session-frequency` — Top users by sessions and visit history
- `GET /sentiment` — Composite sentiment and satisfaction (VADER + ratings)
- `GET /top` — Top users ranked by sessions/messages
- `GET /{user_id}/metrics` — Per-user KPIs across the selected window

Note: Demographics, retention, and geographic endpoints are not enabled by default in the current router.

### Usage Analytics (`/analytics/usage`)
- `GET /traffic` — Sessions, messages, unique users, peak hours, trend
- `GET /session-duration` — Avg/median duration and distribution buckets
- `GET /system-health` — Response times (p50/p95/p99), error rate, uptime window
- `GET /peak-hours` — Ranked busy hours (UTC)
- `GET /capacity` — Utilization vs configured capacity with tips
- `GET /errors` — Error rate and breakdown
- `GET /hourly-traffic` — 24 buckets aggregated over N days
- `GET /response-times` — Daily p50/p95/p99 (TTFA) for last N days
- `GET /latency` — Percentiles for TTFB/TTFA (overall)
- `GET /tool-usage` — RAG tool usage (overall and by collection)
- `GET /collections-health` — Documents/webpages counts and freshness by collection

### Conversation Analytics (`/analytics/conversation`)
- `GET /summary` — Total conversations, avg turns, completion rate estimate
- `GET /flows` — Turn buckets with completion/abandonment and avg response time
- `GET /intents` — Heuristic intents inferred from messages and RAG usage
- `GET /document-retrieval` — Collection access and retrieval success
- `GET /drop-offs` — Common abandonment points and triggers
- `GET /sentiment-trends` — Positive/neutral/negative distribution over time
- `GET /knowledge-gaps` — Topics inferred from no‑answer triggers
- `GET /no-answer` — No‑answer rate, examples, and top triggers
- `GET /citations` — Citation coverage overall and per collection
- `GET /answer-length` — Word-count distribution and central tendencies

### Optional: Business Analytics (not enabled by default)

Endpoints exist in `analytics/routers/business_analytics.py` (ROI, containment, dashboards) but are not included in `main.py`. If you need them, include the router in the app and ensure required data sources are present.

## Setup

### Requirements

- Python 3.11+
  - `chats`, `chat_messages` (conversation data)
  - `documents`, `webpages` (RAG content health)
  - `message_ratings` (for explicit user ratings; optional)
  - `chat_events` (for latency/response-time metrics; required for some endpoints)

### Install (local)

From repo root:

1) Install dependencies
	- `pip install -r analytics/requirements.txt`

2) Configure environment
	- `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/govstackdb`

3) Run
	- `python -m analytics.main` (serves on `:8005`)

### Docker Compose

`docker-compose.yml` builds and runs this service:

- Service: `analytics` on port `8005` (mapped from `${ANALYTICS_PORT:-8005}`)
- Env: `DATABASE_URL` is set to point at the `postgres` service
- Healthcheck: `GET /analytics/health`

The optional `analytics-dashboard` (Next.js) expects `ANALYTICS_API_URL=http://analytics:8005`.

## Configuration

- `DATABASE_URL` (required): async DSN, e.g. `postgresql+asyncpg://postgres:postgres@localhost/govstackdb`
- CORS is open by default. Put the service behind your gateway in production.
- Port: `8005`

## Data and assumptions

Some endpoints compute metrics from tables that are not defined in this package but exist in the main app database:

- `chat_events`: used to derive latency and response-time trends
- `message_ratings`: used for explicit ratings and composite satisfaction

If these tables are missing, affected endpoints will fail. Ensure the main application migrations have been applied to the shared database.

## Testing

- Contract tests live in `analytics/tests` and use `httpx.ASGITransport`
- Run from repo root: `pytest analytics/tests -q`

See also: `analytics/README_TESTS.md`.

## Related docs

- Composite Sentiment API: `analytics/COMPOSITE_METRICS_API.md`
- Sentiment Analysis (VADER): `analytics/SENTIMENT_ANALYSIS.md`

## Security notes

- No auth is enforced in this microservice. Restrict network access and front it with the main API gateway for authentication/authorization.

## Version

- API: 1.0.0 (see `analytics/main.py`)
