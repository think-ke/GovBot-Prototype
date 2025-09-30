"""
Transcription tracking model for speech-to-text requests.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Transcription(Base):
    """Database model for tracking Groq speech-to-text transcriptions."""

    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    status = Column(String(32), nullable=False, default="queued", index=True)
    source_type = Column(String(50), nullable=False)  # upload | minio | url
    source_object = Column(String(512), nullable=True)
    file_name = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    language = Column(String(64), nullable=True)
    language_confidence = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=False, default="whisper-large-v3-turbo")
    transcription_text = Column(Text, nullable=True)
    segments = Column(JSON, nullable=True)
    usage = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    requested_by = Column(String(100), nullable=True, index=True)
    api_key_name = Column(String(100), nullable=True, index=True)
    meta_data = Column(JSON, nullable=True)
    prompt = Column(Text, nullable=True)
    temperature = Column(Float, nullable=True)
    response_format = Column(String(32), nullable=True)
    timestamp_granularities = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for API responses."""
        created_at = self.created_at.isoformat() if getattr(self, "created_at", None) else None
        updated_at = self.updated_at.isoformat() if getattr(self, "updated_at", None) else None
        completed_at = (
            self.completed_at.isoformat() if getattr(self, "completed_at", None) else None
        )

        return {
            "id": self.id,
            "request_id": self.request_id,
            "status": self.status,
            "source_type": self.source_type,
            "source_object": self.source_object,
            "file_name": self.file_name,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "duration_seconds": self.duration_seconds,
            "language": self.language,
            "language_confidence": self.language_confidence,
            "model_name": self.model_name,
            "transcription_text": self.transcription_text,
            "segments": self.segments,
            "usage": self.usage,
            "error_message": self.error_message,
            "requested_by": self.requested_by,
            "api_key_name": self.api_key_name,
            "metadata": self.meta_data,
            "prompt": self.prompt,
            "temperature": self.temperature,
            "response_format": self.response_format,
            "timestamp_granularities": self.timestamp_granularities,
            "created_at": created_at,
            "updated_at": updated_at,
            "completed_at": completed_at,
        }
