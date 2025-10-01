# GovStack API Reference

## Authentication

All API endpoints (except `/` and `/health`) require authentication via the `X-API-Key` header.

```http
X-API-Key: your-api-key-here
## Transcription API

GovStack exposes Groq Whisper-based speech-to-text functionality via `/transcriptions` endpoints. The service uses the [Groq Speech-to-Text API](https://console.groq.com/docs/speech-to-text) and currently defaults to the `whisper-large-v3-turbo` model for fast multilingual transcription.

### Create Transcription Job

```http
POST /transcriptions/
Content-Type: multipart/form-data
X-API-Key: your-api-key-here
```

**Required permission:** `write`

**Form fields:**
- `file` *(required)* – audio file upload. Supported types: `flac`, `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `ogg`, `wav`, `webm`.
- `model` *(optional)* – Groq Whisper model ID. Defaults to `whisper-large-v3-turbo`.
- `metadata` *(optional)* – JSON string saved alongside the transcription record.

### Permission Levels
|------------|-------------|-----------|
| `read` | View data and chat history | GET endpoints, chat history |
| `write` | Create and modify data | POST endpoints, document upload, chat |
| `delete` | Remove data | DELETE endpoints |

- `GOVSTACK_ADMIN_API_KEY`: Admin key (read, write)

## Core Endpoints

### Health Check

**Public endpoint - no authentication required**

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-10-20T14:30:15.123456Z"
}
```

### API Information

**Response:**
```json
{
  "api_key_name": "master",
  "permissions": ["read", "write", "delete"],
  "description": "Master API key with full access"
}
```

## Chat API

### Create Chat Message

Process a chat message and get an AI response.

```http
POST /chat/
Content-Type: application/json
X-API-Key: your-api-key-here
```json
{
  "message": "What services does the government provide for business registration?",
  "session_id": "optional-existing-session-id",
  "user_id": "user123",
  "metadata": {
    "platform": "web",
    "language": "en"
  }
}
```

### Agency-Scoped Chat

Chat with a specific agency/collection assistant.

  - Legacy alias (`kfc`, `kfcb`, `brs`, `odpc`)
  - Collection name (`Kenya Film Commission`)
  - Canonical UUID (`3fa85f64-5717-4562-b3fc-2c963f66afa6`)

**Request Body:** Same as `/chat/`

**Response:** Same as `/chat/` but scoped to specific agency's knowledge base

**Side Effects:**

**Response:**
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "answer": "To register a business in Kenya, you need to follow these steps...",
  "sources": [
    {
      "title": "Business Registration Guidelines",
      "url": "https://example.gov/business-reg",
      "snippet": "The Business Registration Service (BRS) is a state corporation..."
    }
  ],
    "What are the fees for business registration?",
    "How long does the business registration process take?"
  ],
  "usage": {
    "requests": 1,
    "request_tokens": 891,
    "response_tokens": 433,
    "total_tokens": 1324,
    "details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "cached_tokens": 0
    }
  }
}
```

### Get Chat History

Retrieve the conversation history for a session.

```http
```

**Response:**
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "messages": [
    {
      "id": 1,
      },
      "timestamp": "2023-10-20T14:30:15.123456"
    },
    {
      "id": 2,
      "message_id": "msg2",
      "message_type": "assistant",
      },
      "timestamp": "2023-10-20T14:30:18.654321"
    }
  ],
  "created_at": "2023-10-20T14:30:15.123456",
  "updated_at": "2023-10-20T14:30:18.654321",
  "message_count": 2,
  "num_messages": 2
}
```
### Delete Chat Session

Remove a chat session and all its messages.

```http
DELETE /chat/{session_id}
X-API-Key: your-api-key-here
```

**Response:**
```json
{
  "message": "Chat session 3fa85f64-5717-4562-b3fc-2c963f66afa6 deleted successfully"
}
```

## Chat Events

### Get Chat Events

Retrieve processing events for a chat session.

```http
GET /chat/events/{session_id}
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `limit`: Maximum events to return (default: 50, max: 500)
- `event_type`: Filter by specific event type
- `event_status`: Filter by event status ('started', 'progress', 'completed', 'failed')

**Required Permission:** `read`

**Response:**
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "events": [
    {
      "id": 1,
      "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "message_id": "msg1",
      "event_type": "message_received",
      "event_status": "completed",
      "event_data": {
        "message_length": 45
      },
      "user_message": "✅ Message received and validated",
      "timestamp": "2023-10-20T14:30:15.123456",
      "processing_time_ms": 120
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

### Get Latest Chat Events

Get the most recent events for a session.

```http
GET /chat/events/{session_id}/latest?count=10
X-API-Key: your-api-key-here
```

**Required Permission:** `read`

### WebSocket Event Stream

Real-time event streaming for a chat session.

```
ws://your-domain/chat/ws/events/{session_id}
```

**Message Format:**
```json
{
  "type": "event",
  "event": {
    "id": 1,
    "event_type": "agent_thinking",
    "event_status": "started",
    "user_message": "🤔 AI is analyzing your question...",
    "timestamp": "2023-10-20T14:30:15.123456"
  }
}
```

## Message Ratings

### Submit Rating

Rate an assistant message.

```http
POST /chat/ratings
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "message_id": "msg1",
  "rating": 5,
  "feedback_text": "Very helpful response!",
  "user_id": "user123",
  "metadata": {
    "category": "helpful"
  }
}
```

**Required Permission:** `write`

**Response:**
```json
{
  "id": 1,
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "message_id": "msg1",
  "user_id": "user123",
  "rating": 5,
  "feedback_text": "Very helpful response!",
  "created_at": "2023-10-20T14:30:15.123456",
  "updated_at": "2023-10-20T14:30:15.123456",
  "metadata": {
    "category": "helpful"
  }
}
```

### Get Rating

Retrieve a specific rating.

```http
GET /chat/ratings/{rating_id}
X-API-Key: your-api-key-here
```

**Required Permission:** `read`

### Update Rating

Update an existing rating.

```http
PUT /chat/ratings/{rating_id}
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "rating": 4,
  "feedback_text": "Updated feedback"
}
```

**Required Permission:** `write`

### List Ratings

Get ratings with filtering options.

```http
GET /chat/ratings?session_id=3fa85f64-5717-4562-b3fc-2c963f66afa6&rating=5
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `session_id`: Filter by session
- `message_id`: Filter by message
- `user_id`: Filter by user
- `rating`: Filter by rating value
- `skip`: Pagination offset
- `limit`: Maximum results

**Required Permission:** `read`

### Get Rating Statistics

Get aggregated rating statistics.

```http
GET /chat/ratings/stats
X-API-Key: your-api-key-here
```

**Required Permission:** `read`

**Response:**
```json
{
  "total_ratings": 150,
  "average_rating": 4.2,
  "rating_distribution": {
    "1": 5,
    "2": 10,
    "3": 25,
    "4": 60,
    "5": 50
  },
  "recent_ratings_trend": [
    {
      "date": "2023-10-20",
      "average_rating": 4.3,
      "count": 15
    }
  ]
}
```

## Audit Logs

### List Audit Logs

Retrieve system audit logs.

```http
GET /audit-logs
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (1-1000, default: 50)
- `user_id`: Filter by user ID
- `action`: Filter by action type
- `resource_type`: Filter by resource type
- `resource_id`: Filter by resource ID
- `hours_ago`: Filter by hours ago (max 1 year)

**Required Permission:** `admin`

**Response:**
```json
[
  {
    "id": 1,
    "user_id": "user123",
    "action": "upload",
    "resource_type": "document",
    "resource_id": "doc1",
    "details": {
      "filename": "policy.pdf",
      "size": 1024000
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "api_key_name": "master",
    "timestamp": "2023-10-20T14:30:15.123456"
  }
]
```

### Get Audit Summary

Get audit activity summary.

```http
GET /audit-logs/summary
X-API-Key: your-api-key-here
```

**Required Permission:** `admin`

**Response:**
```json
{
  "total_actions": 1500,
  "unique_users": 25,
  "action_counts": {
    "upload": 500,
    "delete": 100,
    "crawl_start": 50
  },
  "resource_type_counts": {
    "document": 600,
    "webpage": 400,
    "collection": 50
  },
  "recent_activity": [...]
}
```

### Get User Audit Logs

Get audit logs for a specific user.

```http
GET /audit-logs/user/{user_id}
X-API-Key: your-api-key-here
```

**Required Permission:** `admin`

### Get Resource Audit Logs

Get audit logs for a specific resource.

```http
GET /audit-logs/resource/{resource_type}/{resource_id}
X-API-Key: your-api-key-here
```

**Required Permission:** `admin`

## Document Management

### Upload Document

Upload a document to storage.

```http
POST /documents/
Content-Type: multipart/form-data
X-API-Key: your-api-key-here
```

**Form Fields:**
- `file`: The document file (required)
- `description`: Optional description text
- `is_public`: Boolean, default false
- `collection_id`: Optional collection identifier

**Response:**
```json
{
  "id": 1,
  "filename": "document.pdf",
  "object_name": "uuid-filename.pdf",
  "content_type": "application/pdf",
  "size": 1024000,
  "description": "Government policy document",
  "is_public": false,
  "collection_id": "policies",
  "is_indexed": false,
  "indexed_at": null,
  "created_by": "user123",
  "updated_by": null,
  "created_at": "2023-10-20T14:30:15.123456",
  "access_url": "https://minio.example.com/presigned-url",
  "index_job_id": "2f7a6e2c-9ca4-4d85-9dd7-42e6f4e9e7ad"
}
```

**Side Effects:**
- File stored in MinIO object storage
- Sets `is_indexed=false`, triggers background indexing
- Returns `index_job_id` so clients can poll indexing progress
- Creates audit log entry
```

### Get Document

Retrieve document metadata and access URL.

```http
GET /documents/{document_id}
X-API-Key: your-api-key-here
```

**Response:**
```json
{
  "id": 1,
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "size": 1024000,
  "description": "Government policy document",
  "is_indexed": true,
  "indexed_at": "2023-10-20T15:45:30.123456",
  "created_by": "user123",
  "updated_by": "user456",
  "upload_date": "2023-10-20T14:30:15.123456",
  "access_url": "https://minio.example.com/presigned-url",
  "last_accessed": "2023-10-20T14:30:15.123456"
}
```

### List Documents

Get paginated list of documents.

```http
GET /documents/?skip=0&limit=100
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `skip`: Number of documents to skip (default: 0)
- `limit`: Maximum documents to return (default: 100)

### Update Document

Update document metadata and optionally replace the file.

```http
PUT /documents/{document_id}
Content-Type: multipart/form-data
X-API-Key: your-api-key-here
```

**Form Fields:**
- `file`: Optional new document file to replace existing
- `description`: Optional description text
- `is_public`: Optional boolean visibility flag
- `collection_id`: Optional collection identifier to move document

**Required Permission:** `write`

**Response:**
```json
{
  "id": 1,
  "filename": "updated-document.pdf",
  "object_name": "uuid-filename.pdf",
  "content_type": "application/pdf",
  "size": 2048000,
  "description": "Updated government policy document",
  "is_public": true,
  "collection_id": "updated-policies",
  "is_indexed": false,
  "indexed_at": null,
  "created_by": "user123",
  "updated_by": "user456",
  "upload_date": "2023-10-20T14:30:15.123456",
  "access_url": "https://minio.example.com/presigned-url",
  "index_job_id": "2f7a6e2c-9ca4-4d85-9dd7-42e6f4e9e7ad"
}
```

**Side Effects:**
- If `file` is provided: uploads new file to MinIO, deletes old file, clears vector embeddings by doc_id, sets `is_indexed=false`, triggers background reindexing
- If `collection_id` changes: deletes vectors from old collection, sets `is_indexed=false`, triggers reindexing in new collection
- When a reindex is scheduled, response includes `index_job_id` for progress polling

### Delete Document

Remove a document from storage, database, and vector embeddings.

```http
DELETE /documents/{document_id}
X-API-Key: your-api-key-here
```

**Required Permission:** `delete`

**Response:**
```json
{
  "message": "Document 123 deleted successfully"
}
```

**Side Effects:**
- Deletes vector embeddings by doc_id from ChromaDB
- Removes file from MinIO storage
- Deletes database record
- Creates audit log entry

### Get Document Indexing Status

Get indexing progress for documents in a collection.

```http
GET /documents/indexing-status?collection_id=policies
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `collection_id`: Collection ID to check (required)

**Required Permission:** `read`

**Response:**
```json
{
  "collection_id": "policies",
  "documents_total": 150,
  "indexed": 142,
  "unindexed": 8,
  "progress_percent": 94.7
}
```

### List Document Indexing Jobs

List recent background indexing jobs, optionally filtered by collection.

```http
GET /documents/indexing-jobs?collection_id=policies
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `collection_id`: Optional collection identifier to filter results
- `limit`: Optional maximum number of jobs to return (default 50, max 500)

**Required Permission:** `read`

**Response:**
```json
[
  {
    "job_id": "2f7a6e2c-9ca4-4d85-9dd7-42e6f4e9e7ad",
    "collection_id": "policies",
    "status": "running",
    "documents_total": 25,
    "documents_processed": 10,
    "documents_indexed": 10,
    "progress_percent": 40.0,
    "message": "Indexed 10/25 documents",
    "error": null,
    "created_at": "2025-10-01T09:15:00.123456+00:00",
    "started_at": "2025-10-01T09:15:01.456789+00:00",
    "completed_at": null,
    "updated_at": "2025-10-01T09:16:05.000000+00:00"
  }
]
```

### Get Document Indexing Job

Retrieve the latest status for a specific background indexing job.

```http
GET /documents/indexing-jobs/{job_id}
X-API-Key: your-api-key-here
```

**Required Permission:** `read`

**Response:**
```json
{
  "job_id": "2f7a6e2c-9ca4-4d85-9dd7-42e6f4e9e7ad",
  "collection_id": "policies",
  "status": "completed",
  "documents_total": 25,
  "documents_processed": 25,
  "documents_indexed": 25,
  "progress_percent": 100.0,
  "message": "Indexing completed and cache refreshed",
  "error": null,
  "created_at": "2025-10-01T09:15:00.123456+00:00",
  "started_at": "2025-10-01T09:15:01.456789+00:00",
  "completed_at": "2025-10-01T09:17:45.000000+00:00",
  "updated_at": "2025-10-01T09:17:45.000000+00:00"
}
```

## Web Crawling

### Start Website Crawl

Begin crawling a website in the background.

```http
POST /crawl/
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "url": "https://example.gov",
  "depth": 3,
  "concurrent_requests": 10,
  "follow_external": false,
  "strategy": "breadth_first",
  "collection_id": "gov-website"
}
```

**Parameters:**
- `url`: Starting URL to crawl (required)
- `depth`: Maximum crawl depth (1-10, default: 3)
- `concurrent_requests`: Concurrent requests (1-50, default: 10)
- `follow_external`: Follow external links (default: false)
- `strategy`: "breadth_first" or "depth_first" (default: "breadth_first")
- `collection_id`: Collection identifier for grouping

**Response:**
```json
{
  "task_id": "uuid-task-id",
  "status": "starting",
  "seed_urls": ["https://example.gov"],
  "start_time": "2023-10-20T14:30:15.123456Z",
  "finished": false,
  "collection_id": "gov-website"
}
```

### Get Crawl Status

Check the status of a crawl operation.

```http
GET /crawl/{task_id}
X-API-Key: your-api-key-here
```

**Response:**
```json
{
  "task_id": "uuid-task-id",
  "status": "running",
  "seed_urls": ["https://example.gov"],
  "urls_crawled": 45,
  "total_urls_queued": 120,
  "errors": 2,
  "start_time": "2023-10-20T14:30:15.123456Z",
  "finished": false,
  "collection_id": "gov-website"
}
```

### Fetch Single Webpage

Fetch and convert a single webpage to markdown.

```http
POST /webpages/fetch-webpage/
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "url": "https://example.gov/page",
  "skip_ssl_verification": false
}
```

**Response:**
```json
{
  "url": "https://example.gov/page",
  "content": "# Page Title\n\nPage content in markdown...",
  "title": "Page Title"
}
```

## Webpage Management

### List Webpages

Get paginated list of crawled webpages.

```http
GET /webpages/?skip=0&limit=50
X-API-Key: your-api-key-here
```

### Get Webpage Details

Retrieve detailed information about a webpage.

```http
GET /webpages/{webpage_id}?include_content=true&include_links=false
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `include_content`: Include markdown content (default: true)
- `include_links`: Include incoming/outgoing links (default: false)

### Get Webpages by Collection

List webpages in a specific collection.

```http
GET /webpages/collection/{collection_id}?limit=100&offset=0
X-API-Key: your-api-key-here
```

### Get Webpage by URL

Find a webpage by its URL.

```http
GET /webpages/by-url/?url=https://example.gov/page
X-API-Key: your-api-key-here
```

### Delete Webpage

Remove a webpage from database and vector embeddings.

```http
DELETE /webpages/{webpage_id}
X-API-Key: your-api-key-here
```

**Required Permission:** `delete`

**Response:**
```json
{
  "message": "Webpage 456 deleted successfully"
}
```

**Side Effects:**
- Deletes vector embeddings by doc_id from ChromaDB
- Removes database record
- Creates audit log entry

### Recrawl Webpage

Mark a webpage for recrawling and reprocessing.

```http
POST /webpages/{webpage_id}/recrawl
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Required Permission:** `write`

**Response:**
```json
{
  "message": "Webpage 456 marked for recrawl"
}
```

**Side Effects:**
- Sets `is_indexed=false` and `indexed_at=null`
- Page will be reprocessed in next indexing cycle
- Creates audit log entry

### Extract Text from Collection

Extract text content from webpages in a collection.

```http
POST /webpages/extract-texts/
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "collection_id": "gov-website",
  "hours_ago": 24,
  "output_format": "text"
}
```

**Parameters:**
- `collection_id`: Collection to extract from (required)
- `hours_ago`: Only include pages crawled within N hours (default: 24)
- `output_format`: "text", "json", or "markdown" (default: "text")

## Collection Statistics

### Get Collection Stats

Retrieve statistics for a specific collection.

```http
GET /collection-stats/{collection_id}
X-API-Key: your-api-key-here
```

**Response:**
```json
{
  "collection_id": "gov-website",
  "total_webpages": 156,
  "total_documents": 23,
  "indexed_count": 134,
  "last_crawl": "2023-10-20T14:30:15.123456Z",
  "average_crawl_depth": 2.3,
  "status_codes": {
    "200": 145,
    "404": 8,
    "500": 3
  }
}
```

### Get Collection Indexing Status

Get detailed indexing progress for documents and webpages in a collection.

```http
GET /collection-stats/{collection_id}/indexing-status
X-API-Key: your-api-key-here
```

**Required Permission:** `read`

**Response:**
```json
{
  "collection_id": "gov-website",
  "documents": {
    "total": 23,
    "indexed": 20,
    "unindexed": 3
  },
  "webpages": {
    "total": 156,
    "indexed": 142,
    "unindexed": 14
  },
  "combined": {
    "total": 179,
    "indexed": 162,
    "unindexed": 17,
    "progress_percent": 90.5
  }
}
```

### Get All Collection Stats

Get statistics for all collections.

```http
GET /collection-stats/
X-API-Key: your-api-key-here
```

## Collection Management

Collections represent logical groupings of documents and webpages that power retrieval for specific agencies or topics.

### Create Collection

Create a new collection.

```http
POST /collections/
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "name": "Ministry of Health",
  "description": "Health policies and procedures",
  "type": "mixed"
}
```

**Required Permission:** `write`

**Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Ministry of Health",
  "description": "Health policies and procedures",
  "type": "mixed",
  "created_at": "2023-10-20T14:30:15.123456",
  "updated_at": "2023-10-20T14:30:15.123456",
  "api_key_name": "master",
  "document_count": 0,
  "webpage_count": 0
}
```

**Side Effects:**
- Creates Chroma vector collection
- Auto-refreshes available chat tools
- New collection immediately available for document uploads and chat scoping

### List Collections

Get all collections with counts.

```http
GET /collections/
X-API-Key: your-api-key-here
```

**Required Permission:** `read`

**Response:**
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Ministry of Health",
    "description": "Health policies and procedures",
    "type": "mixed",
    "created_at": "2023-10-20T14:30:15.123456",
    "document_count": 45,
    "webpage_count": 123
  }
]
```

### Get Collection

Get details for a specific collection.

```http
GET /collections/{collection_id}
X-API-Key: your-api-key-here
```

### Update Collection

Update collection metadata.

```http
PUT /collections/{collection_id}
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "name": "Updated Ministry of Health",
  "description": "Updated description"
}
```

**Side Effects:**
- Auto-refreshes chat tools with new metadata
- Updates system prompts for agents

### Delete Collection

Remove a collection and optionally its contents.

```http
DELETE /collections/{collection_id}
X-API-Key: your-api-key-here
```

**Required Permission:** `delete`

**Side Effects:**
- Removes collection from chat tools
- Orphans documents/webpages (sets collection_id to null)
- Auto-refreshes available tools

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Validation Error - Request body validation failed |
| 500 | Internal Server Error - Server error |

### Authentication Errors

```json
{
  "detail": "Missing API key",
  "status_code": 401
}
```

```json
{
  "detail": "Invalid API key",
  "status_code": 401
}
```

```json
{
  "detail": "Insufficient permissions for this operation",
  "status_code": 403
}
```

## Rate Limiting

Currently, no rate limiting is implemented, but it's recommended to:
- Limit concurrent requests to avoid overwhelming the system
- Implement client-side retry logic with exponential backoff
- Monitor your usage through application logs

## Best Practices

1. **Always include the `X-API-Key` header** for authenticated endpoints
2. **Use appropriate HTTP methods** (GET for reading, POST for creating, DELETE for removing)
3. **Handle errors gracefully** with proper HTTP status code checks
4. **Use pagination** for large datasets with `skip` and `limit` parameters
5. **Store API keys securely** and rotate them regularly
6. **Monitor your usage** through logs and trace IDs
7. **Use HTTPS** in production environments
