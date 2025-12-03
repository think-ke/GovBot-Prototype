import os
import sys
import asyncio
import json
from httpx import AsyncClient, ASGITransport

# Ensure repo root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from analytics.main import app  # noqa: E402

ENDPOINTS = [
    ("health", "/analytics/health"),
    ("conversation.drop_offs", "/analytics/conversation/drop-offs"),
    ("conversation.sentiment_trends", "/analytics/conversation/sentiment-trends"),
    ("conversation.knowledge_gaps", "/analytics/conversation/knowledge-gaps"),
    ("usage.errors", "/analytics/usage/errors"),
    ("usage.hourly_traffic", "/analytics/usage/hourly-traffic?days=7"),
    ("usage.response_times", "/analytics/usage/response-times?days=7"),
    ("usage.capacity", "/analytics/usage/capacity"),
    ("user.retention", "/analytics/user/retention"),
    ("conversation.intents", "/analytics/conversation/intents"),
    ("conversation.document_retrieval", "/analytics/conversation/document-retrieval"),
]

async def main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for name, path in ENDPOINTS:
            resp = await ac.get(path)
            print(f"\n=== {name} ({resp.status_code}) ===")
            try:
                data = resp.json()
                print(json.dumps(data, indent=2, sort_keys=True))
            except Exception as e:
                print(f"Error parsing JSON: {e}")
                print(resp.text)

if __name__ == "__main__":
    asyncio.run(main())
