"""
FastAPI application for the GovStack service.
"""

import os
import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import uvicorn
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any

from app.utils.storage import minio_client
from app.db.models.document import Document, Base as DocumentBase
from app.db.models.webpage import Webpage, WebpageLink, Base as WebpageBase
from app.core.crawlers.web_crawler import crawl_website
from app.core.crawlers.utils import get_page_as_markdown

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GovStack API",
    description="GovStack Document Management API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Database dependency
async def get_db():
    """Get database session."""
    db = async_session()
    try:
        yield db
    finally:
        await db.close()

@app.on_event("startup")
async def startup():
    """Application startup: initialize database tables if needed."""
    logger.info("Starting up GovStack API")
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(DocumentBase.metadata.create_all)
        await conn.run_sync(WebpageBase.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    """Application shutdown: close resources."""
    logger.info("Shutting down GovStack API")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to GovStack API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

# Document endpoints
@app.post("/documents/", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(None),
    is_public: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to MinIO storage and save its metadata in the database.
    
    Args:
        file: The file to upload
        description: Optional description of the document
        is_public: Whether the document should be publicly accessible
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
        
        # Upload to MinIO
        minio_client.upload_file(
            file_obj=file_content,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Create document record
        document = Document(
            filename=file.filename,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            description=description,
            is_public=is_public,
            metadata={"original_filename": file.filename}
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

@app.get("/documents/{document_id}")
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

@app.get("/documents/")
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

@app.delete("/documents/{document_id}")
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
    
class WebpageResponse(BaseModel):
    """Response model for webpage data."""
    id: int
    url: str
    title: Optional[str] = None
    crawl_depth: int
    last_crawled: Optional[str] = None
    status_code: Optional[int] = None
    
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

# In-memory storage for background task status
crawl_tasks = {}

# Web Crawler Endpoints
@app.post("/crawl/", response_model=CrawlStatusResponse)
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
                    crawl_strategy=request.strategy,
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
            finished=False
        )
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting crawl: {str(e)}")

@app.get("/crawl/{task_id}", response_model=CrawlStatusResponse)
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
        finished=task_status.get("finished", False)
    )

@app.post("/fetch-webpage/", response_model=WebpageFetchResponse)
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

@app.get("/webpages/", response_model=List[WebpageResponse])
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
                status_code=wp.status_code
            ) 
            for wp in webpages
        ]
        
    except Exception as e:
        logger.error(f"Error listing webpages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing webpages: {str(e)}")

@app.get("/webpages/{webpage_id}", response_model=Dict[str, Any])
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

if __name__ == "__main__":
    uvicorn.run("fast_api_app:app", host="0.0.0.0", port=5000, reload=True)