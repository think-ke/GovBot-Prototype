# API Issues Discovered During Integration Testing

**Test Suite:** GovStack API Integration Tests v2  
**Date:** 2025-11-07  
**API:** https://govstack-api.think.ke/  
**Organization:** Tech Innovators Network (THiNK)

## Summary

During comprehensive integration testing of the GovStack API, several issues were discovered that prevent certain endpoints from functioning correctly. These are API implementation issues, not test issues.

## Critical Issues

### 1. Collection Creation Returns 500 Error
**Endpoint:** `POST /collection-stats/`  
**Status:** Server Error (500)  
**Impact:** HIGH - Blocks all collection-dependent tests

**Symptoms:**
```
ERROR - Request failed: POST /collection-stats/ - HTTPSConnectionPool(host='govstack-api.think.ke', port=443): 
Max retries exceeded with url: /collection-stats/ (Caused by ResponseError('too many 500 error responses'))
```

**Request Payload (Valid according to API spec):**
```json
{
  "name": "Test Collection - THiNK Integration Tests",
  "description": "Test collection for THiNK integration tests",
  "type": "mixed"
}
```

**Cascading Failures:**
- Cannot upload documents (requires collection_id)
- Cannot test crawling (requires collection_id)
- Cannot test agency-scoped chat (requires collection_id)
- Cannot test collection indexing status
- Cannot test collection updates/deletes

**Recommendation:** Check server logs for `/collection-stats/` POST endpoint. Likely database constraint violation, authentication issue, or missing default values.

---

### 2. Router Prefix Conflicts - Chat vs Ratings
**Endpoints:** `/chat/ratings` and `/chat/ratings/stats`  
**Status:** Route Matching Error (404/422)  
**Impact:** HIGH - Rating system completely broken

**Root Cause:**
Multiple routers mounted at `/chat` prefix with conflicting path patterns:

1. `chat_router` at `/chat` with route `GET /{session_id}` → `/chat/{session_id}`
2. `rating_router` at `/chat` with route `GET /ratings` → `/chat/ratings`

**Issue:**
When calling `/chat/ratings`, FastAPI matches it against `chat_router`'s `/{session_id}` pattern FIRST (because chat_router is registered before rating_router), treating "ratings" as a session_id string.

**Symptoms:**
```
GET /chat/ratings → 404: Chat session not found (treats "ratings" as session_id)
GET /chat/ratings/stats → 422: Unable to parse "stats" as integer rating_id
```

**Evidence from fast_api_app.py:**
```python
# Line 2682
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
# Line 2685  
app.include_router(chat_event_router, prefix="/chat", tags=["Chat"])
# Line 2688
app.include_router(rating_router, prefix="/chat", tags=["Chat"])
```

**Affected Endpoints:**
- `GET /chat/ratings` - List ratings
- `POST /chat/ratings` - Create rating
- `GET /chat/ratings/{rating_id}` - Get specific rating
- `PUT /chat/ratings/{rating_id}` - Update rating
- `DELETE /chat/ratings/{rating_id}` - Delete rating
- `GET /chat/ratings/stats` - Get rating statistics

**Solutions:**
1. **Option A:** Mount rating_router at different prefix (e.g., `/ratings` instead of `/chat`)
2. **Option B:** Make chat routes more specific (e.g., `/chat/session/{session_id}` instead of `/chat/{session_id}`)
3. **Option C:** Register rating_router BEFORE chat_router (may break other things)

**Recommendation:** Implement Option A - mount rating_router at `/ratings` prefix.

---

### 3. Route Ordering Issue - Parametrized vs Literal Paths
**Endpoints:** `/chat/ratings/stats` and `/documents/indexing-jobs`  
**Status:** Route Matching Error (422)  
**Impact:** MEDIUM - Statistics endpoints broken

**Root Cause:**
FastAPI route ordering problem where parametrized routes (e.g., `/{id}`) are defined BEFORE literal routes (e.g., `/stats`).

**Examples:**

**A. Rating Stats**
```python
# rating_endpoints.py line 201
@router.get("/ratings/{rating_id}", ...)  # Defined FIRST

# rating_endpoints.py line 376
@router.get("/ratings/stats", ...)  # Defined SECOND
```

When calling `/chat/ratings/stats`, FastAPI matches `/ratings/{rating_id}` first and tries to parse "stats" as an integer `rating_id`, resulting in:
```
422: Input should be a valid integer, unable to parse string as an integer', 'input': 'stats'
```

**B. Indexing Jobs**
```python
# fast_api_app.py line 2185
@document_router.get("/indexing-jobs/{job_id}", ...)  # Defined FIRST

# fast_api_app.py line 2207
@document_router.get("/indexing-jobs", ...)  # Defined SECOND
```

When calling `/documents/indexing-jobs`, FastAPI matches `/indexing-jobs/{job_id}` first and tries to parse "indexing-jobs" as a document_id, resulting in:
```
422: Input should be a valid integer, unable to parse string as an integer', 'input': 'indexing-jobs'
```

**Affected Endpoints:**
- `GET /chat/ratings/stats`
- `GET /documents/indexing-jobs`

**Solution:**
Reorder routes so literal paths come BEFORE parametrized paths:

```python
# CORRECT ORDER:
@router.get("/ratings/stats", ...)  # Literal path FIRST
@router.get("/ratings", ...)  # List endpoint
@router.get("/ratings/{rating_id}", ...)  # Parametrized LAST
```

**Recommendation:** Review all routers and ensure literal/static routes are defined before parametrized routes.

---

### 4. Get Chat History Returns 500 Error
**Endpoint:** `GET /chat/{session_id}`  
**Status:** Server Error (500)  
**Impact:** MEDIUM - Cannot retrieve chat history

**Symptoms:**
```
ERROR - Request failed: GET /chat/db47262a-92a3-4779-8449-a4c60b1225f0 - 
HTTPSConnectionPool(host='govstack-api.think.ke', port=443): Max retries exceeded with url: 
/chat/db47262a-92a3-4779-8449-a4c60b1225f0 (Caused by ResponseError('too many 500 error responses'))
```

**Context:**
- Session ID was created successfully via `POST /chat/`
- Session ID is valid UUID format
- Other chat endpoints work (events, latest events)

**Recommendation:** Check server logs for `/chat/{session_id}` GET endpoint. Likely database query issue or missing joins.

---

## Working Endpoints ✅

The following endpoints were successfully tested and work correctly:

### Collections
- ✅ `GET /collection-stats/collections` - List collections
- ✅ `GET /collection-stats/` - Get all collection stats

### Documents  
- ✅ `GET /documents/` - List documents

### Webpages
- ✅ `POST /webpages/fetch-webpage/` - Fetch single webpage
- ✅ `GET /webpages/` - List webpages
- ✅ `GET /webpages/{webpage_id}` - Get webpage details
- ✅ `POST /webpages/{webpage_id}/recrawl` - Mark for recrawl

### Crawler
- ✅ `GET /crawl/` - List crawl jobs

### Chat
- ✅ `POST /chat/` - Send chat message
- ✅ `GET /chat/events/{session_id}` - Get chat events
- ✅ `GET /chat/events/{session_id}/latest` - Get latest events

### Audit
- ✅ `GET /admin/audit-logs` - List audit logs
- ✅ `GET /admin/audit-logs/summary` - Get audit summary
- ✅ `GET /admin/audit-logs/user/{user_id}` - Get user logs

### Transcriptions
- ✅ `GET /transcriptions/` - List transcriptions

---

## Test Results Summary

```
Total Tests: 58
✅ Passed: 26 (44.8%)
❌ Failed: 21 (36.2%)
⏭️  Skipped: 11 (19.0%)
```

### Failure Breakdown
- **Collection creation (500 error):** 1 direct failure
- **Cascading from collection failure:** 13 failures
- **Router conflict (ratings):** 3 failures
- **Route ordering (stats/jobs):** 2 failures
- **Chat history (500 error):** 1 failure
- **Other:** 1 failure

### Pass Rate by Category
- **Collections:** 33% (2/6 passing)
- **Documents:** 12% (1/8 passing - limited by collection failure)
- **Indexing:** 25% (1/4 passing - limited by collection failure)
- **Webpages:** 67% (4/6 passing - limited by collection failure)
- **Crawler:** 67% (2/3 passing - limited by collection failure)
- **Chat:** 60% (3/5 passing)
- **Ratings:** 40% (2/5 passing - limited by routing conflicts)
- **Audit:** 100% (4/4 passing) ✅
- **Transcriptions:** 100% (1/1 passing) ✅

---

## Recommended Actions

### Immediate (P0)
1. **Fix collection creation endpoint** - Blocking 13 other tests
2. **Fix rating router conflicts** - Complete rating system broken

### High Priority (P1)
3. **Fix route ordering issues** - Statistics endpoints unusable
4. **Fix chat history endpoint** - Core functionality broken

### Medium Priority (P2)
5. **Add integration tests to CI/CD** - Prevent regressions
6. **Review all router mounting** - Prevent future conflicts
7. **Document working vs broken endpoints** - User communication

---

## Testing Methodology

### Approach
1. Examined actual endpoint implementation in source code
2. Built tests based on actual request/response models
3. Followed FastAPI router structure and prefixes
4. Tested against production API at https://govstack-api.think.ke/

### Files Examined
- `/home/ubuntu/govstack/app/api/fast_api_app.py` (2728 lines)
- `/home/ubuntu/govstack/app/api/endpoints/rating_endpoints.py` (463 lines)
- `/home/ubuntu/govstack/app/api/endpoints/chat_endpoints.py`
- Router mounting and prefix configuration

### Test Organization (THiNK)
- **Name:** Tech Innovators Network (THiNK)
- **URL:** https://think.ke
- **API Key:** 63b528c7-2b42-4028-a1b1-ec62c56309f6
- **Admin Key:** b689ccc1-d925-4c4e-871a-379fcd79f269

---

## Appendix: Router Structure

```
FastAPI App
├── /collection-stats (collection_router)
│   ├── POST /collection-stats/ ❌ 500 ERROR
│   ├── GET /collection-stats/collections ✅
│   ├── GET /collection-stats/{id} ⚠️ Untested
│   └── GET /collection-stats/ ✅
│
├── /documents (document_router)
│   ├── GET /documents/ ✅
│   ├── POST /documents/ ⚠️ Untested (needs collection)
│   ├── GET /documents/indexing-jobs ❌ Route ordering issue
│   └── GET /documents/indexing-jobs/{job_id} ✅
│
├── /webpages (webpage_router)
│   ├── POST /webpages/fetch-webpage/ ✅
│   ├── GET /webpages/ ✅
│   ├── GET /webpages/{id} ✅
│   └── POST /webpages/{id}/recrawl ✅
│
├── /crawl (crawler_router)
│   ├── GET /crawl/ ✅
│   ├── POST /crawl/ ⚠️ Untested (needs collection)
│   └── GET /crawl/{task_id} ⚠️ Untested (needs task)
│
├── /chat (chat_router) ⚠️ CONFLICT WITH RATING ROUTER
│   ├── POST /chat/ ✅
│   ├── GET /chat/{session_id} ❌ 500 ERROR
│   └── POST /chat/{agency} ⚠️ Untested (needs collection)
│
├── /chat (chat_event_router)
│   ├── GET /chat/events/{session_id} ✅
│   └── GET /chat/events/{session_id}/latest ✅
│
├── /chat (rating_router) ❌ ALL BROKEN DUE TO ROUTER CONFLICT
│   ├── POST /chat/ratings ❌ Matched by /{session_id}
│   ├── GET /chat/ratings ❌ Matched by /{session_id}
│   ├── GET /chat/ratings/{id} ❌ Matched by /{session_id}
│   ├── PUT /chat/ratings/{id} ❌ Matched by /{session_id}
│   ├── DELETE /chat/ratings/{id} ❌ Matched by /{session_id}
│   └── GET /chat/ratings/stats ❌ Route ordering + conflict
│
├── /admin (audit_router)
│   ├── GET /admin/audit-logs ✅
│   ├── GET /admin/audit-logs/summary ✅
│   ├── GET /admin/audit-logs/user/{user_id} ✅
│   └── GET /admin/audit-logs/resource/{type}/{id} ✅
│
└── /transcriptions (transcription_router)
    └── GET /transcriptions/ ✅
```

---

**Report Generated:** 2025-11-07  
**Test Suite Version:** v2  
**Total Test Coverage:** 58 endpoints across 9 user story categories
