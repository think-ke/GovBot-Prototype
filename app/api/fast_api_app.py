"""
FastAPI application for the GovStack service.
"""

from dotenv import load_dotenv
load_dotenv()


import os
import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, APIRouter
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
from app.core.crawlers.web_crawler import crawl_website
from app.core.crawlers.utils import get_page_as_markdown
from app.core.rag.indexer import extract_text_batch, get_collection_stats, start_background_indexing
from app.core.orchestrator import generate_agent

import logfire

logfire.configure()

logfire.instrument_openai()
logfire.instrument()
logfire.instrument_httpx()
logfire.instrument_aiohttp_client()
logfire.instrument_system_metrics()
logfire.instrument_asyncpg()
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
    yield
    # Shutdown logic
    logger.info("Shutting down GovStack API")

# Initialize FastAPI app
app = FastAPI(
    title="GovStack API",
    description="GovStack Document Management API",
    version="0.1.0",
    lifespan=lifespan  # Use the new lifespan manager
)

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
    """Root endpoint."""
    return {"message": "Welcome to GovStack API"}

@core_router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

# Chat models are now defined in the chat_endpoints.py module

# Document endpoints
@document_router.post("/", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(None),
    is_public: bool = Form(False),
    collection_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to MinIO storage and save its metadata in the database.
    
    Args:
        file: The file to upload
        description: Optional description of the document
        is_public: Whether the document should be publicly accessible
        collection_id: Identifier for grouping documents
        db: Database session
        
    Returns:
        Document metadata with access URL
    """
    try:
        # Generate a unique object name
        file_extension = os.path.splitext(file.filename)[1] if "." in file.filename else ""
        object_name = f"{uuid.uuid4()}{file_extension}"
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Prepare MinIO metadata
        minio_metadata = None
        if collection_id:
            minio_metadata = {"collection_id": collection_id}
        
        # Upload to MinIO
        minio_client.upload_file(
            file_obj=file_content,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
            metadata=minio_metadata  # Pass metadata here
        )
        
        # Create document record
        document = Document(
            filename=file.filename,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            description=description,
            is_public=is_public,
            metadata={"original_filename": file.filename},
            collection_id=collection_id  # Pass collection_id to Document constructor
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get document metadata and generate a presigned URL for access.
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    List documents with pagination.
    
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

@document_router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document from both MinIO storage and the database.
    
    Args:
        document_id: ID of the document to delete
        db: Database session
        
    Returns:
        Confirmation message
    """
    try:
        # Get document from database
        document = await db.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from MinIO
        object_name = document.object_name
        minio_client.delete_file(object_name)
        
        # Delete from database
        await db.delete(document)
        await db.commit()
        
        return {"message": f"Document {document_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# Web Crawler API Models
class CrawlWebsiteRequest(BaseModel):
    """Request model for crawling a website."""
    url: HttpUrl
    depth: int = Field(default=3, ge=1, le=10)
    concurrent_requests: int = Field(default=10, ge=1, le=50)
    follow_external: bool = Field(default=False)
    strategy: str = Field(default="breadth_first", pattern="^(breadth_first|depth_first)$")
    collection_id: Optional[str] = Field(default=None, description="Identifier for grouping crawl jobs")
    
class WebpageResponse(BaseModel):
    """Response model for webpage data."""
    id: int
    url: str
    title: Optional[str] = None
    crawl_depth: int
    last_crawled: Optional[str] = None
    status_code: Optional[int] = None
    collection_id: Optional[str] = None
    
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

# In-memory storage for background task status
crawl_tasks = {}

# Web Crawler Endpoints
@crawler_router.post("/", response_model=CrawlStatusResponse)
async def start_crawl(
    request: CrawlWebsiteRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a website crawl operation in the background.
    
    Args:
        request: Crawl configuration
        background_tasks: Background task manager
        db: Database session
        
    Returns:
        Initial crawl status including task ID
    """
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        # Initialize task status
        crawl_tasks[task_id] = {
            "status": "starting",
            "seed_urls": [str(request.url)],
            "start_time": datetime.now(timezone.utc).isoformat(),
            "urls_crawled": 0,
            "total_urls_queued": 1,
            "errors": 0,
            "finished": False,
            "collection_id": request.collection_id,
        }
        
        # Define the background task function
        async def background_crawl():
            try:
                # Update status to running
                crawl_tasks[task_id]["status"] = "running"
                # Start the crawl operation                
                result = await crawl_website(
                    seed_url=str(request.url),
                    depth=request.depth,
                    concurrent_requests=request.concurrent_requests,
                    follow_external=request.follow_external,
                    strategy=request.strategy,
                    collection_id=request.collection_id,
                    session_maker=async_session,
                    task_status=crawl_tasks[task_id]
                )
                # Update task status on completion
                crawl_tasks[task_id].update({
                    "status": "completed",
                    "urls_crawled": result.get("urls_crawled", 0),
                    "errors": result.get("errors", 0),
                    "finished": True
                })
                
                # Start background indexing for the collection if a collection_id was provided
                if request.collection_id:
                    logger.info(f"Crawl completed, starting background indexing for collection '{request.collection_id}'")
                    start_background_indexing(request.collection_id)
                
            except Exception as e:
                logger.error(f"Error in background crawl task: {str(e)}")
                crawl_tasks[task_id].update({
                    "status": "failed",
                    "error_message": str(e),
                    "finished": True
                })
        
        # Add the crawl task to background tasks
        background_tasks.add_task(background_crawl)
        
        # Return initial status
        return CrawlStatusResponse(
            task_id=task_id,
            status=crawl_tasks[task_id]["status"],
            seed_urls=crawl_tasks[task_id]["seed_urls"],
            start_time=crawl_tasks[task_id]["start_time"],
            finished=False,
            collection_id=request.collection_id
        )
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting crawl: {str(e)}")

@crawler_router.get("/{task_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(task_id: str):
    """
    Get the status of a crawl operation.
    
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
async def fetch_webpage(request: FetchWebpageRequest):
    """
    Fetch a single webpage and convert it to markdown.
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    List webpages with pagination.
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get webpage details with optional content and links.
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get all webpages in a specific collection.
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get a webpage by its URL.
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    Extract text content from webpages in a specific collection.
    
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

@collection_router.get("/{collection_id}", response_model=Dict[str, Any])
async def get_collection_statistics(
    collection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about a specific collection.
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about all collections.
    
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