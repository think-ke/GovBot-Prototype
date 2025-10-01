"""
FastAPI application for the GovStack service.
"""

from dotenv import load_dotenv
load_dotenv()


import os
import logging
import mimetypes
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, APIRouter, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import uvicorn
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Dict, Any, Union, cast
from contextlib import asynccontextmanager
from starlette.concurrency import run_in_threadpool

from app.utils.storage import minio_client
from app.db.models.document import Document, Base as DocumentBase
from app.db.models.webpage import Webpage, WebpageLink, Base as WebpageBase
from app.db.models.chat import Chat, ChatMessage, Base as ChatBase
from app.db.models.chat_event import ChatEvent, Base as ChatEventBase
from app.db.models.message_rating import MessageRating, Base as MessageRatingBase
from app.db.models.collection import Collection
from app.db.models.audit_log import AuditLog, Base as AuditBase
from app.core.crawlers.web_crawler import crawl_website
from app.core.crawlers.utils import get_page_as_markdown
from app.core.rag.indexer import (
    extract_text_batch,
    get_collection_stats,
    start_background_indexing,
    start_background_document_indexing,
    register_document_index_job,
    get_document_index_job,
    list_document_index_jobs,
)
from app.core.rag.vectorstore_admin import delete_embeddings_for_doc
from app.utils.security import add_api_key_to_docs, validate_api_key, require_read_permission, require_write_permission, require_delete_permission, APIKeyInfo, log_audit_action

import logfire

logfire.configure()

logfire.instrument_openai()
logfire.instrument()
logfire.instrument_httpx()
logfire.instrument_aiohttp_client()
logfire.instrument_system_metrics()
#logfire.instrument_asyncpg()
logfire.instrument_requests()


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Database configuration
from app.db.database import get_db, engine, async_session


def _get_file_extension(filename: Optional[str]) -> str:
    """Safely extract a file extension or return an empty string.

    Avoids None access and inconsistent checks.
    """
    if not filename:
        return ""
    try:
        return os.path.splitext(filename)[1] if "." in filename else ""
    except Exception:
        return ""


SUPPORTED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
}


def _validate_upload_extension(extension: str) -> None:
    """Validate that the provided file extension is supported."""
    if not extension or extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{extension or 'unknown'}'. Supported extensions: {supported}",
        )


def _resolve_content_type(filename: Optional[str], provided_content_type: Optional[str]) -> str:
    """Resolve the best-effort content type for an uploaded file."""
    if provided_content_type:
        return provided_content_type

    guessed_content_type, _ = mimetypes.guess_type(filename or "")
    return guessed_content_type or "application/octet-stream"


async def _ensure_upload_ready(upload_file: UploadFile) -> int:
    """Validate the uploaded file has content and return its size without buffering it in memory."""
    await run_in_threadpool(upload_file.file.seek, 0, os.SEEK_END)
    file_size = await run_in_threadpool(upload_file.file.tell)
    await run_in_threadpool(upload_file.file.seek, 0)

    if file_size <= 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return file_size

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting up GovStack API")
    async with engine.begin() as conn:
        # In production, rely on Alembic migrations instead of create_all.
        # Enable this only for local dev bootstrapping by setting DB_AUTO_CREATE=true
        if os.getenv("DB_AUTO_CREATE", "false").lower() == "true":
            await conn.run_sync(DocumentBase.metadata.create_all)
            await conn.run_sync(WebpageBase.metadata.create_all)
            await conn.run_sync(ChatBase.metadata.create_all)
            await conn.run_sync(ChatEventBase.metadata.create_all)
            await conn.run_sync(AuditBase.metadata.create_all)
    yield
    # Shutdown logic
    logger.info("Shutting down GovStack API")

# Initialize FastAPI app
app = FastAPI(
    title="GovStack API",
    description="GovStack Document Management API with API Key Authentication",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Core",
            "description": "Core API endpoints for health checks and basic operations",
        },
        {
            "name": "Chat", 
            "description": "AI-powered chat and conversation endpoints",
        },
        {
            "name": "Documents",
            "description": "Document upload, retrieval, and management",
        },
        {
            "name": "Web Crawler",
            "description": "Website crawling and content extraction",
        },
        {
            "name": "Webpages",
            "description": "Webpage data retrieval and management",
        },
        {
            "name": "Collections",
            "description": "Collection statistics and management",
        },
        {
            "name": "Audit",
            "description": "Audit trail and activity logging",
        },
    ]
)

# Add API key security scheme to OpenAPI
app.openapi_components = {
    "securitySchemes": add_api_key_to_docs()
}

# Global security requirement
app.openapi_security = [{"ApiKeyAuth": []}]

# Configure CORS
# Note: When allow_credentials=True, browsers do not allow wildcard "*" for Access-Control-Allow-Origin.
# Use explicit origins via CORS_ALLOW_ORIGINS env (comma-separated) or sensible defaults for dev + production dashboards.
cors_env = os.getenv("CORS_ALLOW_ORIGINS", "")
if cors_env.strip():
    allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
else:
    allowed_origins = [
        # Local dev
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Production dashboards
        "https://govstack-dashboard.vercel.app",
    ]

# Allow CORS from all origins while supporting credentials by echoing the Origin header (regex match)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

logfire.instrument_fastapi(app, capture_headers=True)

# Database dependency
# Using get_db from app.db.database

# Create APIRouters for different endpoint categories
core_router = APIRouter(
    prefix="",
    tags=["Core"],
    responses={404: {"description": "Not found"}},
)

# chat_router removed as we use the persistent_chat_router directly

document_router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    responses={404: {"description": "Not found"}},
)

crawler_router = APIRouter(
    prefix="/crawl",
    tags=["Web Crawler"],
    responses={404: {"description": "Not found"}},
)

webpage_router = APIRouter(
    prefix="/webpages",
    tags=["Webpages"],
    responses={404: {"description": "Not found"}},
)

collection_router = APIRouter(
    prefix="/collection-stats",
    tags=["Collections"],
    responses={404: {"description": "Not found"}},
)

# Core endpoints
@core_router.get("/")
async def root():
    """Root endpoint - Public access for basic connectivity testing."""
    return {"message": "Welcome to GovStack API", "version": "0.1.0", "authentication": "X-API-Key header required for most endpoints"}

@core_router.get("/health")
async def health():
    """Health check endpoint - Public access for monitoring."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@core_router.get("/api-info")
async def api_info(api_key_info: APIKeyInfo = Depends(validate_api_key)):
    """Get API key information and permissions."""
    return {
        "api_key_name": api_key_info.name,
        "permissions": api_key_info.permissions,
        "description": api_key_info.description
    }

# Document endpoints - Updated with security
@document_router.post("/", status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    description: str = Form(None),
    is_public: bool = Form(False),
    collection_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
):
    """
    Upload a document to MinIO storage and save its metadata in the database.
    Requires write permission.
    
    Args:
        file: The file to upload
        description: Optional description of the document
        is_public: Whether the document should be publicly accessible
        collection_id: Required identifier for grouping documents
        db: Database session
        request: Request object for audit logging
        
    Returns:
        Document metadata with access URL
    """
    try:
        normalized_collection_id = (collection_id or "").strip()
        if not normalized_collection_id:
            raise HTTPException(status_code=400, detail="collection_id is required.")

        original_filename = file.filename or ""
        file_extension = _get_file_extension(original_filename).lower()
        _validate_upload_extension(file_extension)

        file_size = await _ensure_upload_ready(file)
        content_type = _resolve_content_type(original_filename, file.content_type)

        object_name = f"{uuid.uuid4()}{file_extension}"
        minio_metadata = {"collection_id": normalized_collection_id}

        minio_client.upload_file(
            file_obj=file.file,
            object_name=object_name,
            content_type=content_type,
            metadata=minio_metadata,
        )

        await file.close()

        document = Document(
            filename=original_filename or object_name,
            object_name=object_name,
            content_type=content_type,
            size=file_size,
            description=description,
            is_public=is_public,
            meta_data={"original_filename": original_filename or object_name},
            collection_id=normalized_collection_id,
            created_by=api_key_info.get_user_id(),
            api_key_name=api_key_info.name,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Log audit action
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="upload",
            resource_type="document",
            resource_id=str(document.id),
            details={
                "filename": file.filename,
                "size": file_size,
                "collection_id": collection_id,
                "is_public": is_public
            },
            request=request,
            api_key_name=api_key_info.name
        )
        
        document_id_value = cast(Optional[int], document.id)
        index_job_id = register_document_index_job(
            normalized_collection_id,
            document_ids=[document_id_value] if document_id_value is not None else None,
        )
        background_tasks.add_task(
            start_background_document_indexing,
            normalized_collection_id,
            index_job_id,
        )

        # Generate access URL
        access_url = minio_client.get_presigned_url(object_name)

        # Return metadata with URL and background job ID to poll progress
        result = document.to_dict()
        result["access_url"] = access_url
        result["index_job_id"] = index_job_id

        return result
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@document_router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get document metadata and generate a presigned URL for access.
    Requires read permission.
    
    Args:
        document_id: ID of the document to retrieve
        db: Database session
        
    Returns:
        Document metadata with access URL
    """
    try:
        # Get document from database
        result = await db.get(Document, document_id)
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update last accessed timestamp
        result.last_accessed = timezone.utc
        await db.commit()
        
        # Generate access URL
        access_url = minio_client.get_presigned_url(result.object_name)
        
        # Return metadata with URL
        response = result.to_dict()
        response["access_url"] = access_url
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@document_router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    List documents with pagination.
    Requires read permission.
    
    Args:
        skip: Number of documents to skip (for pagination)
        limit: Maximum number of documents to return
        db: Database session
        
    Returns:
        List of document metadata
    """
    try:
        from sqlalchemy import select
        
        # Query documents with pagination
        query = select(Document).offset(skip).limit(limit)
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Convert to dict representation
        return [doc.to_dict() for doc in documents]
    
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@document_router.get("/collection/{collection_id}")
async def list_documents_by_collection(
    collection_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    List documents in a specific collection with pagination.
    Requires read permission.
    
    Args:
        collection_id: The collection ID to filter by
        skip: Number of documents to skip (for pagination)
        limit: Maximum number of documents to return
        db: Database session
        
    Returns:
        List of document metadata for the specified collection
    """
    try:
        from sqlalchemy import select
        
        # Query documents by collection with pagination
        query = select(Document).where(Document.collection_id == collection_id).offset(skip).limit(limit)
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Convert to dict representation
        return [doc.to_dict() for doc in documents]
    
    except Exception as e:
        logger.error(f"Error listing documents for collection {collection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents for collection: {str(e)}")

@document_router.put("/{document_id}", 
                    summary="Update document",
                    description="Update document metadata and optionally replace the file. File replacement triggers vector cleanup and reindexing.",
                    responses={
                        200: {"description": "Document updated successfully"},
                        404: {"description": "Document not found"},
                        403: {"description": "Insufficient permissions"},
                        500: {"description": "Internal server error"}
                    })
async def update_document(
    document_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None),
    is_public: Optional[bool] = Form(None),
    collection_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
):
    """
    Update a document's metadata and optionally replace the file.
    
    **Parameters:**
    - **document_id**: ID of the document to update
    - **file**: New file to replace existing document (optional)  
    - **description**: Updated description text (optional)
    - **is_public**: Updated visibility flag (optional)
    - **collection_id**: Collection ID to move document to (optional)
    
    **Side Effects:**
    - If `file` provided: uploads new file, deletes old file, clears vector embeddings by doc_id, sets `is_indexed=false`, triggers background reindexing
    - If `collection_id` changes: deletes vectors from old collection, sets `is_indexed=false`, triggers reindexing in new collection
    - Creates audit log entry
    
    **Permissions:** Requires `write` permission
    
    **Returns:** Updated document metadata with indexing status
    """
    try:
        index_job_id: Optional[str] = None
        doc = await db.get(Document, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        changes: Dict[str, Any] = {}

        # Handle file replacement
        if file is not None:
            import uuid

            safe_name = file.filename or ""
            file_extension = _get_file_extension(safe_name).lower()
            _validate_upload_extension(file_extension)

            target_collection_id = (
                (collection_id if collection_id is not None else doc.collection_id) or ""
            )
            target_collection_id = str(target_collection_id).strip()

            file_size = await _ensure_upload_ready(file)
            content_type = _resolve_content_type(safe_name, file.content_type)

            new_object_name = f"{uuid.uuid4()}{file_extension}"

            minio_client.upload_file(
                file_obj=file.file,
                object_name=new_object_name,
                content_type=content_type,
                metadata={"collection_id": target_collection_id} if target_collection_id else None,
            )
            await file.close()
            # remove old object
            try:
                if doc.object_name:  # type: ignore[attr-defined]
                    minio_client.delete_file(str(doc.object_name))
            except Exception as ve:
                logger.warning(f"Failed to delete old object for doc {document_id}: {ve}")
            # update doc fields
            doc.object_name = new_object_name
            doc.filename = safe_name or new_object_name
            doc.content_type = content_type
            doc.size = file_size
            doc.is_indexed = False
            doc.indexed_at = None
            changes["file_replaced"] = True
            # delete any existing embeddings for this document in its current collection
            try:
                if doc.collection_id is not None:
                    delete_embeddings_for_doc(collection_id=str(doc.collection_id), doc_id=str(document_id))
            except Exception as ve:
                logger.warning(f"Failed to delete embeddings for doc {document_id} on replace: {ve}")

        # Metadata updates
        if description is not None and description != doc.description:
            changes["description"] = {"old": doc.description, "new": description}
            doc.description = description
        if is_public is not None and is_public != doc.is_public:
            changes["is_public"] = {"old": doc.is_public, "new": is_public}
            doc.is_public = bool(is_public)
        collection_changed = False
        old_cid: Optional[str] = None
        if collection_id is not None:
            normalized_collection = collection_id.strip()
            current_collection = cast(Optional[str], doc.collection_id) or ""
            if normalized_collection != current_collection:
                collection_changed = True
                old_cid = current_collection or None
                changes["collection_id"] = {"old": doc.collection_id, "new": normalized_collection}
                doc.collection_id = normalized_collection
        if collection_changed:
            # collection change implies reindex and cleanup old vectors
            doc.is_indexed = False
            doc.indexed_at = None
            if old_cid:
                try:
                    delete_embeddings_for_doc(collection_id=old_cid, doc_id=str(document_id))
                except Exception as ve:
                    logger.warning(f"Failed to delete embeddings for doc {document_id} in old collection {old_cid}: {ve}")

        doc.updated_by = api_key_info.get_user_id()

        await db.commit()
        await db.refresh(doc)

        # Audit log
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="update",
            resource_type="document",
            resource_id=str(document_id),
            details={"changes": changes},
            request=request,
            api_key_name=api_key_info.name,
        )

        # trigger background reindex if needed
        try:
            raw_collection_id = cast(Optional[str], doc.collection_id)
            collection_for_job = raw_collection_id.strip() if raw_collection_id else ""
            if ("file_replaced" in changes or "collection_id" in changes) and collection_for_job:
                if background_tasks is not None:
                    index_job_id = register_document_index_job(
                        collection_for_job,
                        document_ids=[cast(int, doc.id)] if doc.id is not None else None,
                    )
                    background_tasks.add_task(
                        start_background_document_indexing,
                        collection_for_job,
                        index_job_id,
                    )
        except Exception as ve:
            logger.warning(f"Failed to schedule background reindex for doc {document_id}: {ve}")

        response_payload = doc.to_dict()
        if index_job_id:
            response_payload["index_job_id"] = index_job_id
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@document_router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_delete_permission)
):
    """
    Delete a document from both MinIO storage and the database.
    Requires delete permission.
    
    Args:
        document_id: ID of the document to delete
        db: Database session
        request: Request object for audit logging
        
    Returns:
        Confirmation message
    """
    try:
        # Get document from database
        document = await db.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Store document info for audit log
        document_info = {
            "filename": document.filename,
            "collection_id": document.collection_id,
            "size": document.size
        }
        
        # Delete embeddings from Chroma by metadata doc_id in the collection
        try:
            if document.collection_id:
                delete_embeddings_for_doc(collection_id=document.collection_id, doc_id=str(document_id))
        except Exception as ve:
            logger.warning(f"Failed to delete vectors for doc {document_id}: {ve}")

        # Delete from MinIO
        object_name = document.object_name
        minio_client.delete_file(object_name)
        
        # Delete from database
        await db.delete(document)
        await db.commit()
        
        # Log audit action
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="delete",
            resource_type="document",
            resource_id=str(document_id),
            details=document_info,
            request=request,
            api_key_name=api_key_info.name
        )
        
        return {"message": f"Document {document_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# Collection Management Models
class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: str = Field(default="mixed", pattern="^(documents|webpages|mixed)$")

class UpdateCollectionRequest(BaseModel):
    """Request model for updating a collection."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: Optional[str] = Field(None, pattern="^(documents|webpages|mixed)$")

class CollectionResponse(BaseModel):
    """Response model for collection data."""
    id: str
    name: str
    description: Optional[str] = None
    type: str
    created_at: str
    updated_at: str
    document_count: int
    webpage_count: int


class BulkCreateCollectionItem(CreateCollectionRequest):
    """Single collection definition for bulk creation."""


class BulkCreateCollectionsRequest(BaseModel):
    """Request body for creating multiple collections in one call."""
    collections: List[BulkCreateCollectionItem]

    @validator("collections")
    def validate_collections(cls, value: List[BulkCreateCollectionItem]) -> List[BulkCreateCollectionItem]:
        if not value:
            raise ValueError("At least one collection must be provided")
        if len(value) > 100:
            raise ValueError("A maximum of 100 collections can be created per request")
        return value

# Web Crawler API Models
class CrawlWebsiteRequest(BaseModel):
    """Request model for crawling a website."""
    url: HttpUrl
    depth: int = Field(default=3, ge=1, le=10)
    concurrent_requests: int = Field(default=10, ge=1, le=50)
    follow_external: bool = Field(default=False)
    strategy: str = Field(default="breadth_first", pattern="^(breadth_first|depth_first)$")
    collection_id: str = Field(..., description="Required identifier for grouping crawl jobs")
    
class WebpageResponse(BaseModel):
    """Response model for webpage data."""
    id: int
    url: str
    title: Optional[str] = None
    crawl_depth: int
    last_crawled: Optional[str] = None
    status_code: Optional[int] = None
    collection_id: str
    
class DocumentIndexingStatusResponse(BaseModel):
    """Response model for document indexing status."""
    collection_id: str
    documents_total: int
    indexed: int
    unindexed: int
    progress_percent: float


class DocumentIndexJobStatus(BaseModel):
    """Response model for background document indexing job status."""
    job_id: str
    collection_id: str
    status: str
    documents_total: int = 0
    documents_processed: int = 0
    documents_indexed: int = 0
    progress_percent: float = 0.0
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    updated_at: Optional[str] = None

class IndexingBreakdown(BaseModel):
    """Indexing breakdown for a specific content type."""
    total: int
    indexed: int
    unindexed: int

class CollectionIndexingStatusResponse(BaseModel):
    """Response model for combined collection indexing status."""
    collection_id: str
    documents: IndexingBreakdown
    webpages: IndexingBreakdown
    combined: Dict[str, Any]  # Contains total, indexed, unindexed, progress_percent

class WebpageLinkResponse(BaseModel):
    """Response model for webpage link data."""
    source_url: str
    target_url: str
    text: Optional[str] = None
    rel: Optional[str] = None

class FetchWebpageRequest(BaseModel):
    """Request model for fetching a webpage as markdown."""
    url: HttpUrl
    skip_ssl_verification: bool = Field(default=False)
    
class WebpageFetchResponse(BaseModel):
    """Response model for fetched webpage content."""
    url: str
    content: str
    title: Optional[str] = None
    
class CrawlStatusResponse(BaseModel):
    """Response model for crawl operation status."""
    task_id: str
    status: str
    seed_urls: List[str]
    urls_crawled: Optional[int] = None
    total_urls_queued: Optional[int] = None
    errors: Optional[int] = None
    start_time: Optional[str] = None
    finished: bool = False
    collection_id: Optional[str] = None

class CollectionTextRequest(BaseModel):
    """Request model for extracting texts from a collection."""
    collection_id: str
    hours_ago: Optional[int] = 24
    output_format: str = Field(default="text", pattern="^(text|json|markdown)$")

# Collections are now persisted in the database via the Collection model

# In-memory storage for background task status
crawl_tasks = {}

# Web Crawler Endpoints
@crawler_router.post("/", response_model=CrawlStatusResponse)
async def start_crawl(
    request_data: CrawlWebsiteRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
):
    """
    Start a website crawl operation in the background.
    Requires write permission.
    
    Args:
        request_data: Crawl configuration
        background_tasks: Background task manager
        db: Database session
        request: Request object for audit logging
        
    Returns:
        Initial crawl status including task ID
    """
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        # Initialize task status
        crawl_tasks[task_id] = {
            "status": "starting",
            "seed_urls": [str(request_data.url)],
            "start_time": datetime.now(timezone.utc).isoformat(),
            "urls_crawled": 0,
            "total_urls_queued": 1,
            "errors": 0,
            "finished": False,
            "collection_id": request_data.collection_id,
            "user_id": api_key_info.get_user_id(),
            "api_key_name": api_key_info.name,
        }
        
        # Log audit action for crawl start
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="crawl_start",
            resource_type="webpage",
            resource_id=task_id,
            details={
                "url": str(request_data.url),
                "depth": request_data.depth,
                "collection_id": request_data.collection_id,
                "strategy": request_data.strategy
            },
            request=request,
            api_key_name=api_key_info.name
        )
        
        # Define the background task function
        async def background_crawl():
            try:
                # Update status to running
                crawl_tasks[task_id]["status"] = "running"
                # Start the crawl operation                
                result = await crawl_website(
                    seed_url=str(request_data.url),
                    depth=request_data.depth,
                    concurrent_requests=request_data.concurrent_requests,
                    follow_external=request_data.follow_external,
                    strategy=request_data.strategy,
                    collection_id=request_data.collection_id,
                    session_maker=async_session,
                    task_status=crawl_tasks[task_id],
                    user_id=api_key_info.get_user_id(),  # Pass user ID for audit trail
                    api_key_name=api_key_info.name  # Pass API key name for audit trail
                )
                # Update task status on completion
                crawl_tasks[task_id].update({
                    "status": "completed",
                    "urls_crawled": result.get("urls_crawled", 0),
                    "errors": result.get("errors", 0),
                    "finished": True
                })
                
                # Log audit action for crawl completion
                await log_audit_action(
                    user_id=api_key_info.get_user_id(),
                    action="crawl_complete",
                    resource_type="webpage",
                    resource_id=task_id,
                    details={
                        "urls_crawled": result.get("urls_crawled", 0),
                        "errors": result.get("errors", 0),
                        "collection_id": request_data.collection_id
                    },
                    api_key_name=api_key_info.name
                )
                
                # Start background indexing for the collection
                logger.info(f"Crawl completed, starting background indexing for collection '{request_data.collection_id}'")
                start_background_indexing(request_data.collection_id)
                
            except Exception as e:
                logger.error(f"Error in background crawl task: {str(e)}")
                crawl_tasks[task_id].update({
                    "status": "failed",
                    "error_message": str(e),
                    "finished": True
                })
                
                # Log audit action for crawl failure
                await log_audit_action(
                    user_id=api_key_info.get_user_id(),
                    action="crawl_failed",
                    resource_type="webpage",
                    resource_id=task_id,
                    details={
                        "error": str(e),
                        "collection_id": request_data.collection_id
                    },
                    api_key_name=api_key_info.name
                )
        
        # Add the crawl task to background tasks
        background_tasks.add_task(background_crawl)
        
        # Return initial status
        return CrawlStatusResponse(
            task_id=task_id,
            status=crawl_tasks[task_id]["status"],
            seed_urls=crawl_tasks[task_id]["seed_urls"],
            start_time=crawl_tasks[task_id]["start_time"],
            finished=False,
            collection_id=request_data.collection_id
        )
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting crawl: {str(e)}")

@crawler_router.get("/{task_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(
    task_id: str,
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get the status of a crawl operation.
    Requires read permission.
    
    Args:
        task_id: ID of the crawl task
        
    Returns:
        Current crawl status
    """
    if task_id not in crawl_tasks:
        raise HTTPException(status_code=404, detail="Crawl task not found")
    
    task_status = crawl_tasks[task_id]
    
    # Clean up very old completed tasks
    current_time = datetime.now(timezone.utc)
    for tid, status in list(crawl_tasks.items()):
        if status.get("finished", False) and status.get("start_time"):
            start_time = datetime.fromisoformat(status["start_time"]) 
            if (current_time - start_time) > timedelta(hours=24):
                # Remove task status after 24 hours
                if tid != task_id:  # Don't remove the current task
                    crawl_tasks.pop(tid, None)
    
    return CrawlStatusResponse(
        task_id=task_id,
        status=task_status.get("status", "unknown"),
        seed_urls=task_status.get("seed_urls", []),
        urls_crawled=task_status.get("urls_crawled"),
        total_urls_queued=task_status.get("total_urls_queued"),
        errors=task_status.get("errors"),
        start_time=task_status.get("start_time"),
        finished=task_status.get("finished", False),
        collection_id=task_status.get("collection_id")
    )

@crawler_router.get("/", response_model=List[CrawlStatusResponse])
async def list_crawl_jobs(
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    List all crawl jobs with their statuses.
    Requires read permission.

    Returns:
        A list of crawl job statuses.
    """
    try:
        # Build response objects for all known tasks
        responses: List[CrawlStatusResponse] = []
        for tid, status in crawl_tasks.items():
            responses.append(CrawlStatusResponse(
                task_id=tid,
                status=status.get("status", "unknown"),
                seed_urls=status.get("seed_urls", []),
                urls_crawled=status.get("urls_crawled"),
                total_urls_queued=status.get("total_urls_queued"),
                errors=status.get("errors"),
                start_time=status.get("start_time"),
                finished=status.get("finished", False),
                collection_id=status.get("collection_id")
            ))

        # Optionally, sort by start_time descending when available
        def sort_key(item: CrawlStatusResponse):
            return item.start_time or ""

        responses.sort(key=sort_key, reverse=True)
        return responses
    except Exception as e:
        logger.error(f"Error listing crawl jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing crawl jobs: {str(e)}")

@webpage_router.post("/fetch-webpage/", response_model=WebpageFetchResponse)
async def fetch_webpage(
    request: FetchWebpageRequest,
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Fetch a single webpage and convert it to markdown.
    Requires read permission.
    
    Args:
        request: Webpage fetch configuration
        
    Returns:
        Webpage content as markdown
    """
    try:
        url = str(request.url)
        
        # Fetch the page as markdown
        content, title = await get_page_as_markdown(
            url=url, 
            skip_ssl_verification=request.skip_ssl_verification
        )
        
        return WebpageFetchResponse(
            url=url,
            content=content,
            title=title
        )
        
    except Exception as e:
        logger.error(f"Error fetching webpage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching webpage: {str(e)}")

@webpage_router.get("/", response_model=List[WebpageResponse])
async def list_webpages(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    List webpages with pagination.
    Requires read permission.
    
    Args:
        skip: Number of webpages to skip (for pagination)
        limit: Maximum number of webpages to return
        db: Database session
        
    Returns:
        List of webpage data
    """
    try:
        query = select(Webpage).offset(skip).limit(limit)
        result = await db.execute(query)
        webpages = result.scalars().all()
        return [
            WebpageResponse(
                id=wp.id,
                url=wp.url,
                title=wp.title,
                crawl_depth=wp.crawl_depth,
                last_crawled=wp.last_crawled.isoformat() if wp.last_crawled else None,
                status_code=wp.status_code,
                collection_id=wp.collection_id
            ) 
            for wp in webpages
        ]
        
    except Exception as e:
        logger.error(f"Error listing webpages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing webpages: {str(e)}")

@webpage_router.get("/{webpage_id}", response_model=Dict[str, Any])
async def get_webpage(
    webpage_id: int,
    include_content: bool = True,
    include_links: bool = False,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get webpage details with optional content and links.
    Requires read permission.
    
    Args:
        webpage_id: ID of the webpage to retrieve
        include_content: Whether to include the markdown content
        include_links: Whether to include incoming and outgoing links
        db: Database session
        
    Returns:
        Webpage data with optional content and links
    """
    try:
        # Get webpage from database
        webpage = await db.get(Webpage, webpage_id)
        if not webpage:
            raise HTTPException(status_code=404, detail="Webpage not found")
        
        # Convert to dictionary
        result = webpage.to_dict()
        
        # Remove content if not requested
        if not include_content:
            result.pop('content_markdown', None)
        
        # Add links if requested
        if include_links:
            # Get outgoing links
            outgoing_query = select(WebpageLink).filter(WebpageLink.source_id == webpage_id)
            outgoing_result = await db.execute(outgoing_query)
            outgoing_links = outgoing_result.scalars().all()
            
            # Get incoming links
            incoming_query = select(WebpageLink).filter(WebpageLink.target_id == webpage_id)
            incoming_result = await db.execute(incoming_query)
            incoming_links = incoming_result.scalars().all()
            
            # Add to result
            result['outgoing_links'] = [link.to_dict() for link in outgoing_links]
            result['incoming_links'] = [link.to_dict() for link in incoming_links]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving webpage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving webpage: {str(e)}")

@webpage_router.get("/collection/{collection_id}", response_model=List[WebpageResponse])
async def get_webpages_by_collection(
    collection_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get all webpages in a specific collection.
    Requires read permission.
    
    Args:
        collection_id: The collection ID to filter by
        limit: Maximum number of results to return
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List of webpages in the collection
    """
    try:
        query = select(Webpage).where(Webpage.collection_id == collection_id).limit(limit).offset(offset)
        result = await db.execute(query)
        webpages = result.scalars().all()
        
        return [WebpageResponse(
            id=webpage.id,
            url=webpage.url,
            title=webpage.title,
            crawl_depth=webpage.crawl_depth,
            last_crawled=webpage.last_crawled.isoformat() if webpage.last_crawled else None,
            status_code=webpage.status_code,
            collection_id=webpage.collection_id
        ) for webpage in webpages]
    except Exception as e:
        logger.error(f"Error fetching webpages by collection: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching webpages: {str(e)}")

@webpage_router.get("/by-url/", response_model=WebpageResponse)
async def get_webpage_by_url(
    url: str = Query(..., description="The URL of the webpage to fetch"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get a webpage by its URL.
    Requires read permission.
    
    Args:
        url: The URL of the webpage to fetch
        db: Database session
        
    Returns:
        Webpage data
    """
    try:
        query = select(Webpage).where(Webpage.url == url)
        result = await db.execute(query)
        webpage = result.scalars().first()
        
        if not webpage:
            raise HTTPException(status_code=404, detail="Webpage not found")
        
        return WebpageResponse(
            id=webpage.id,
            url=webpage.url,
            title=webpage.title,
            crawl_depth=webpage.crawl_depth,
            last_crawled=webpage.last_crawled.isoformat() if webpage.last_crawled else None,
            status_code=webpage.status_code,
            collection_id=webpage.collection_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching webpage by URL: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching webpage: {str(e)}")

@webpage_router.post("/extract-texts/", response_model=Union[str, List[Dict[str, Any]]])
async def extract_texts_from_collection(
    request: CollectionTextRequest,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Extract text content from webpages in a specific collection.
    Requires read permission.
    
    Args:
        request: Extraction configuration
        db: Database session
        
    Returns:
        Extracted text content in the requested format
    """
    try:
        texts = await extract_text_batch(
            db=db,
            collection_id=request.collection_id,
            hours_ago=request.hours_ago,
            output_format=request.output_format
        )
        return texts
    except Exception as e:
        logger.error(f"Error extracting texts: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting texts: {str(e)}")

@webpage_router.delete("/{webpage_id}",
                      summary="Delete webpage",
                      description="Delete a crawled webpage and its vector embeddings from ChromaDB",
                      responses={
                          200: {"description": "Webpage deleted successfully"},
                          404: {"description": "Webpage not found"},
                          403: {"description": "Insufficient permissions"},
                          500: {"description": "Internal server error"}
                      })
async def delete_webpage(
    webpage_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_delete_permission)
):
    """
    Delete a crawled webpage and its embeddings from ChromaDB.
    
    **Parameters:**
    - **webpage_id**: ID of the webpage to delete
    
    **Side Effects:**
    - Deletes vector embeddings by doc_id from ChromaDB
    - Removes database record
    - Creates audit log entry
    
    **Permissions:** Requires `delete` permission
    
    **Returns:** Confirmation message
    """
    try:
        page = await db.get(Webpage, webpage_id)
        if not page:
            raise HTTPException(status_code=404, detail="Webpage not found")

        info = {"url": page.url, "collection_id": page.collection_id}

        # Delete vectors using doc_id = webpage_id
        try:
            coll_id = str(page.collection_id) if page.collection_id is not None else None
            if coll_id:
                from app.core.rag.vectorstore_admin import delete_embeddings_for_doc
                delete_embeddings_for_doc(collection_id=coll_id, doc_id=str(webpage_id))
        except Exception as ve:
            logger.warning(f"Failed to delete vectors for webpage {webpage_id}: {ve}")

        # Delete DB row
        await db.delete(page)
        await db.commit()

        # Audit log
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="delete",
            resource_type="webpage",
            resource_id=str(webpage_id),
            details=info,
            request=request,
            api_key_name=api_key_info.name,
        )

        return {"message": f"Webpage {webpage_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webpage: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting webpage: {str(e)}")

@webpage_router.post("/{webpage_id}/recrawl",
                     summary="Recrawl webpage",
                     description="Mark a webpage for recrawling and reprocessing by resetting indexing flags",
                     responses={
                         200: {"description": "Webpage marked for recrawl successfully"},
                         404: {"description": "Webpage not found"},
                         403: {"description": "Insufficient permissions"},
                         500: {"description": "Internal server error"}
                     })
async def recrawl_webpage(
    webpage_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
):
    """
    Mark a webpage for recrawling and reprocessing.
    
    **Parameters:**
    - **webpage_id**: ID of the webpage to recrawl
    
    **Side Effects:**
    - Sets `is_indexed=false` and `indexed_at=null`
    - Page will be reprocessed in next indexing cycle
    - Creates audit log entry
    
    **Permissions:** Requires `write` permission
    
    **Returns:** Confirmation message with webpage ID
    """
    try:
        page = await db.get(Webpage, webpage_id)
        if not page:
            raise HTTPException(status_code=404, detail="Webpage not found")

        page.is_indexed = False
        page.indexed_at = None
        await db.commit()
        await db.refresh(page)

        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="update",
            resource_type="webpage",
            resource_id=str(webpage_id),
            details={"recrawl": True},
            request=request,
            api_key_name=api_key_info.name,
        )

        return {"message": f"Webpage {webpage_id} marked for recrawl"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking webpage for recrawl: {e}")
        raise HTTPException(status_code=500, detail=f"Error marking webpage for recrawl: {str(e)}")

# Indexing progress endpoints
@document_router.get("/indexing-status", 
                    response_model=Dict[str, Any],
                    summary="Get document indexing status",
                    description="Get indexing progress for uploaded documents in a specific collection",
                    responses={
                        200: {"description": "Indexing status retrieved successfully"},
                        403: {"description": "Insufficient permissions"},
                        500: {"description": "Internal server error"}
                    })
async def get_documents_indexing_status(
    collection_id: str = Query(..., description="Collection ID to check indexing status for"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Return indexing status for uploaded documents in a collection.
    
    **Parameters:**
    - **collection_id**: Collection ID to check indexing status for
    
    **Permissions:** Requires `read` permission
    
    **Returns:** Document indexing statistics including total, indexed, unindexed counts and progress percentage
    """
    try:
        from sqlalchemy import select, func
        total = (await db.execute(select(func.count(Document.id)).where(Document.collection_id == collection_id))).scalar() or 0
        indexed = (await db.execute(select(func.count(Document.id)).where((Document.collection_id == collection_id) & (Document.is_indexed == True)))).scalar() or 0
        unindexed = max(total - indexed, 0)
        progress = (indexed / total * 100.0) if total > 0 else 0.0
        return {
            "collection_id": collection_id,
            "documents_total": total,
            "indexed": indexed,
            "unindexed": unindexed,
            "progress_percent": round(progress, 1),
        }
    except Exception as e:
        logger.error(f"Error getting documents indexing status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting documents indexing status: {str(e)}")


@document_router.get(
    "/indexing-jobs/{job_id}",
    response_model=DocumentIndexJobStatus,
    summary="Get document indexing job status",
    description="Retrieve the latest status for a specific background indexing job",
    responses={
        200: {"description": "Indexing job status retrieved successfully"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Job not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_document_indexing_job_status(
    job_id: str = Path(..., description="Indexing job identifier"),
    api_key_info: APIKeyInfo = Depends(require_read_permission),
):
    job = get_document_index_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Indexing job not found")
    return job


@document_router.get(
    "/indexing-jobs",
    response_model=List[DocumentIndexJobStatus],
    summary="List document indexing jobs",
    description="List recent document indexing jobs, optionally filtered by collection",
    responses={
        200: {"description": "Indexing jobs listed successfully"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error"},
    },
)
async def list_document_indexing_job_status(
    collection_id: Optional[str] = Query(None, description="Optional collection ID to filter jobs"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of jobs to return"),
    api_key_info: APIKeyInfo = Depends(require_read_permission),
):
    return list_document_index_jobs(collection_id, limit)


@collection_router.get("/{collection_id}/indexing-status", 
                      response_model=Dict[str, Any],
                      summary="Get collection indexing status", 
                      description="Get combined indexing progress for documents and webpages in a collection",
                      responses={
                          200: {"description": "Combined indexing status retrieved successfully"},
                          403: {"description": "Insufficient permissions"},
                          500: {"description": "Internal server error"}
                      })
async def get_collection_indexing_status(
    collection_id: str = Path(..., description="Collection ID to check indexing status for"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Return combined indexing status for documents and webpages in a collection.
    
    **Parameters:**
    - **collection_id**: Collection ID to check indexing status for
    
    **Permissions:** Requires `read` permission
    
    **Returns:** Combined indexing statistics with separate document/webpage breakdowns and overall progress
    """
    try:
        from sqlalchemy import select, func
        # Documents
        doc_total = (await db.execute(select(func.count(Document.id)).where(Document.collection_id == collection_id))).scalar() or 0
        doc_indexed = (await db.execute(select(func.count(Document.id)).where((Document.collection_id == collection_id) & (Document.is_indexed == True)))).scalar() or 0
        doc_unindexed = max(doc_total - doc_indexed, 0)
        # Webpages
        web_total = (await db.execute(select(func.count(Webpage.id)).where(Webpage.collection_id == collection_id))).scalar() or 0
        web_indexed = (await db.execute(select(func.count(Webpage.id)).where((Webpage.collection_id == collection_id) & (Webpage.is_indexed == True)))).scalar() or 0
        web_unindexed = max(web_total - web_indexed, 0)

        total = doc_total + web_total
        indexed = doc_indexed + web_indexed
        progress = (indexed / total * 100.0) if total > 0 else 0.0

        return {
            "collection_id": collection_id,
            "documents": {"total": doc_total, "indexed": doc_indexed, "unindexed": doc_unindexed},
            "webpages": {"total": web_total, "indexed": web_indexed, "unindexed": web_unindexed},
            "combined": {"total": total, "indexed": indexed, "unindexed": total - indexed, "progress_percent": round(progress, 1)},
        }
    except Exception as e:
        logger.error(f"Error getting collection indexing status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting collection indexing status: {str(e)}")

# Collection Management Endpoints
@collection_router.post("/", response_model=CollectionResponse)
async def create_collection(
    request_data: CreateCollectionRequest,
    request: Request,
    api_key_info: APIKeyInfo = Depends(require_write_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new collection.
    Requires write permission.
    
    Args:
        request_data: Collection creation data
        request: Request object for audit logging
        
    Returns:
        Created collection data
    """
    try:
        import uuid
        collection_id = str(uuid.uuid4())
        # Create DB row
        db_obj = Collection(
            id=collection_id,
            name=request_data.name,
            description=request_data.description,
            collection_type=request_data.type,
            api_key_name=api_key_info.name,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Log audit action
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="create",
            resource_type="collection",
            resource_id=collection_id,
            details={
                "name": request_data.name,
                "type": request_data.type,
                "description": request_data.description
            },
            request=request,
            api_key_name=api_key_info.name
        )
        
        # Trigger RAG cache refresh
        try:
            from app.core.rag.tool_loader import refresh_collections
            refresh_collections(collection_id)
        except Exception as _e:
            logger.warning(f"RAG refresh after create failed: {_e}")

        # Build response
        return CollectionResponse(
            id=db_obj.id,
            name=db_obj.name,
            description=db_obj.description,
            type=db_obj.collection_type,
            created_at=db_obj.created_at.isoformat() if db_obj.created_at else datetime.now(timezone.utc).isoformat(),
            updated_at=db_obj.updated_at.isoformat() if db_obj.updated_at else datetime.now(timezone.utc).isoformat(),
            document_count=0,
            webpage_count=0,
        )
    
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")


@collection_router.post("/bulk", response_model=List[CollectionResponse])
async def bulk_create_collections(
    request_data: BulkCreateCollectionsRequest,
    request: Request,
    api_key_info: APIKeyInfo = Depends(require_write_permission),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple collections in a single request."""

    try:
        import uuid
        from sqlalchemy.exc import IntegrityError

        # Prevent duplicate names within the same payload to avoid partial commits
        provided_names = [item.name for item in request_data.collections]
        if len(provided_names) != len(set(provided_names)):
            raise HTTPException(status_code=400, detail="Duplicate collection names in request payload")

        new_objects: List[Collection] = []
        for payload in request_data.collections:
            collection_id = str(uuid.uuid4())
            obj = Collection(
                id=collection_id,
                name=payload.name,
                description=payload.description,
                collection_type=payload.type,
                api_key_name=api_key_info.name,
            )
            db.add(obj)
            new_objects.append(obj)

        try:
            await db.commit()
        except IntegrityError as integrity_error:
            await db.rollback()
            logger.warning("Bulk collection creation failed: %s", integrity_error)
            raise HTTPException(status_code=409, detail="One or more collections already exist")

        for obj in new_objects:
            await db.refresh(obj)

        # Audit log entries per collection (post-commit to avoid duplicate writes on failure)
        for obj, payload in zip(new_objects, request_data.collections):
            await log_audit_action(
                user_id=api_key_info.get_user_id(),
                action="create",
                resource_type="collection",
                resource_id=obj.id,
                details={
                    "name": payload.name,
                    "type": payload.type,
                    "description": payload.description,
                    "bulk": True,
                },
                request=request,
                api_key_name=api_key_info.name,
            )

        # Trigger targeted cache refresh for newly created collections
        try:
            from app.core.rag.tool_loader import refresh_collections

            refresh_collections([obj.id for obj in new_objects])
        except Exception as refresh_error:
            logger.warning("RAG refresh after bulk create failed: %s", refresh_error)

        now_iso = datetime.now(timezone.utc).isoformat()
        response_payload: List[CollectionResponse] = []
        for obj in new_objects:
            response_payload.append(
                CollectionResponse(
                    id=obj.id,
                    name=obj.name,
                    description=obj.description,
                    type=obj.collection_type,
                    created_at=obj.created_at.isoformat() if obj.created_at else now_iso,
                    updated_at=obj.updated_at.isoformat() if obj.updated_at else now_iso,
                    document_count=0,
                    webpage_count=0,
                )
            )

        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating collections in bulk: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating collections in bulk: {e}")

@collection_router.get("/collections", response_model=List[CollectionResponse])
async def list_collections(
    api_key_info: APIKeyInfo = Depends(require_read_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    List all collections with counts.
    Requires read permission.
    
    Returns:
        List of all collections with document and webpage counts
    """
    try:
        from sqlalchemy import select, func
        # Fetch all collections
        coll_result = await db.execute(select(Collection))
        rows = coll_result.scalars().all()

        # Precompute counts per collection_id
        doc_counts = {}
        web_counts = {}
        doc_rows = (await db.execute(select(Document.collection_id, func.count(Document.id)).group_by(Document.collection_id))).all()
        for cid, cnt in doc_rows:
            if cid:
                doc_counts[str(cid)] = cnt or 0
        web_rows = (await db.execute(select(Webpage.collection_id, func.count(Webpage.id)).group_by(Webpage.collection_id))).all()
        for cid, cnt in web_rows:
            if cid:
                web_counts[str(cid)] = cnt or 0

        # Build responses
        resp: List[CollectionResponse] = []
        for c in rows:
            resp.append(CollectionResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                type=c.collection_type,
                created_at=c.created_at.isoformat() if c.created_at else datetime.now(timezone.utc).isoformat(),
                updated_at=c.updated_at.isoformat() if c.updated_at else datetime.now(timezone.utc).isoformat(),
                document_count=doc_counts.get(c.id, 0),
                webpage_count=web_counts.get(c.id, 0),
            ))
        return resp
    
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")

@collection_router.put("/{collection_id}", response_model=CollectionResponse) 
async def update_collection(
    collection_id: str,
    request_data: UpdateCollectionRequest,
    request: Request,
    api_key_info: APIKeyInfo = Depends(require_write_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing collection.
    Requires write permission.
    
    Args:
        collection_id: ID of the collection to update
        request_data: Collection update data
        request: Request object for audit logging
        
    Returns:
        Updated collection data
    """
    try:
        # Load from DB
        db_obj = await db.get(Collection, collection_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Track changes for audit
        changes = {}
        if request_data.name is not None and request_data.name != db_obj.name:
            changes["name"] = {"old": db_obj.name, "new": request_data.name}
            db_obj.name = request_data.name
        if request_data.description is not None and request_data.description != db_obj.description:
            changes["description"] = {"old": db_obj.description, "new": request_data.description}
            db_obj.description = request_data.description
        if request_data.type is not None and request_data.type != db_obj.collection_type:
            changes["type"] = {"old": db_obj.collection_type, "new": request_data.type}
            db_obj.collection_type = request_data.type

        await db.commit()
        await db.refresh(db_obj)
        # Trigger RAG cache refresh
        try:
            from app.core.rag.tool_loader import refresh_collections
            refresh_collections(collection_id)
        except Exception as _e:
            logger.warning(f"RAG refresh after update failed: {_e}")
        
        # Log audit action
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="update",
            resource_type="collection",
            resource_id=collection_id,
            details={"changes": changes},
            request=request,
            api_key_name=api_key_info.name
        )
        
        # Add counts
        from sqlalchemy import select, func
        doc_count = (await db.execute(select(func.count(Document.id)).where(Document.collection_id == collection_id))).scalar() or 0
        webpage_count = (await db.execute(select(func.count(Webpage.id)).where(Webpage.collection_id == collection_id))).scalar() or 0

        return CollectionResponse(
            id=db_obj.id,
            name=db_obj.name,
            description=db_obj.description,
            type=db_obj.collection_type,
            created_at=db_obj.created_at.isoformat() if db_obj.created_at else datetime.now(timezone.utc).isoformat(),
            updated_at=db_obj.updated_at.isoformat() if db_obj.updated_at else datetime.now(timezone.utc).isoformat(),
            document_count=doc_count,
            webpage_count=webpage_count,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating collection: {str(e)}")

@collection_router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    request: Request,
    api_key_info: APIKeyInfo = Depends(require_delete_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a collection.
    Requires delete permission.
    
    Args:
        collection_id: ID of the collection to delete
        request: Request object for audit logging
        
    Returns:
        Confirmation message
    """
    try:
        db_obj = await db.get(Collection, collection_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Collection not found")

        if collection_id == "default":
            raise HTTPException(status_code=400, detail="Cannot delete default collection")

        collection_info = db_obj.to_dict()

        # Delete DB row
        await db.delete(db_obj)
        await db.commit()
        # Trigger RAG cache refresh
        try:
            from app.core.rag.tool_loader import refresh_collections
            refresh_collections(collection_id)
        except Exception as _e:
            logger.warning(f"RAG refresh after delete failed: {_e}")
        
        # Log audit action
        await log_audit_action(
            user_id=api_key_info.get_user_id(),
            action="delete",
            resource_type="collection",
            resource_id=collection_id,
            details={
                "name": collection_info.get("name"),
                "type": collection_info.get("type")
            },
            request=request,
            api_key_name=api_key_info.name
        )
        
        return {"message": f"Collection {collection_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting collection: {str(e)}")

@collection_router.get("/{collection_id}", response_model=Dict[str, Any])
async def get_collection_statistics(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get statistics about a specific collection.
    Requires read permission.
    
    Args:
        collection_id: The collection ID to get stats for
        db: Database session
        
    Returns:
        Collection statistics
    """
    try:
        stats = await get_collection_stats(db=db, collection_id=collection_id)
        if "indexed_count" not in stats:
            # Add a message to the response if indexing columns are missing
            stats["indexing_status"] = "not_available"
            stats["indexing_message"] = "Indexing columns not found in database. Run scripts/add_indexing_columns.py to add them."
        return stats
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting collection stats: {str(e)}")

@collection_router.get("/", response_model=Dict[str, Any])
async def get_all_collection_statistics(
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get statistics about all collections.
    Requires read permission.
    
    Args:
        db: Database session
        
    Returns:
        Statistics for all collections
    """
    try:
        stats = await get_collection_stats(db=db)
        # Add a note about running the migration script if needed
        stats["note"] = "For indexing statistics, ensure you've run scripts/add_indexing_columns.py"
        return stats
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting collection stats: {str(e)}")

# Register all routers with the main app
app.include_router(core_router)
# Import the chat endpoints router
from app.api.endpoints.chat_endpoints import router as chat_router
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
# Import the chat event endpoints router
from app.api.endpoints.chat_event_endpoints import router as chat_event_router
app.include_router(chat_event_router, prefix="/chat", tags=["Chat"])
# Import the rating endpoints router
from app.api.endpoints.rating_endpoints import router as rating_router
app.include_router(rating_router, prefix="/chat", tags=["Chat"])
# Import the audit endpoints router
from app.api.endpoints.audit_endpoints import router as audit_router
app.include_router(audit_router, prefix="/admin", tags=["Audit"])
# Import the transcription endpoints router
from app.api.endpoints.transcription_endpoints import router as transcription_router
app.include_router(transcription_router)
app.include_router(document_router)
app.include_router(crawler_router)
app.include_router(webpage_router)
app.include_router(collection_router)

if __name__ == "__main__":
    import os
    
    # Check if we should use uvloop
    use_uvloop = os.getenv("USE_UVLOOP", "false").lower() == "true"
    
    # Define directories to watch (exclude data directory)
    watch_dirs = ["app"]
    
    if use_uvloop:
        uvicorn.run(
            "app.api.fast_api_app:app", 
            host="0.0.0.0", 
            port=5000, 
            reload=True, 
            reload_dirs=watch_dirs
        )
    else:
        # Disable uvloop when running directly
        uvicorn.run(
            "app.api.fast_api_app:app", 
            host="0.0.0.0", 
            port=5000, 
            reload=True,
            loop="asyncio",  # Use standard asyncio instead of uvloop
            http="httptools",  # Use httptools to maintain performance
            reload_dirs=watch_dirs
        )