# GovStack API Integration Test Suite v2

Comprehensive integration tests for the GovStack API, built from actual endpoint implementation analysis.

## Overview

This test suite provides end-to-end integration testing for the GovStack RAG (Retrieval-Augmented Generation) chatbot API. Tests are organized chronologically following the user journey from content ingestion to querying and feedback.

**Test Organization:** Tech Innovators Network (THiNK)  
**Website:** https://think.ke  
**API URL:** https://govstack-api.think.ke/  
**Test Coverage:** 58 endpoints across 9 functional categories

## Quick Start

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install requests python-dotenv
```

### Configuration

1. Create `.env` file in `tests/integration/`:

```bash
# API Configuration
GOVSTACK_BASE_URL=https://govstack-api.think.ke
GOVSTACK_TEST_API_KEY=your-test-key-here
GOVSTACK_ADMIN_API_KEY=your-admin-key-here

# Test Configuration
TEST_COLLECTION_NAME=Test Collection - THiNK Integration Tests
TEST_COLLECTION_DESCRIPTION=Test collection for THiNK integration tests
TEST_ORG_NAME=Tech Innovators Network (THiNK)
TEST_ORG_URL=https://think.ke
TEST_USER_ID=test-user-think-integration
TEST_DOCUMENT_DESCRIPTION=Test immigration FAQ document

# Feature Toggles
SKIP_LONG_RUNNING_TESTS=false
SKIP_CRAWL_TESTS=false
SKIP_CLEANUP=true

# Crawler Configuration
CRAWL_DEPTH=2
CRAWL_CONCURRENT_REQUESTS=5
CRAWL_FOLLOW_EXTERNAL=false
CRAWL_STRATEGY=breadth_first

# Logging
LOG_LEVEL=INFO
```

### Run Tests

```bash
cd /home/ubuntu/govstack/tests/integration

# Run all tests
python test_runner_v2.py

# View logs
tail -f logs/test_run_*.log
```

## Test Structure

### Test Categories

Tests are organized into 9 functional categories following the user journey:

```
0. ✅ Health Check
   └── Verify API is running and accessible

1. 📦 Collections (6 tests)
   ├── Create collection
   ├── List collections  
   ├── Get collection stats
   ├── Update collection
   ├── Get indexing status
   └── Get all collection stats

2. 📄 Documents (8 tests)
   ├── Upload document
   ├── List documents
   ├── Get document details
   ├── Get document metadata
   ├── Update metadata
   ├── Bulk metadata update
   ├── List by collection
   └── Download document

3. 🔄 Indexing (4 tests)
   ├── Trigger indexing
   ├── Get indexing status
   ├── List indexing jobs
   └── Get job status

4. 🌐 Webpages (6 tests)
   ├── Fetch webpage
   ├── List webpages
   ├── Get webpage details
   ├── Get by URL
   ├── List by collection
   └── Recrawl webpage

5. 🕷️ Web Crawler (3 tests)
   ├── Start crawl
   ├── List crawl jobs
   └── Get crawl status

6. 💬 Chat (5 tests)
   ├── Send chat query
   ├── Agency-scoped chat
   ├── Get chat history
   ├── Get chat events
   └── Get latest events

7. ⭐ Ratings (5 tests)
   ├── Submit rating
   ├── List ratings
   ├── Get specific rating
   ├── Update rating
   └── Get rating stats

8. 📋 Audit Logs (4 tests)
   ├── List audit logs
   ├── Get audit summary
   ├── Get user logs
   └── Get resource logs

9. 🎙️ Transcriptions (1 test)
   └── List transcriptions

🧹 Cleanup (5 tests)
   ├── Delete rating
   ├── Delete chat session
   ├── Delete webpage
   ├── Delete document
   └── Delete collection
```

### Test Results

**Current Status:**
```
Total Tests: 58
✅ Passed: 26 (44.8%)
❌ Failed: 21 (36.2%)
⏭️  Skipped: 11 (19.0%)
```

**Known Issues:** See [API_ISSUES_DISCOVERED.md](./API_ISSUES_DISCOVERED.md) for detailed analysis of API bugs discovered during testing.

## File Structure

```
tests/integration/
├── test_runner_v2.py          # Main test suite (1217 lines)
├── config.py                  # Configuration and environment
├── logger.py                  # Logging utilities
├── api_client.py              # HTTP client with retry logic
├── .env                       # Environment variables (gitignored)
├── API_ISSUES_DISCOVERED.md   # Detailed bug report
├── README.md                  # This file
├── logs/                      # Test execution logs
│   └── test_run_*.log
└── test_data/                 # Test fixtures
    └── test_immigration_faq.txt
```

## Test Development Approach

### 1. Source Code Analysis

Tests were built by examining actual endpoint implementations:

```python
# Examined files:
- app/api/fast_api_app.py (2728 lines)
- app/api/endpoints/rating_endpoints.py
- app/api/endpoints/chat_endpoints.py
- app/api/endpoints/audit_endpoints.py
- And more...
```

### 2. Router Structure Discovery

```python
# Discovered router prefixes:
collection_router → /collection-stats
document_router → /documents
webpage_router → /webpages
crawler_router → /crawl
chat_router → /chat
rating_router → /chat  # ⚠️ Conflict!
audit_router → /admin
transcription_router → /transcriptions
```

### 3. Request Model Validation

All test payloads match actual Pydantic models:

```python
# Example: CreateCollectionRequest
{
    "name": str,              # Required
    "description": Optional[str],
    "type": str               # Pattern: documents|webpages|mixed
}
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOVSTACK_BASE_URL` | Required | API base URL |
| `GOVSTACK_TEST_API_KEY` | Required | Read/write API key |
| `GOVSTACK_ADMIN_API_KEY` | Required | Admin API key |
| `TEST_COLLECTION_NAME` | Required | Collection name for tests |
| `TEST_ORG_URL` | Required | Organization website |
| `SKIP_LONG_RUNNING_TESTS` | `false` | Skip tests that take >30s |
| `SKIP_CRAWL_TESTS` | `false` | Skip web crawler tests |
| `SKIP_CLEANUP` | `true` | Skip resource deletion |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Feature Toggles

```python
# In config.py:
SKIP_LONG_RUNNING_TESTS = False  # Indexing, crawling
SKIP_CRAWL_TESTS = False         # Web crawler only
SKIP_CLEANUP = True              # Keep test data
```

## API Client Features

### Automatic Retries

```python
# Exponential backoff with jitter
max_retries = 3
retry_delay = 1.0  # seconds
backoff_factor = 2.0
```

### Response Handling

```python
response = client.get("/endpoint")
if response["ok"]:
    data = response["data"]
else:
    error = response["data"]  # Error details
```

### Utility Methods

```python
# Health check
client.health_check()

# Wait for async jobs
client.wait_for_indexing_job(job_id, max_wait=120)
client.wait_for_crawl_completion(task_id, max_wait=180)
```

## Logging

### Log Levels

- **INFO** - Test execution flow, API responses
- **WARNING** - Skipped tests, non-critical issues
- **ERROR** - Test failures, API errors
- **CRITICAL** - Fatal errors, configuration issues

### Log Output

```
# Console - Simplified format
INFO - ✅ PASSED: List Collections - Response: Found 21 collections
ERROR - ❌ FAILED: Create Collection - 500 Server Error

# File - Detailed format
2025-11-07 03:12:05 - GovStackTests - INFO - [test_runner_v2.py:123] - Starting test: List Collections
2025-11-07 03:12:05 - GovStackTests - INFO - [api_client.py:89] - GET /collection-stats/collections -> 200
```

### Log Files

```bash
# Location
logs/test_run_20251107_031205.log

# Tail logs in real-time
tail -f logs/test_run_*.log

# Search logs
grep "FAILED" logs/test_run_*.log
grep "collection" logs/test_run_*.log
```

## Test Execution Flow

### Typical Test Run

```
1. Configuration validation
2. Health check
3. Collection creation (⚠️ Currently failing)
4. Document upload
5. Indexing trigger and monitoring
6. Webpage fetching
7. Web crawling (optional)
8. Chat queries
9. Rating submission
10. Audit log verification
11. Cleanup (optional)
```

### Dependency Chain

```
Collection → Documents → Indexing
Collection → Webpages → Crawling
Chat → Ratings
All operations → Audit Logs
```

### Failure Handling

- **Critical failures** (health check) → Immediate exit
- **Cascade failures** (collection creation) → Skip dependent tests
- **Individual failures** → Continue with other tests
- **Cleanup failures** → Log and continue

## Known Issues

### Critical (Blocking)

1. **Collection Creation - 500 Error**
   - Endpoint: `POST /collection-stats/`
   - Impact: Blocks 13 dependent tests
   - Status: Server-side issue

2. **Rating Router Conflicts**
   - Endpoints: All `/chat/ratings/*`
   - Impact: Complete rating system broken
   - Root Cause: Multiple routers at `/chat` prefix
   - Status: API design issue

See [API_ISSUES_DISCOVERED.md](./API_ISSUES_DISCOVERED.md) for complete analysis and recommendations.

## Interpreting Results

### Success Indicators

```
✅ Test passes with expected response
⏭️  Test skipped (intentional or missing dependency)
```

### Failure Indicators

```
❌ Test failed with error
ERROR - API Error [status]: Details
ERROR - Request failed: Connection issue
```

### Test Summary

```
--------------------------------------------------------------------------------
📂 TEST EXECUTION SUMMARY
--------------------------------------------------------------------------------
Total Tests: 58
✅ Passed: 26
❌ Failed: 21
⏭️  Skipped: 11
Success Rate: 55.32%
```

## Extending Tests

### Adding New Tests

```python
def test_new_feature(self):
    """GET /endpoint - Description"""
    logger.story("As a user, I want to...")
    
    response = client.get("/endpoint", params={...})
    
    if response["ok"]:
        data = response["data"]
        logger.info(f"✅ Success")
        return {"message": "Success"}
    else:
        raise Exception(f"Failed: {response['data']}")
```

### Test Registration

```python
# In run_all_tests():
logger.section("NEW CATEGORY")
self.run_test("Test Name", self.test_new_feature)
```

### Test Data Storage

```python
# Store for later tests:
self.test_data["resource_id"] = response["data"]["id"]

# Retrieve in dependent tests:
resource_id = self.test_data.get("resource_id")
if not resource_id:
    raise Exception("Resource ID not found")
```

## Troubleshooting

### Common Issues

**"Configuration not valid"**
```bash
# Check .env file exists and has required variables
cat tests/integration/.env
```

**"API health check failed"**
```bash
# Verify API is accessible
curl https://govstack-api.think.ke/health

# Check API keys
echo $GOVSTACK_TEST_API_KEY
```

**"Collection ID not found"**
```bash
# Collection creation is failing (known issue)
# Use existing collection ID from API:
curl -H "X-API-Key: $GOVSTACK_TEST_API_KEY" \
  https://govstack-api.think.ke/collection-stats/collections
```

**"Too many 500 error responses"**
```bash
# Server-side issue
# Check server logs or contact API maintainer
```

### Debug Mode

```python
# In config.py:
LOG_LEVEL = "DEBUG"  # Verbose API request/response logging

# Run single test:
def main():
    suite = GovStackTestSuite()
    suite.run_test("Test Name", suite.test_function)
```

## Best Practices

### Test Independence

- Each test should work independently where possible
- Use `self.test_data` for resource dependencies
- Handle missing dependencies gracefully

### Error Handling

```python
try:
    response = client.get("/endpoint")
    if not response["ok"]:
        raise Exception(f"API Error: {response['data']}")
except HTTPException:
    raise  # Re-raise HTTP errors
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Resource Cleanup

```python
# Store all created resources
self.test_data["collection_id"] = collection_id
self.test_data["document_id"] = document_id

# Clean up in reverse order
if SKIP_CLEANUP:
    return
# Delete document
# Delete collection
```

## Contributing

### Running Tests Locally

```bash
# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
python test_runner_v2.py

# Check results
cat logs/test_run_*.log
```

### Reporting Issues

When reporting test failures, include:
1. Test name and category
2. Error message from logs
3. API response (if available)
4. Test configuration (sanitized)

## API Documentation

- **API Reference:** [docs/API_REFERENCE.md](../../docs/API_REFERENCE.md)
- **Issue Report:** [API_ISSUES_DISCOVERED.md](./API_ISSUES_DISCOVERED.md)
- **Deployment Guide:** [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md)

## Support

- **Issues:** See [API_ISSUES_DISCOVERED.md](./API_ISSUES_DISCOVERED.md)
- **Test Logs:** `tests/integration/logs/`
- **Test Organization:** Tech Innovators Network (THiNK) - https://think.ke

---

**Version:** 2.0  
**Last Updated:** 2025-11-07  
**Test Coverage:** 58 endpoints  
**Success Rate:** 44.8% (26/58 passing) - Limited by API bugs
