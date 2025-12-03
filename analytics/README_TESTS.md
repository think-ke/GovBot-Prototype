# Analytics microservice tests

Uses pytest, pytest-asyncio, httpx>=0.28 with ASGITransport.
No database required for these contract tests; DB-dependent routes are excluded.

Run:
- From repo root: pytest analytics/tests -q