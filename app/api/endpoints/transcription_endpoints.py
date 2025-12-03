"""Transcription REST endpoints for GovStack."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.db.models.transcription import Transcription
from app.core.asr.transcription_service import GroqTranscriptionService, TranscriptionError
from app.utils.security import (
    APIKeyInfo,
    require_read_permission,
    require_write_permission,
    log_audit_action,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcriptions", tags=["Transcriptions"])

_service_instance: Optional[GroqTranscriptionService] = None


def get_transcription_service() -> GroqTranscriptionService:
    global _service_instance
    if _service_instance is None:
        try:
            _service_instance = GroqTranscriptionService()
        except TranscriptionError as exc:  # pragma: no cover - configuration errors
            logger.error("Failed to initialize Groq transcription service: %s", exc)
            raise HTTPException(status_code=503, detail="Transcription service is not configured")
    return _service_instance


class TranscriptionResponse(BaseModel):
    """Response payload for a transcription resource."""

    id: int
    request_id: str
    status: str
    source_type: str
    source_object: Optional[str] = None
    file_name: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    duration_seconds: Optional[float] = None
    language: Optional[str] = None
    language_confidence: Optional[float] = None
    model_name: str
    transcription_text: Optional[str] = None
    segments: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    requested_by: Optional[str] = None
    api_key_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class TranscriptionListResponse(BaseModel):
    """Paginated list of transcriptions."""

    transcriptions: List[TranscriptionResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class TranscriptionCreateResponse(BaseModel):
    """Immediate response after creating a transcription."""

    transcription: TranscriptionResponse
    processing_started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


def _serialize_transcription(item: Transcription) -> TranscriptionResponse:
    data = item.to_dict()
    return TranscriptionResponse(**data)


@router.post("/", response_model=TranscriptionCreateResponse, status_code=202)
async def create_transcription(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to transcribe"),
    model: Optional[str] = Form(None, description="Optional Groq Whisper model override"),
    metadata: Optional[str] = Form(None, description="Optional JSON metadata to associate with the transcription"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission),
) -> TranscriptionCreateResponse:
    """Create a new transcription job."""
    service = get_transcription_service()

    try:
        payload_metadata: Optional[Dict[str, Any]] = json.loads(metadata) if metadata else None
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {exc}") from exc

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    requested_by = api_key_info.get_user_id()

    try:
        transcription = await service.transcribe_upload(
            session=db,
            file_bytes=file_bytes,
            filename=file.filename or "audio",
            content_type=file.content_type,
            requested_by=requested_by,
            api_key_name=api_key_info.name,
            metadata=payload_metadata,
            model=model,
        )
    except TranscriptionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    background_tasks.add_task(
        log_audit_action,
        user_id=requested_by,
        action="transcribe",
        resource_type="transcription",
        resource_id=str(transcription.id),
        details={"request_id": transcription.request_id, "status": transcription.status},
        request=request,
        api_key_name=api_key_info.name,
    )

    response_payload = TranscriptionResponse(**transcription.to_dict())
    return TranscriptionCreateResponse(transcription=response_payload)


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission),
) -> TranscriptionResponse:
    """Retrieve a single transcription record."""

    result = await db.execute(
        select(Transcription).where(Transcription.id == transcription_id)
    )
    transcription = result.scalar_one_or_none()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return _serialize_transcription(transcription)


@router.get("/", response_model=TranscriptionListResponse)
async def list_transcriptions(
    status: Optional[str] = Query(None, description="Filter by transcription status"),
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    api_key_name: Optional[str] = Query(None, description="Filter by API key name"),
    requested_by: Optional[str] = Query(None, description="Filter by requester identifier"),
    created_from: Optional[datetime] = Query(None, description="Start timestamp (inclusive)"),
    created_to: Optional[datetime] = Query(None, description="End timestamp (inclusive)"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission),
) -> TranscriptionListResponse:
    """List historical transcriptions with optional filtering."""

    query = select(Transcription)
    if status:
        query = query.where(Transcription.status == status)
    if model_name:
        query = query.where(Transcription.model_name == model_name)
    if api_key_name:
        query = query.where(Transcription.api_key_name == api_key_name)
    if requested_by:
        query = query.where(Transcription.requested_by == requested_by)
    if created_from:
        query = query.where(Transcription.created_at >= created_from)
    if created_to:
        query = query.where(Transcription.created_at <= created_to)

    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total_count = int(total_result.scalar_one())

    query = query.order_by(Transcription.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    response_items = [_serialize_transcription(item) for item in records]
    has_more = offset + limit < total_count

    return TranscriptionListResponse(
        transcriptions=response_items,
        total_count=total_count,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )
