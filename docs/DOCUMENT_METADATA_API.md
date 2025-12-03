# Document Metadata CRUD API Documentation

## Overview

The Document Metadata API provides comprehensive CRUD (Create, Read, Update, Delete) operations for managing document metadata in the GovStack system. This API allows you to manage document properties, custom metadata fields, and document organization without touching the actual file content.

## Base URL

All document metadata endpoints are under:
```
/documents
```

## Authentication

All endpoints require API key authentication via the `X-API-Key` header:
```http
X-API-Key: your-api-key-here
```

### Permission Requirements

- **Read Operations**: Require `read` permission
- **Update Operations**: Require `write` permission
- **Delete Operations**: Require `delete` permission

---

## Endpoints

### 1. Upload Document with Metadata

**Endpoint:** `POST /documents/`

**Description:** Upload a new document with initial metadata configuration.

**Permission Required:** `write`

**Request:** `multipart/form-data`

**Form Fields:**
- `file` (required): The document file to upload
- `description` (optional): Document description text
- `is_public` (optional, default: `false`): Public visibility flag
- `collection_id` (required): Collection identifier for grouping
- `index_on_upload` (optional, default: `true`): Whether to trigger indexing immediately

**Example Request:**
```bash
curl -X POST "http://localhost:5000/documents/" \
  -H "X-API-Key: your-api-key" \
  -F "file=@policy_document.pdf" \
  -F "description=Government policy document for 2024" \
  -F "is_public=false" \
  -F "collection_id=policies-2024" \
  -F "index_on_upload=true"
```

**Response:** `201 Created`
```json
{
  "id": 123,
  "filename": "policy_document.pdf",
  "object_name": "a1b2c3d4-e5f6-7890-1234-567890abcdef.pdf",
  "content_type": "application/pdf",
  "size": 2048576,
  "upload_date": "2024-10-30T10:30:00.000000",
  "last_accessed": null,
  "description": "Government policy document for 2024",
  "is_public": false,
  "metadata": {
    "original_filename": "policy_document.pdf"
  },
  "collection_id": "policies-2024",
  "is_indexed": false,
  "indexed_at": null,
  "created_by": "user@example.com",
  "updated_by": null,
  "api_key_name": "main-api-key",
  "access_url": "https://minio.example.com/presigned-url...",
  "index_job_id": "job-uuid-here",
  "indexing_scheduled": true
}
```

---

### 2. Get Document with Access URL

**Endpoint:** `GET /documents/{document_id}`

**Description:** Retrieve complete document metadata including a presigned access URL to download the file.

**Permission Required:** `read`

**Path Parameters:**
- `document_id` (integer): The ID of the document

**Example Request:**
```bash
curl -X GET "http://localhost:5000/documents/123" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "filename": "policy_document.pdf",
  "object_name": "a1b2c3d4-e5f6-7890-1234-567890abcdef.pdf",
  "content_type": "application/pdf",
  "size": 2048576,
  "upload_date": "2024-10-30T10:30:00.000000",
  "last_accessed": "2024-10-30T14:15:22.000000",
  "description": "Government policy document for 2024",
  "is_public": false,
  "metadata": {
    "original_filename": "policy_document.pdf",
    "department": "Finance",
    "version": "1.0"
  },
  "collection_id": "policies-2024",
  "is_indexed": true,
  "indexed_at": "2024-10-30T10:35:00.000000",
  "created_by": "user@example.com",
  "updated_by": null,
  "api_key_name": "main-api-key",
  "access_url": "https://minio.example.com/presigned-url-valid-for-7-days"
}
```

**Side Effects:**
- Updates `last_accessed` timestamp

---

### 3. Get Document Metadata Only (NEW)

**Endpoint:** `GET /documents/{document_id}/metadata`

**Description:** Retrieve only document metadata without generating a presigned access URL. Use this for lightweight metadata queries.

**Permission Required:** `read`

**Path Parameters:**
- `document_id` (integer): The ID of the document

**Example Request:**
```bash
curl -X GET "http://localhost:5000/documents/123/metadata" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "filename": "policy_document.pdf",
  "object_name": "a1b2c3d4-e5f6-7890-1234-567890abcdef.pdf",
  "content_type": "application/pdf",
  "size": 2048576,
  "upload_date": "2024-10-30T10:30:00.000000",
  "last_accessed": "2024-10-30T14:15:22.000000",
  "description": "Government policy document for 2024",
  "is_public": false,
  "metadata": {
    "original_filename": "policy_document.pdf",
    "department": "Finance",
    "version": "1.0",
    "tags": ["policy", "finance", "2024"]
  },
  "collection_id": "policies-2024",
  "is_indexed": true,
  "indexed_at": "2024-10-30T10:35:00.000000",
  "created_by": "user@example.com",
  "updated_by": "admin@example.com",
  "api_key_name": "main-api-key"
}
```

**Notes:**
- No `access_url` field in response
- Does NOT update `last_accessed` timestamp
- Faster than the full GET endpoint

---

### 4. Update Document Metadata (NEW)

**Endpoint:** `PATCH /documents/{document_id}/metadata`

**Description:** Update only the metadata fields of a document without replacing the file. Supports partial updates and custom metadata objects.

**Permission Required:** `write`

**Path Parameters:**
- `document_id` (integer): The ID of the document

**Request Body:** `application/json`

```json
{
  "description": "Updated policy document for 2024 - Q4 revision",
  "is_public": true,
  "collection_id": "policies-2024-q4",
  "metadata": {
    "department": "Finance",
    "year": 2024,
    "quarter": "Q4",
    "version": "1.2",
    "tags": ["policy", "finance", "compliance", "updated"],
    "approval_status": "approved",
    "approved_by": "director@example.com",
    "approval_date": "2024-10-30"
  },
  "created_by": "user@example.com"
}
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | No | Updated description text (max 5000 chars) |
| `is_public` | boolean | No | Public visibility flag |
| `collection_id` | string | No | Collection identifier (max 64 chars) |
| `metadata` | object | No | Custom metadata fields (any JSON object) |
| `created_by` | string | No | User who created the document (max 100 chars) |

**Example Request:**
```bash
curl -X PATCH "http://localhost:5000/documents/123/metadata" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated policy document for 2024 - Q4 revision",
    "is_public": true,
    "metadata": {
      "department": "Finance",
      "version": "1.2",
      "tags": ["policy", "finance", "compliance"]
    }
  }'
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "filename": "policy_document.pdf",
  "object_name": "a1b2c3d4-e5f6-7890-1234-567890abcdef.pdf",
  "content_type": "application/pdf",
  "size": 2048576,
  "upload_date": "2024-10-30T10:30:00.000000",
  "last_accessed": "2024-10-30T14:15:22.000000",
  "description": "Updated policy document for 2024 - Q4 revision",
  "is_public": true,
  "metadata": {
    "original_filename": "policy_document.pdf",
    "department": "Finance",
    "version": "1.2",
    "tags": ["policy", "finance", "compliance"]
  },
  "collection_id": "policies-2024-q4",
  "is_indexed": false,
  "indexed_at": null,
  "created_by": "user@example.com",
  "updated_by": "admin@example.com",
  "api_key_name": "main-api-key",
  "index_job_id": "job-uuid-if-reindexing"
}
```

**Side Effects:**
- Updates `updated_by` field automatically
- If `collection_id` changes:
  - Deletes embeddings from old collection
  - Sets `is_indexed=false`
  - Triggers background reindexing in new collection
  - Returns `index_job_id` for tracking
- Custom metadata is **merged** with existing metadata (not replaced)
- Creates audit log entry with change tracking

**Metadata Merge Behavior:**

The `metadata` field uses a merge strategy. Existing fields are preserved unless explicitly overwritten:

**Before:**
```json
{
  "metadata": {
    "department": "Finance",
    "version": "1.0",
    "created_date": "2024-01-15"
  }
}
```

**Update Request:**
```json
{
  "metadata": {
    "version": "1.1",
    "tags": ["updated"]
  }
}
```

**After:**
```json
{
  "metadata": {
    "department": "Finance",
    "version": "1.1",
    "created_date": "2024-01-15",
    "tags": ["updated"]
  }
}
```

---

### 5. Bulk Update Document Metadata (NEW)

**Endpoint:** `POST /documents/bulk-metadata-update`

**Description:** Update metadata for multiple documents in a single operation. Useful for batch operations like re-categorization, archival, or mass tagging.

**Permission Required:** `write`

**Request Body:** `application/json`

```json
{
  "document_ids": [123, 124, 125, 126, 127],
  "metadata_updates": {
    "collection_id": "archive-2024",
    "is_public": false,
    "metadata": {
      "archived": true,
      "archived_date": "2024-10-30",
      "archived_by": "admin@example.com",
      "status": "archived"
    }
  }
}
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_ids` | array[integer] | Yes | List of document IDs (1-100 items) |
| `metadata_updates` | object | Yes | Metadata fields to apply to all documents |

**Limits:**
- Maximum 100 documents per request
- Processes documents sequentially
- Continues on errors

**Example Request:**
```bash
curl -X POST "http://localhost:5000/documents/bulk-metadata-update" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [123, 124, 125],
    "metadata_updates": {
      "collection_id": "archive-2024",
      "is_public": false,
      "metadata": {
        "archived": true,
        "archived_date": "2024-10-30"
      }
    }
  }'
```

**Response:** `200 OK`
```json
{
  "updated_count": 2,
  "failed_count": 1,
  "updated_ids": [123, 125],
  "failed_ids": [124],
  "errors": {
    "124": "Document not found"
  }
}
```

**Side Effects:**
- Updates each document individually
- For collection changes: triggers vector cleanup and reindexing
- Creates single audit log entry for the entire operation
- Returns detailed success/failure breakdown

---

### 6. Update Document (File + Metadata)

**Endpoint:** `PUT /documents/{document_id}`

**Description:** Update document with optional file replacement and/or metadata changes. This is the comprehensive update endpoint.

**Permission Required:** `write`

**Request:** `multipart/form-data`

**Form Fields:**
- `file` (optional): New file to replace existing document
- `description` (optional): Updated description
- `is_public` (optional): Updated visibility flag
- `collection_id` (optional): Collection ID to move document to

**Example Request (Metadata Only):**
```bash
curl -X PUT "http://localhost:5000/documents/123" \
  -H "X-API-Key: your-api-key" \
  -F "description=Updated description" \
  -F "is_public=true"
```

**Example Request (File + Metadata):**
```bash
curl -X PUT "http://localhost:5000/documents/123" \
  -H "X-API-Key: your-api-key" \
  -F "file=@new_version.pdf" \
  -F "description=Updated version of policy" \
  -F "collection_id=policies-2024-v2"
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "filename": "new_version.pdf",
  "object_name": "new-uuid-here.pdf",
  "content_type": "application/pdf",
  "size": 3145728,
  "upload_date": "2024-10-30T10:30:00.000000",
  "last_accessed": "2024-10-30T14:15:22.000000",
  "description": "Updated version of policy",
  "is_public": true,
  "metadata": {
    "original_filename": "new_version.pdf"
  },
  "collection_id": "policies-2024-v2",
  "is_indexed": false,
  "indexed_at": null,
  "created_by": "user@example.com",
  "updated_by": "admin@example.com",
  "api_key_name": "main-api-key",
  "index_job_id": "reindex-job-uuid"
}
```

**Side Effects:**
- If file provided:
  - Uploads new file to MinIO
  - Deletes old file from MinIO
  - Updates file-related fields (filename, size, content_type, object_name)
  - Deletes all vector embeddings for the document
  - Sets `is_indexed=false`
  - Triggers background reindexing
- If collection changes (same as file replacement)
- Updates `updated_by` field
- Creates audit log entry

**When to Use:**
- Use `PUT /documents/{id}` when you need to replace the file
- Use `PATCH /documents/{id}/metadata` for metadata-only updates (more efficient)

---

### 7. List Documents

**Endpoint:** `GET /documents/`

**Description:** List all documents with pagination.

**Permission Required:** `read`

**Query Parameters:**
- `skip` (integer, default: 0): Number of documents to skip
- `limit` (integer, default: 100): Maximum documents to return

**Example Request:**
```bash
curl -X GET "http://localhost:5000/documents/?skip=0&limit=50" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "filename": "policy_document.pdf",
    "object_name": "a1b2c3d4.pdf",
    "content_type": "application/pdf",
    "size": 2048576,
    "upload_date": "2024-10-30T10:30:00.000000",
    "description": "Government policy",
    "is_public": false,
    "metadata": {...},
    "collection_id": "policies-2024",
    "is_indexed": true,
    "indexed_at": "2024-10-30T10:35:00.000000",
    "created_by": "user@example.com",
    "updated_by": null,
    "api_key_name": "main-api-key"
  },
  ...
]
```

---

### 8. List Documents by Collection

**Endpoint:** `GET /documents/collection/{collection_id}`

**Description:** List documents in a specific collection with pagination.

**Permission Required:** `read`

**Path Parameters:**
- `collection_id` (string): The collection identifier

**Query Parameters:**
- `skip` (integer, default: 0): Number of documents to skip
- `limit` (integer, default: 100): Maximum documents to return

**Example Request:**
```bash
curl -X GET "http://localhost:5000/documents/collection/policies-2024?skip=0&limit=50" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "filename": "policy_document.pdf",
    "collection_id": "policies-2024",
    ...
  },
  ...
]
```

---

### 9. Delete Document

**Endpoint:** `DELETE /documents/{document_id}`

**Description:** Delete a document from MinIO storage, database, and vector embeddings.

**Permission Required:** `delete`

**Path Parameters:**
- `document_id` (integer): The ID of the document

**Example Request:**
```bash
curl -X DELETE "http://localhost:5000/documents/123" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
{
  "message": "Document 123 deleted successfully"
}
```

**Side Effects:**
- Deletes vector embeddings from ChromaDB
- Removes file from MinIO storage
- Deletes database record
- Creates audit log entry

---

## Custom Metadata Best Practices

The `metadata` field in documents accepts any JSON object, allowing you to store custom attributes relevant to your use case.

### Recommended Metadata Structure

```json
{
  "metadata": {
    // Document Classification
    "department": "Finance",
    "category": "Policy",
    "document_type": "Policy Document",
    "tags": ["compliance", "policy", "finance", "2024"],
    
    // Versioning
    "version": "1.2.3",
    "version_date": "2024-10-30",
    "previous_version_id": 122,
    
    // Lifecycle
    "status": "approved",
    "review_date": "2025-01-30",
    "expiry_date": "2025-12-31",
    
    // Approval Workflow
    "approval_status": "approved",
    "approved_by": "director@example.com",
    "approval_date": "2024-10-25",
    "approver_comments": "Approved for publication",
    
    // Business Context
    "project_id": "PROJ-2024-001",
    "reference_number": "POL-FIN-2024-042",
    "language": "en",
    "confidentiality": "internal",
    
    // Technical
    "checksum": "sha256:abc123...",
    "original_filename": "policy_document.pdf",
    "pages": 45,
    "word_count": 8500
  }
}
```

### Examples by Use Case

#### Legal Documents
```json
{
  "metadata": {
    "case_number": "2024-CV-001234",
    "court": "Supreme Court",
    "filing_date": "2024-10-15",
    "parties": ["Plaintiff Name", "Defendant Name"],
    "document_type": "Motion",
    "status": "filed"
  }
}
```

#### HR Documents
```json
{
  "metadata": {
    "employee_id": "EMP-12345",
    "document_type": "Employment Contract",
    "effective_date": "2024-11-01",
    "department": "Engineering",
    "confidentiality": "confidential",
    "retention_years": 7
  }
}
```

#### Financial Documents
```json
{
  "metadata": {
    "fiscal_year": 2024,
    "quarter": "Q4",
    "document_type": "Financial Report",
    "department": "Finance",
    "audited": true,
    "auditor": "External Audit Firm",
    "audit_date": "2024-10-28"
  }
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

### 400 Bad Request
```json
{
  "detail": "Invalid request data: field 'collection_id' exceeds maximum length"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions. Required: write"
}
```

### 404 Not Found
```json
{
  "detail": "Document 123 not found"
}
```

### 415 Unsupported Media Type
```json
{
  "detail": "Unsupported file type '.xyz'. Supported extensions: .pdf, .docx, .txt, ..."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error updating document metadata: database connection error"
}
```

---

## Audit Trail

All document metadata operations are automatically logged to the audit trail with:

- **User ID**: From API key
- **Action**: `upload`, `update`, `update_metadata`, `bulk_update_metadata`, `delete`
- **Resource Type**: `document`
- **Resource ID**: Document ID(s)
- **Details**: Changes made, including before/after values
- **Timestamp**: UTC timestamp
- **API Key Name**: Name of the API key used

**Example Audit Log Entry:**
```json
{
  "id": 456,
  "user_id": "admin@example.com",
  "action": "update_metadata",
  "resource_type": "document",
  "resource_id": "123",
  "details": {
    "changes": {
      "description": {
        "old": "Old description",
        "new": "Updated description"
      },
      "metadata": {
        "old": {"version": "1.0"},
        "new": {"version": "1.1", "status": "approved"}
      }
    },
    "index_job_id": "job-uuid-here"
  },
  "timestamp": "2024-10-30T14:20:00.000000",
  "api_key_name": "main-api-key",
  "ip_address": "192.168.1.100",
  "user_agent": "curl/7.68.0"
}
```

---

## Integration Examples

### Python Example

```python
import requests
import json

API_BASE = "http://localhost:5000"
API_KEY = "your-api-key-here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Upload document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "description": "My document",
        "collection_id": "my-collection",
        "is_public": False
    }
    response = requests.post(f"{API_BASE}/documents/", 
                            headers={"X-API-Key": API_KEY},
                            files=files,
                            data=data)
    document = response.json()
    doc_id = document["id"]

# Update metadata only
metadata_update = {
    "description": "Updated description",
    "metadata": {
        "department": "Finance",
        "tags": ["important", "2024"]
    }
}
response = requests.patch(f"{API_BASE}/documents/{doc_id}/metadata",
                         headers=headers,
                         json=metadata_update)
updated_doc = response.json()
print(f"Document updated: {updated_doc['id']}")

# Bulk update
bulk_update = {
    "document_ids": [doc_id, doc_id + 1, doc_id + 2],
    "metadata_updates": {
        "collection_id": "archive-2024",
        "metadata": {"archived": True}
    }
}
response = requests.post(f"{API_BASE}/documents/bulk-metadata-update",
                        headers=headers,
                        json=bulk_update)
result = response.json()
print(f"Updated {result['updated_count']} documents")
```

### JavaScript/TypeScript Example

```typescript
const API_BASE = "http://localhost:5000";
const API_KEY = "your-api-key-here";

// Update document metadata
async function updateDocumentMetadata(docId: number, updates: any) {
  const response = await fetch(`${API_BASE}/documents/${docId}/metadata`, {
    method: "PATCH",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(updates)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }
  
  return await response.json();
}

// Usage
const updates = {
  description: "Updated policy document",
  metadata: {
    department: "Finance",
    version: "2.0",
    tags: ["policy", "approved"]
  }
};

updateDocumentMetadata(123, updates)
  .then(doc => console.log("Updated:", doc))
  .catch(err => console.error("Error:", err));
```

### Bash/cURL Example

```bash
#!/bin/bash

API_BASE="http://localhost:5000"
API_KEY="your-api-key-here"

# Get document metadata
curl -X GET "$API_BASE/documents/123/metadata" \
  -H "X-API-Key: $API_KEY"

# Update document metadata
curl -X PATCH "$API_BASE/documents/123/metadata" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated document",
    "metadata": {
      "department": "Finance",
      "tags": ["important"]
    }
  }'

# Bulk update
curl -X POST "$API_BASE/documents/bulk-metadata-update" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [123, 124, 125],
    "metadata_updates": {
      "collection_id": "archive-2024",
      "metadata": {"archived": true}
    }
  }'
```

---

## Performance Considerations

### Metadata Updates vs Full Updates

| Operation | Endpoint | Performance | Use When |
|-----------|----------|-------------|----------|
| Metadata Only | `PATCH /documents/{id}/metadata` | Fast (no file I/O) | Updating attributes only |
| File + Metadata | `PUT /documents/{id}` | Slower (file upload/delete) | Replacing file content |
| Get Metadata | `GET /documents/{id}/metadata` | Fast (no presigned URL) | Lightweight queries |
| Get with URL | `GET /documents/{id}` | Slightly slower | Need download link |

### Bulk Operations

- Bulk updates process documents **sequentially** for data consistency
- Maximum 100 documents per bulk request
- Failed documents don't block subsequent updates
- Returns detailed success/failure breakdown
- Consider batch size based on:
  - Number of metadata fields being updated
  - Collection changes (triggers reindexing)
  - Network latency

### Indexing Impact

Operations that trigger vector reindexing:
- Changing `collection_id` (moves document between collections)
- Replacing file content (requires re-embedding)

Indexing runs **asynchronously** in the background. Use the returned `index_job_id` to track progress:

```bash
curl -X GET "http://localhost:5000/documents/indexing-jobs/{job_id}" \
  -H "X-API-Key: your-api-key"
```

---

## API Versioning

Current API version: **v1** (implicit in base URL)

Future versions will be explicitly versioned:
- `/v2/documents/...`

The current endpoints will remain stable with backward compatibility.

---

## Rate Limiting

*Note: Rate limiting is not currently enforced but may be added in future releases.*

Recommended client-side practices:
- Batch operations where possible (use bulk endpoints)
- Implement exponential backoff for retries
- Cache metadata locally when appropriate
- Use pagination for large result sets

---

## Support and Feedback

For issues, questions, or feature requests related to the Document Metadata API:

1. Check the [API Reference](./API_REFERENCE.md) for general API documentation
2. Review [Audit Trail System](./AUDIT_TRAIL_SYSTEM.md) for logging details
3. See [Data Currency and Updates](./DATA_CURRENCY_AND_UPDATES.md) for indexing information

---

## Changelog

### Version 1.1.0 (2024-10-30)
- **NEW**: `PATCH /documents/{id}/metadata` - Metadata-only updates
- **NEW**: `GET /documents/{id}/metadata` - Lightweight metadata retrieval
- **NEW**: `POST /documents/bulk-metadata-update` - Bulk metadata updates
- **ENHANCED**: Custom metadata support with merge behavior
- **ENHANCED**: Comprehensive audit logging for all operations
- **ENHANCED**: Automatic vector cleanup on collection changes

### Version 1.0.0
- Initial document management endpoints
- Upload, retrieve, update (with file), delete operations
- Basic metadata support
