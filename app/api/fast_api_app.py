"""
FastAPI application for the GovStack service.
"""

from dotenv import load_dotenv
load_dotenv()


import os
import logging
from io import BytesIO
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import uvicorn
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager

from app.utils.storage import minio_client
from app.db.models.document import Document, Base as DocumentBase
from app.db.models.webpage import Webpage, WebpageLink, Base as WebpageBase
from app.db.models.chat import Chat, ChatMessage, Base as ChatBase
from app.db.models.chat_event import ChatEvent, Base as ChatEventBase
from app.db.models.message_rating import MessageRating, Base as MessageRatingBase
from app.db.models.audit_log import AuditLog, Base as AuditBase
from app.core.crawlers.web_crawler import crawl_website
from app.core.crawlers.utils import get_page_as_markdown
from app.core.rag.indexer import extract_text_batch, get_collection_stats, start_background_indexing, start_background_document_indexing
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting up GovStack API")
    async with engine.begin() as conn:
        # Create tables if they don't exist
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        # Generate a unique object name
        file_extension = os.path.splitext(file.filename or "")[1] if file.filename and "." in file.filename else ""
        object_name = f"{uuid.uuid4()}{file_extension}"
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Prepare MinIO metadata with required collection_id
        minio_metadata = {"collection_id": collection_id}
        
        # Convert bytes to file-like object for MinIO
        file_obj = BytesIO(file_content)
        
        # Upload to MinIO
        minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
            metadata=minio_metadata  # Pass metadata here
        )
        
        # Create document record with audit trail
        document = Document(
            filename=file.filename,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            description=description,
            is_public=is_public,
            metadata={"original_filename": file.filename},
            collection_id=collection_id,
            created_by=api_key_info.get_user_id(),
            api_key_name=api_key_info.name
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
        
        # Start background indexing for the uploaded document
        background_tasks.add_task(start_background_document_indexing, collection_id)
        
        # Generate access URL
        access_url = minio_client.get_presigned_url(object_name)
        
        # Return metadata with URL
        result = document.to_dict()
        result["access_url"] = access_url
        
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

# Simple in-memory collection storage (should be replaced with database model)
collections_storage = {
    "default": {
        "id": "default",
        "name": "Default Collection",
        "description": "Default collection for uncategorized content",
        "type": "mixed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
}

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

# Collection Management Endpoints
@collection_router.post("/", response_model=CollectionResponse)
async def create_collection(
    request_data: CreateCollectionRequest,
    request: Request,
    api_key_info: APIKeyInfo = Depends(require_write_permission)
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
        current_time = datetime.now(timezone.utc).isoformat()
        
        collection_data = {
            "id": collection_id,
            "name": request_data.name,
            "description": request_data.description,
            "type": request_data.type,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        collections_storage[collection_id] = collection_data
        
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
        
        # Add counts (would come from database queries in real implementation)
        response_data = collection_data.copy()
        response_data.update({
            "document_count": 0,
            "webpage_count": 0
        })
        
        return response_data
    
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")

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
        
        collections = []
        for collection_id, collection_data in collections_storage.items():
            # Get document count for this collection
            doc_query = select(func.count(Document.id)).where(Document.collection_id == collection_id)
            doc_result = await db.execute(doc_query)
            doc_count = doc_result.scalar() or 0
            
            # Get webpage count for this collection  
            webpage_query = select(func.count(Webpage.id)).where(Webpage.collection_id == collection_id)
            webpage_result = await db.execute(webpage_query)
            webpage_count = webpage_result.scalar() or 0
            
            response_data = collection_data.copy()
            response_data.update({
                "document_count": doc_count,
                "webpage_count": webpage_count
            })
            collections.append(response_data)
        
        return collections
    
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
        if collection_id not in collections_storage:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        collection_data = collections_storage[collection_id].copy()
        original_data = collection_data.copy()
        
        # Update fields that were provided
        changes = {}
        if request_data.name is not None:
            changes["name"] = {"old": collection_data.get("name"), "new": request_data.name}
            collection_data["name"] = request_data.name
        if request_data.description is not None:
            changes["description"] = {"old": collection_data.get("description"), "new": request_data.description}
            collection_data["description"] = request_data.description
        if request_data.type is not None:
            changes["type"] = {"old": collection_data.get("type"), "new": request_data.type}
            collection_data["type"] = request_data.type
        
        collection_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        collections_storage[collection_id] = collection_data
        
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
        doc_query = select(func.count(Document.id)).where(Document.collection_id == collection_id)
        doc_result = await db.execute(doc_query)
        doc_count = doc_result.scalar() or 0
        
        webpage_query = select(func.count(Webpage.id)).where(Webpage.collection_id == collection_id)
        webpage_result = await db.execute(webpage_query)
        webpage_count = webpage_result.scalar() or 0
        
        response_data = collection_data.copy()
        response_data.update({
            "document_count": doc_count,
            "webpage_count": webpage_count
        })
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating collection: {str(e)}")

@collection_router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    request: Request,
    api_key_info: APIKeyInfo = Depends(require_delete_permission)
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
        if collection_id not in collections_storage:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        if collection_id == "default":
            raise HTTPException(status_code=400, detail="Cannot delete default collection")
        
        # Store collection info for audit log
        collection_info = collections_storage[collection_id].copy()
        
        del collections_storage[collection_id]
        
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