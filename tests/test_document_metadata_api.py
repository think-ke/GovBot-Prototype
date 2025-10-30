"""
Test script for Document Metadata CRUD API endpoints.

This script tests the new document metadata management endpoints:
- PATCH /documents/{id}/metadata
- GET /documents/{id}/metadata
- POST /documents/bulk-metadata-update
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db, engine
from app.db.models.document import Document, Base as DocumentBase
from app.api.fast_api_app import app


@pytest.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session():
    """Create test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(DocumentBase.metadata.create_all)
    
    async for session in get_db():
        yield session
        break


@pytest.fixture
async def sample_document(db_session: AsyncSession):
    """Create a sample document for testing."""
    doc = Document(
        filename="test_doc.pdf",
        object_name="test-uuid.pdf",
        content_type="application/pdf",
        size=1024,
        description="Test document",
        is_public=False,
        meta_data={"original_filename": "test_doc.pdf", "department": "IT"},
        collection_id="test-collection",
        created_by="test@example.com",
        api_key_name="test-key"
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.mark.asyncio
async def test_get_document_metadata(async_client: AsyncClient, sample_document: Document):
    """Test GET /documents/{id}/metadata endpoint."""
    response = await async_client.get(
        f"/documents/{sample_document.id}/metadata",
        headers={"X-API-Key": "test-api-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_document.id
    assert data["filename"] == "test_doc.pdf"
    assert data["metadata"]["department"] == "IT"
    assert "access_url" not in data  # Should not include access URL


@pytest.mark.asyncio
async def test_update_document_metadata(async_client: AsyncClient, sample_document: Document):
    """Test PATCH /documents/{id}/metadata endpoint."""
    update_data = {
        "description": "Updated test document",
        "is_public": True,
        "metadata": {
            "department": "Finance",
            "version": "2.0",
            "tags": ["important", "updated"]
        }
    }
    
    response = await async_client.patch(
        f"/documents/{sample_document.id}/metadata",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated test document"
    assert data["is_public"] is True
    assert data["metadata"]["department"] == "Finance"
    assert data["metadata"]["version"] == "2.0"
    # Original metadata should be preserved
    assert data["metadata"]["original_filename"] == "test_doc.pdf"


@pytest.mark.asyncio
async def test_update_metadata_with_collection_change(
    async_client: AsyncClient, 
    sample_document: Document
):
    """Test metadata update with collection change triggers reindexing."""
    update_data = {
        "collection_id": "new-collection",
        "metadata": {
            "moved": True
        }
    }
    
    response = await async_client.patch(
        f"/documents/{sample_document.id}/metadata",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_id"] == "new-collection"
    assert data["is_indexed"] is False  # Should be marked for reindexing
    assert "index_job_id" in data  # Should include reindexing job ID


@pytest.mark.asyncio
async def test_bulk_metadata_update(async_client: AsyncClient, db_session: AsyncSession):
    """Test POST /documents/bulk-metadata-update endpoint."""
    # Create multiple documents
    doc_ids = []
    for i in range(3):
        doc = Document(
            filename=f"bulk_test_{i}.pdf",
            object_name=f"bulk-test-{i}.pdf",
            content_type="application/pdf",
            size=1024,
            collection_id="bulk-test",
            created_by="test@example.com",
            api_key_name="test-key"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        doc_ids.append(doc.id)
    
    # Bulk update
    bulk_update_data = {
        "document_ids": doc_ids,
        "metadata_updates": {
            "collection_id": "bulk-archive",
            "is_public": False,
            "metadata": {
                "archived": True,
                "archived_date": "2024-10-30"
            }
        }
    }
    
    response = await async_client.post(
        "/documents/bulk-metadata-update",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=bulk_update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["updated_count"] == 3
    assert data["failed_count"] == 0
    assert len(data["updated_ids"]) == 3
    assert len(data["failed_ids"]) == 0


@pytest.mark.asyncio
async def test_bulk_update_with_failures(async_client: AsyncClient, sample_document: Document):
    """Test bulk update handles failures gracefully."""
    bulk_update_data = {
        "document_ids": [sample_document.id, 99999, 88888],  # Include non-existent IDs
        "metadata_updates": {
            "metadata": {
                "test": True
            }
        }
    }
    
    response = await async_client.post(
        "/documents/bulk-metadata-update",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=bulk_update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["updated_count"] == 1
    assert data["failed_count"] == 2
    assert sample_document.id in data["updated_ids"]
    assert 99999 in data["failed_ids"]
    assert 88888 in data["failed_ids"]
    assert data["errors"] is not None


@pytest.mark.asyncio
async def test_metadata_merge_behavior(async_client: AsyncClient, sample_document: Document):
    """Test that metadata fields are merged, not replaced."""
    # Initial metadata: {"original_filename": "test_doc.pdf", "department": "IT"}
    
    # Update with new fields
    update_data = {
        "metadata": {
            "version": "1.0",
            "tags": ["new"]
        }
    }
    
    response = await async_client.patch(
        f"/documents/{sample_document.id}/metadata",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have both old and new fields
    assert data["metadata"]["original_filename"] == "test_doc.pdf"
    assert data["metadata"]["department"] == "IT"
    assert data["metadata"]["version"] == "1.0"
    assert data["metadata"]["tags"] == ["new"]


@pytest.mark.asyncio
async def test_partial_metadata_update(async_client: AsyncClient, sample_document: Document):
    """Test that only provided fields are updated."""
    # Update only description
    update_data = {
        "description": "Only description updated"
    }
    
    response = await async_client.patch(
        f"/documents/{sample_document.id}/metadata",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Description should be updated
    assert data["description"] == "Only description updated"
    # Other fields should remain unchanged
    assert data["is_public"] == sample_document.is_public
    assert data["collection_id"] == sample_document.collection_id


@pytest.mark.asyncio
async def test_bulk_update_validation(async_client: AsyncClient):
    """Test bulk update validation."""
    # Test with empty document_ids
    bulk_update_data = {
        "document_ids": [],
        "metadata_updates": {}
    }
    
    response = await async_client.post(
        "/documents/bulk-metadata-update",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=bulk_update_data
    )
    
    assert response.status_code == 422  # Validation error
    
    # Test with too many document_ids
    bulk_update_data = {
        "document_ids": list(range(101)),  # > 100
        "metadata_updates": {}
    }
    
    response = await async_client.post(
        "/documents/bulk-metadata-update",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"},
        json=bulk_update_data
    )
    
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    """Run tests manually for quick validation."""
    print("Document Metadata API Test Suite")
    print("=" * 50)
    print("\nThese tests validate the new metadata CRUD endpoints:")
    print("- PATCH /documents/{id}/metadata")
    print("- GET /documents/{id}/metadata") 
    print("- POST /documents/bulk-metadata-update")
    print("\nRun with: pytest tests/test_document_metadata_api.py -v")
    print("\nNote: Requires running API server and proper test database setup.")
