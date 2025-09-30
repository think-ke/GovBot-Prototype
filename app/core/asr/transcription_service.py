"""Groq-powered speech-to-text service for GovStack."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, cast

from dotenv import load_dotenv
from groq import Groq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.transcription import Transcription
from app.utils.storage import minio_client

logger = logging.getLogger(__name__)

# Ensure environment variables are loaded once the module is imported.
load_dotenv()

SUPPORTED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/x-flac",
    "audio/flac",
    "audio/aac",
    "audio/x-aac",
}

VALID_RESPONSE_FORMATS = {"json", "verbose_json", "text"}
VALID_TIMESTAMP_GRANULARITIES = {"word", "segment"}
DEFAULT_RESPONSE_FORMAT = "verbose_json"
DEFAULT_TEMPERATURE = 0.0
MAX_FILE_BYTES = int(os.getenv("GROQ_STT_MAX_FILE_BYTES", str(100 * 1024 * 1024)))


class TranscriptionError(Exception):
    """Raised when a transcription request cannot be completed."""


class GroqTranscriptionService:
    """Service responsible for orchestrating Groq speech-to-text calls and persistence."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        storage_prefix: str = "transcriptions",
        client: Optional[Groq] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.error("Missing GROQ_API_KEY environment variable")
            raise TranscriptionError("Groq API key is not configured")

        self.default_model = default_model or os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
        self.storage_prefix = storage_prefix.rstrip("/")
        self.client = client or Groq(api_key=self.api_key)

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
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[str] = None,
        timestamp_granularities: Optional[List[str]] = None,
    ) -> Transcription:
        """Transcribe an uploaded file and persist the result."""

        if content_type and content_type.lower() not in SUPPORTED_AUDIO_CONTENT_TYPES:
            logger.warning("Unsupported audio content type: %s", content_type)
            raise TranscriptionError(f"Unsupported audio content type: {content_type}")

        if file_bytes and len(file_bytes) > MAX_FILE_BYTES:
            raise TranscriptionError(
                f"Audio file exceeds maximum supported size of {MAX_FILE_BYTES // (1024 * 1024)} MB"
            )

        temperature_value = temperature if temperature is not None else DEFAULT_TEMPERATURE
        if not 0.0 <= temperature_value <= 1.0:
            raise TranscriptionError("Temperature must be between 0 and 1 inclusive")

        response_format_value = (response_format or DEFAULT_RESPONSE_FORMAT).lower()
        if response_format_value not in VALID_RESPONSE_FORMATS:
            raise TranscriptionError(
                f"Unsupported response_format '{response_format_value}'. Valid values: {', '.join(sorted(VALID_RESPONSE_FORMATS))}"
            )

        normalized_granularities: Optional[List[str]] = None
        if timestamp_granularities:
            candidate = [item.lower() for item in timestamp_granularities]
            invalid = [item for item in candidate if item not in VALID_TIMESTAMP_GRANULARITIES]
            if invalid:
                raise TranscriptionError(
                    f"Unsupported timestamp granularities: {', '.join(invalid)}. Allowed values: word, segment"
                )
            if response_format_value not in {"json", "verbose_json"}:
                raise TranscriptionError(
                    "timestamp_granularities requires response_format to be 'json' or 'verbose_json'"
                )
            normalized_granularities = candidate

        safe_filename = os.path.basename(filename) if filename else "audio"

        sanitized_metadata: Optional[Dict[str, Any]] = None
        if metadata:
            sanitized_metadata = dict(metadata)
        if filename and filename != safe_filename:
            sanitized_metadata = sanitized_metadata or {}
            sanitized_metadata.setdefault("original_filename", filename)

        # Create initial database record
        transcription = Transcription(
            status="queued",
            source_type="upload",
            file_name=safe_filename,
            content_type=content_type,
            file_size=len(file_bytes) if file_bytes else None,
            model_name=model or self.default_model,
            requested_by=requested_by,
            api_key_name=api_key_name,
            meta_data=sanitized_metadata,
            language=language,
            prompt=prompt,
            temperature=temperature_value,
            response_format=response_format_value,
            timestamp_granularities=normalized_granularities,
        )

        await self._persist(session, transcription)

        request_id_value = cast(str, transcription.request_id)
        object_name = f"{self.storage_prefix}/{request_id_value}/{safe_filename}"
        orm_transcription = cast(Any, transcription)
        orm_transcription.source_object = object_name
        orm_transcription.status = "processing"
        await self._persist(session, transcription)

        # Upload the audio to storage for auditing/replay
        try:
            minio_client.upload_file(
                BytesIO(file_bytes),
                object_name=object_name,
                content_type=content_type or "application/octet-stream",
                metadata={"request_id": request_id_value, "filename": safe_filename},
            )
        except Exception as exc:  # pragma: no cover - storage failures should not crash the flow
            logger.error("Failed to upload audio for transcription %s: %s", transcription.request_id, exc)

        # Perform transcription with Groq
        try:
            groq_response, raw_response = await self._invoke_groq(
                data=file_bytes,
                filename=safe_filename,
                model=model or self.default_model,
                language=language,
                prompt=prompt,
                temperature=temperature_value,
                response_format=response_format_value,
                timestamp_granularities=normalized_granularities,
            )
            logger.debug("Groq transcription response for %s: %s", transcription.request_id, raw_response)
        except Exception as exc:  # pragma: no cover - network errors hard to replicate in tests
            logger.exception("Groq transcription failed for %s", transcription.request_id)
            orm_transcription.status = "failed"
            orm_transcription.error_message = str(exc)
            orm_transcription.completed_at = datetime.now(timezone.utc)
            await self._persist(session, transcription)
            raise TranscriptionError("Groq transcription request failed") from exc

        # Update record with results
        orm_transcription.status = "completed"
        orm_transcription.transcription_text = groq_response.get("text")
        orm_transcription.language = groq_response.get("language")
        orm_transcription.duration_seconds = groq_response.get("duration")
        orm_transcription.language_confidence = groq_response.get("language_confidence")
        orm_transcription.segments = groq_response.get("segments")
        usage = (
            raw_response.get("usage")
            or groq_response.get("usage")
            or raw_response.get("x_groq", {}).get("usage")
        )
        orm_transcription.usage = usage
        orm_transcription.completed_at = datetime.now(timezone.utc)
        if metadata or raw_response:
            inherited = dict(metadata or {})
            inherited.setdefault("groq", raw_response)
            orm_transcription.meta_data = inherited

        await self._persist(session, transcription)
        return transcription

    async def _invoke_groq(
        self,
        *,
        data: bytes,
        filename: str,
        model: str,
        language: Optional[str],
        prompt: Optional[str],
        temperature: float,
        response_format: str,
        timestamp_granularities: Optional[List[str]],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Call Groq Whisper API in a thread and normalize the response."""

        def _call() -> Any:
            kwargs: Dict[str, Any] = {
                "file": (filename, data),
                "model": model,
                "response_format": response_format,
                "temperature": temperature,
            }
            if language:
                kwargs["language"] = language
            if prompt:
                kwargs["prompt"] = prompt
            if timestamp_granularities:
                kwargs["timestamp_granularities"] = timestamp_granularities
            return self.client.audio.transcriptions.create(**kwargs)

        response = await asyncio.to_thread(_call)

        raw_dict: Dict[str, Any]
        if hasattr(response, "model_dump"):
            raw_dict = response.model_dump()  # type: ignore[assignment]
        elif hasattr(response, "dict"):
            raw_dict = response.dict()  # type: ignore[assignment]
        elif hasattr(response, "to_dict"):
            raw_dict = response.to_dict()  # type: ignore[assignment]
        else:
            raw_dict = json.loads(str(response)) if response else {}

        normalized = {
            "text": getattr(response, "text", raw_dict.get("text")),
            "language": getattr(response, "language", raw_dict.get("language")),
            "duration": getattr(response, "duration", raw_dict.get("duration")),
            "segments": raw_dict.get("segments"),
            "usage": raw_dict.get("usage") or raw_dict.get("x_groq", {}).get("usage"),
            "language_confidence": raw_dict.get("language_confidence"),
        }

        return normalized, raw_dict

    async def _persist(self, session: AsyncSession, transcription: Transcription) -> None:
        """Persist changes to the database with basic error handling."""
        try:
            session.add(transcription)
            await session.commit()
            await session.refresh(transcription)
        except SQLAlchemyError as exc:  # pragma: no cover - DB failures should be rare
            await session.rollback()
            logger.exception("Database error while saving transcription %s", transcription.request_id)
            raise TranscriptionError("Failed to persist transcription state") from exc