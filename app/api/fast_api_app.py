"""
FastAPI application for the GovStack service.
"""

import os
import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import uvicorn

from app.utils.storage import minio_client
from app.db.models.document import Document, Base

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
        await conn.run_sync(Base.metadata.create_all)

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
        result.last_accessed = datetime.utcnow()
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

if __name__ == "__main__":
    uvicorn.run("fast_api_app:app", host="0.0.0.0", port=5000, reload=True)