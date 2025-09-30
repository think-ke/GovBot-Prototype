import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, cast

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.api.fast_api_app import app
from app.api.endpoints.transcription_endpoints import get_transcription_service, _service_instance
from app.db.database import get_db
from app.db.models.transcription import Transcription

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:transcriptions_test?mode=memory&cache=shared"
ENGINE = create_async_engine(TEST_DATABASE_URL, connect_args={"uri": True})
SESSION_FACTORY = async_sessionmaker(ENGINE, expire_on_commit=False, class_=AsyncSession)


class FakeTranscriptionService:
    """Stub transcription service that avoids external Groq/minio calls."""

    async def transcribe_upload(
        self,
        *,
        session: AsyncSession,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str],
        requested_by: Optional[str],
        api_key_name: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Transcription:
        transcription = Transcription(
            status="completed",
            source_type="upload",
            file_name=filename,
            content_type=content_type,
            file_size=len(file_bytes),
            model_name=model or "whisper-large-v3-turbo",
            requested_by=requested_by,
            api_key_name=api_key_name,
            transcription_text="Test transcription output",
            language="en",
            duration_seconds=0.5,
            segments=[{"id": 0, "text": "Test transcription output"}],
            usage={"duration": 0.5},
            meta_data=metadata,
        )

        orm_transcription = cast(Any, transcription)
        orm_transcription.source_object = f"transcriptions/{transcription.request_id}/{filename}"
        orm_transcription.completed_at = datetime.now(timezone.utc)

        session.add(transcription)
        await session.commit()
        await session.refresh(transcription)
        return transcription


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with ENGINE.begin() as conn:
        await conn.run_sync(Transcription.metadata.create_all)
    yield
    async with ENGINE.begin() as conn:
        await conn.run_sync(Transcription.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        async with SESSION_FACTORY() as session:
            yield session

    fake_service = FakeTranscriptionService()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_transcription_service] = lambda: fake_service

    global _service_instance
    _service_instance = fake_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_transcription_service, None)
    _service_instance = None


@pytest.mark.asyncio
async def test_create_and_retrieve_transcription(client):
    metadata = {"label": "unit-test"}
    files = {"file": ("sample.mp3", b"fake audio bytes", "audio/mpeg")}
    data = {"metadata": json.dumps(metadata)}
    headers = {"X-API-Key": "gs-dev-master-key-12345"}

    create_response = await client.post("/transcriptions/", files=files, data=data, headers=headers)
    assert create_response.status_code == 202, create_response.text

    body = create_response.json()
    transcription_payload = body["transcription"]
    assert transcription_payload["status"] == "completed"
    assert transcription_payload["transcription_text"] == "Test transcription output"
    assert transcription_payload["metadata"]["label"] == "unit-test"

    transcription_id = transcription_payload["id"]

    detail_response = await client.get(f"/transcriptions/{transcription_id}", headers=headers)
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["id"] == transcription_id
    assert detail_data["request_id"] == transcription_payload["request_id"]

    list_response = await client.get("/transcriptions/", headers=headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total_count"] >= 1
    assert any(item["id"] == transcription_id for item in list_data["transcriptions"])