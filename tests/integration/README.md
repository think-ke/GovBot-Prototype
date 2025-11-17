# GovStack API Integration Test Suite

Comprehensive integration tests for the GovStack API following user story chronology.

## 📋 Overview

This test suite validates all GovStack API endpoints against a live application instance. Tests are organized as user stories covering the complete API surface:

1. **Collections** - Setup and organization
2. **Documents** - Upload, manage, and clean up
3. **Indexing** - Make content searchable
4. **Webpages** - Crawl and manage external content
5. **Web Crawler** - Bulk content crawling
6. **Chat** - Ask questions and retrieve answers
7. **Ratings** - Evaluate chat responses
8. **Audit Logs** - Monitor activity
9. **Transcriptions** - Convert audio to text

## 🏢 Test Organization

**Organization:** Tech Innovators Network (THiNK)  
**Website:** https://think.ke  
**Domain:** think.ke

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- `requests` library
- Access to a running GovStack instance
- Valid API key(s)

### Installation

```bash
# Install dependencies
pip install requests urllib3

# Or use the project's requirements
cd /home/ubuntu/govstack
pip install -r requirements.txt
```

### Configuration

Set up your environment variables in `.env`:

```bash
# Required
GOVSTACK_BASE_URL=http://localhost:5000
GOVSTACK_TEST_API_KEY=your-api-key-here

# Optional
GOVSTACK_ADMIN_API_KEY=your-admin-key-here

# Test behavior flags
SKIP_CRAWL_TESTS=false
SKIP_LONG_RUNNING_TESTS=false
SKIP_CLEANUP=false
```

### Running Tests

#### Using the Shell Script (Recommended)

```bash
cd /home/ubuntu/govstack/tests/integration
./run_tests.sh
```

With options:

```bash
# Skip web crawling tests (faster)
./run_tests.sh --skip-crawl

# Skip long-running tests
./run_tests.sh --skip-long-running

# Keep test data (don't cleanup)
./run_tests.sh --skip-cleanup

# Test against a remote instance
./run_tests.sh --base-url https://api.example.com --api-key your-key

# Combine options
./run_tests.sh --skip-crawl --skip-cleanup --base-url http://localhost:5000
```

#### Using Python Directly

```bash
cd /home/ubuntu/govstack/tests/integration

# Set environment variables
export GOVSTACK_BASE_URL=http://localhost:5000
export GOVSTACK_TEST_API_KEY=your-api-key-here

# Run tests
python3 test_runner.py
```

## 📊 Test Output

### Console Output

Tests produce colorful, user-friendly console output:

```
================================================================================
🧪 Starting Test: Create Collection
================================================================================
📖 User Story: As an admin, I want to create a new collection called 'immigration-faqs'
✅ PASSED: Create Collection - Response: Collection created: abc-123-def
```

### Log Files

Detailed logs are saved to `/home/ubuntu/govstack/logs/`:

- `govstack_integration_tests.log` - Main log file with all test details
- Individual test run logs with timestamps

### Test Summary

At the end of execution, you'll see:

```
--------------------------------------------------------------------------------
📂 TEST EXECUTION SUMMARY
--------------------------------------------------------------------------------
Total Tests: 45
✅ Passed: 42
❌ Failed: 1
⏭️  Skipped: 2
Success Rate: 97.67%
```

## 🧪 Test Structure

### Test Flow

```
1. Health Check
2. Create Collection
3. Upload Document
4. Wait for Indexing
5. Crawl Website
6. Chat with AI
7. Submit Rating
8. Check Audit Logs
9. Cleanup Resources
```

### Test Data Management

The test suite:
- Creates a test collection: `immigration-faqs`
- Uploads a test document: `test_immigration_faq.txt`
- Tracks all created resources in `test_results`
- Cleans up resources at the end (unless `--skip-cleanup`)

### Resource Tracking

The suite tracks:
- `collection_id` - Created test collection
- `document_id` - Uploaded test document
- `webpage_id` - Fetched webpage
- `crawl_task_id` - Started crawl job
- `session_id` - Chat session
- `message_id` - Chat message
- `rating_id` - Submitted rating
- `indexing_job_id` - Background indexing job

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOVSTACK_BASE_URL` | API base URL | `http://localhost:5000` |
| `GOVSTACK_TEST_API_KEY` | API key for testing | *Required* |
| `GOVSTACK_ADMIN_API_KEY` | Admin API key | Uses test key if not set |
| `SKIP_CRAWL_TESTS` | Skip web crawling tests | `false` |
| `SKIP_LONG_RUNNING_TESTS` | Skip long tests | `false` |
| `SKIP_CLEANUP` | Don't delete test data | `false` |
| `REQUEST_TIMEOUT` | HTTP request timeout (seconds) | `30` |
| `MAX_RETRIES` | Max retry attempts | `3` |
| `RETRY_DELAY` | Delay between retries (seconds) | `2` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Test Configuration

Edit `tests/integration/config.py` to customize:

```python
# Test organization details
TEST_ORG_NAME = "Tech Innovators Network (THiNK)"
TEST_ORG_URL = "https://think.ke"

# Collection settings
TEST_COLLECTION_NAME = "immigration-faqs"

# Crawl settings
CRAWL_DEPTH = 2
CRAWL_CONCURRENT_REQUESTS = 5
```

## 📝 Test Coverage

### Complete Endpoint Coverage

#### Collections
- ✅ `POST /collections/` - Create collection
- ✅ `GET /collections/` - List collections
- ✅ `GET /collections/{id}` - Get collection
- ✅ `PUT /collections/{id}` - Update collection
- ✅ `DELETE /collections/{id}` - Delete collection
- ✅ `GET /collection-stats/{id}` - Get statistics

#### Documents
- ✅ `POST /documents/` - Upload document
- ✅ `GET /documents/` - List documents
- ✅ `GET /documents/{id}` - Get document
- ✅ `PATCH /documents/{id}/metadata` - Update metadata
- ✅ `POST /documents/bulk-metadata-update` - Bulk update
- ✅ `GET /documents/collection/{id}` - List by collection
- ✅ `DELETE /documents/{id}` - Delete document

#### Indexing
- ✅ `POST /indexing/trigger` - Trigger indexing
- ✅ `GET /documents/indexing-status` - Get status
- ✅ `GET /documents/indexing-jobs` - List jobs
- ✅ `GET /documents/indexing-jobs/{id}` - Get job status

#### Webpages
- ✅ `POST /webpages/fetch-webpage/` - Fetch webpage
- ✅ `GET /webpages/` - List webpages
- ✅ `GET /webpages/{id}` - Get webpage
- ✅ `GET /webpages/by-url/` - Get by URL
- ✅ `GET /webpages/collection/{id}` - List by collection
- ✅ `POST /webpages/{id}/recrawl` - Recrawl webpage
- ✅ `DELETE /webpages/{id}` - Delete webpage

#### Web Crawler
- ✅ `POST /crawl/` - Start crawl
- ✅ `GET /crawl/` - List crawls
- ✅ `GET /crawl/{task_id}` - Get crawl status

#### Chat
- ✅ `POST /chat/` - Send message
- ✅ `POST /chat/{agency}` - Agency-scoped chat
- ✅ `GET /chat/{session_id}` - Get history
- ✅ `DELETE /chat/{session_id}` - Delete session
- ✅ `GET /chat/events/{session_id}` - Get events
- ✅ `GET /chat/events/{session_id}/latest` - Get latest events

#### Ratings
- ✅ `POST /chat/ratings` - Submit rating
- ✅ `GET /chat/ratings` - List ratings
- ✅ `GET /chat/ratings/{id}` - Get rating
- ✅ `PUT /chat/ratings/{id}` - Update rating
- ✅ `DELETE /chat/ratings/{id}` - Delete rating
- ✅ `GET /chat/ratings/stats` - Get statistics

#### Audit Logs
- ✅ `GET /audit-logs` - List audit logs
- ✅ `GET /audit-logs/summary` - Get summary
- ✅ `GET /audit-logs/user/{user_id}` - User logs
- ✅ `GET /audit-logs/resource/{type}/{id}` - Resource logs

#### Transcriptions
- ⏭️ `POST /transcriptions/` - Upload audio (requires audio file)
- ✅ `GET /transcriptions/` - List transcriptions
- ⏭️ `GET /transcriptions/{id}` - Get transcription (requires ID)

## 🐛 Troubleshooting

### Common Issues

#### 1. API Key Not Set

```
Configuration errors: GOVSTACK_TEST_API_KEY environment variable not set
```

**Solution:** Set your API key in `.env` or export it:
```bash
export GOVSTACK_TEST_API_KEY=your-key-here
```

#### 2. Connection Refused

```
Request failed: GET /health - Connection refused
```

**Solution:** Ensure the GovStack server is running:
```bash
docker compose ps
# or
curl http://localhost:5000/health
```

#### 3. Indexing Timeout

```
⏱️ Indexing job timeout after 120s
```

**Solution:** This is normal for large documents. The test will continue.

#### 4. Crawl Tests Taking Too Long

**Solution:** Skip crawl tests:
```bash
./run_tests.sh --skip-crawl
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
python3 test_runner.py
```

## 📦 File Structure

```
tests/integration/
├── README.md              # This file
├── run_tests.sh          # Test runner script
├── config.py             # Configuration
├── logger.py             # Logging utilities
├── api_client.py         # HTTP client
├── test_runner.py        # Main test suite
└── test_data/            # Test files
    └── test_immigration_faq.txt
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Start GovStack
      run: docker compose up -d
      
    - name: Wait for API
      run: |
        timeout 60 bash -c 'until curl -f http://localhost:5000/health; do sleep 5; done'
    
    - name: Run Integration Tests
      env:
        GOVSTACK_BASE_URL: http://localhost:5000
        GOVSTACK_TEST_API_KEY: ${{ secrets.TEST_API_KEY }}
        SKIP_CRAWL_TESTS: true
      run: |
        cd tests/integration
        ./run_tests.sh
    
    - name: Upload Logs
      if: always()
      uses: actions/upload-artifact@v2
      with:
        name: test-logs
        path: logs/
```

## 📚 Additional Resources

- [GovStack API Reference](../../docs/API_REFERENCE.md)
- [Main README](../../README.md)
- [Think.ke Website](https://think.ke)

## 🤝 Contributing

To add new tests:

1. Add test method to `GovStackTestSuite` class
2. Follow naming convention: `test_<action>_<resource>`
3. Use user story format in docstring
4. Add to `run_all_tests()` method
5. Update this README

## 📄 License

Same as parent GovStack project.

## 💬 Support

For issues or questions:
- Check the logs in `/home/ubuntu/govstack/logs/`
- Review the API documentation
- Contact: support@think.ke
