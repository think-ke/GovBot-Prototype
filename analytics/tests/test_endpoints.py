import pytest
from httpx import AsyncClient, ASGITransport
from analytics.main import app

@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

# DB-dependent tests are intentionally excluded for now (e.g., conversation/summary)

@pytest.mark.asyncio
async def test_conversation_dropoffs_typed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/conversation/drop-offs")
        assert resp.status_code == 200
        data = resp.json()
        assert "drop_off_points" in data and isinstance(data["drop_off_points"], list)

@pytest.mark.asyncio
async def test_conversation_sentiment_trends_typed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/conversation/sentiment-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert "sentiment_distribution" in data

@pytest.mark.asyncio
async def test_conversation_knowledge_gaps_typed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/conversation/knowledge-gaps")
        assert resp.status_code == 200
        data = resp.json()
        assert "knowledge_gaps" in data
        # ensure percentage scale
        assert all(0 <= item["success_rate"] <= 100 for item in data["knowledge_gaps"]) 

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_usage_errors_typed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/usage/errors")
        assert resp.status_code == 200
        data = resp.json()
        assert set(["error_rate", "total_errors", "error_types", "analysis_period"]) <= set(data.keys())

@pytest.mark.asyncio
async def test_usage_hourly_traffic():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/usage/hourly-traffic?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list) and len(data) == 24
        assert set(["hour", "sessions", "messages"]) <= set(data[0].keys())

@pytest.mark.asyncio
async def test_usage_response_times():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/usage/response-times?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list) and len(data) == 7
        assert set(["day", "p50", "p95", "p99"]) <= set(data[0].keys())

@pytest.mark.asyncio
async def test_usage_capacity():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/usage/capacity")
        assert resp.status_code == 200
        data = resp.json()
        assert set(["current_load", "capacity_utilization", "concurrent_sessions", "scaling_status"]) <= set(data.keys())

@pytest.mark.asyncio
async def test_user_retention_typed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/analytics/user/retention")
        assert resp.status_code == 200
        data = resp.json()
        assert set(["day_1_retention", "day_7_retention", "day_30_retention"]) <= set(data.keys())

@pytest.mark.asyncio
async def test_conversation_intents_and_documents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.get("/analytics/conversation/intents")
        r2 = await ac.get("/analytics/conversation/document-retrieval")
        assert r1.status_code == 200 and r2.status_code == 200
        assert isinstance(r1.json(), list) and isinstance(r2.json(), list)
