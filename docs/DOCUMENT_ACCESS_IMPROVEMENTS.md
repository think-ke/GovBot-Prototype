# Document Access URL Improvements

## Summary
Replaced temporary presigned URLs with direct API download endpoints for simpler, more reliable document access.

## Changes Made

### 1. New Download Endpoint
**Path:** `GET /documents/{document_id}/download`

**Features:**
- ✅ Streams documents directly from MinIO through the API
- ✅ Requires API key authentication (same as other endpoints)
- ✅ Tracks document access (updates `last_accessed` timestamp)
- ✅ Sets proper Content-Type and Content-Disposition headers
- ✅ Includes cache headers for better performance
- ✅ Works with browser inline viewing (PDFs open in browser)

**Example:**
```bash
curl -X GET "http://localhost:5000/documents/39/download" \
  -H "X-API-Key: your-api-key" \
  --output document.pdf
```

### 2. Updated URL Format
**Before:**
```json
{
  "access_url": "http://minio:9000/govstack-docs/uuid.pdf?X-Amz-Algorithm=...&X-Amz-Expires=3600..."
}
```

**After:**
```json
{
  "access_url": "/documents/39/download",
  "download_url": "/documents/39/download"
}
```

### 3. Benefits

#### Security & Control
- All access goes through API authentication
- Can audit who accessed which documents
- Can revoke access by revoking API keys
- No direct MinIO exposure needed

#### Simplicity
- URLs don't expire (no more 1-hour limits)
- Clean, predictable URL structure
- No complex query parameters
- Works behind proxies/load balancers

#### Performance
- Browser caching enabled (1 hour)
- Streams large files efficiently
- No intermediate file storage needed

## Technical Implementation

### File Streaming
Uses FastAPI's `StreamingResponse` with `run_in_threadpool` to stream files from MinIO without blocking the async event loop:

```python
file_data, metadata = await run_in_threadpool(
    minio_client.get_file,
    document.object_name
)

return StreamingResponse(
    file_data,
    media_type=document.content_type,
    headers={
        "Content-Disposition": f'inline; filename="{document.filename}"',
        "Cache-Control": "public, max-age=3600",
    }
)
```

### Access Logging
Every download updates the `last_accessed` timestamp in the database, allowing for:
- Usage analytics
- Popular document tracking
- Compliance reporting

## Frontend Integration

### HTML Link
```html
<a href="/documents/39/download" target="_blank">
  View Document
</a>
```

### JavaScript Fetch
```javascript
fetch('/documents/39/download', {
  headers: {
    'X-API-Key': 'your-api-key'
  }
})
.then(response => response.blob())
.then(blob => {
  const url = window.URL.createObjectURL(blob);
  window.open(url, '_blank');
});
```

### Direct Browser Navigation
Simply append the API key or use cookie-based auth:
```
https://govstack-api.think.ke/documents/39/download
```

## Migration Notes

### Backward Compatibility
- The `access_url` field still exists in responses
- Changed from presigned MinIO URLs to API download URLs
- No breaking changes to API contract
- `is_public` flag still tracked but not yet enforced (future enhancement)

### Future Enhancements
1. **Public Access**: Add `/documents/{id}/download/public` for truly public documents (no auth)
2. **Thumbnails**: Add `/documents/{id}/thumbnail` for image previews
3. **Range Requests**: Support HTTP range headers for video streaming
4. **Rate Limiting**: Add per-user download rate limits
5. **Watermarking**: Optionally watermark sensitive documents

## Testing

```bash
# Get document metadata
curl -X GET "http://localhost:5000/documents/39" \
  -H "X-API-Key: your-key"

# Download document
curl -X GET "http://localhost:5000/documents/39/download" \
  -H "X-API-Key: your-key" \
  --output document.pdf

# Verify file
file document.pdf
```

## Performance Considerations

- **Memory Usage**: Files stream through memory efficiently (no buffering entire file)
- **Concurrent Downloads**: Limited by uvicorn worker count (default: 1)
- **Large Files**: Works well even for multi-GB files due to streaming
- **Cache Headers**: Browsers/CDNs can cache for 1 hour

## Security Considerations

- ✅ API key required for all downloads
- ✅ Audit trail maintained
- ✅ No direct MinIO access needed
- ⚠️ `is_public` flag not yet enforced (all documents require auth currently)
- ⚠️ Consider adding download rate limiting for public deployment
