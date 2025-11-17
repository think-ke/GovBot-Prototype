"""
Configuration for GovStack API Integration Tests
Testing against live application for Tech Innovators Network (THiNK)
Organization URL: https://think.ke
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try to load from parent directory
    load_dotenv()

# Base configuration
BASE_URL = os.getenv("GOVSTACK_BASE_URL", "http://localhost:5000")
API_KEY = os.getenv("GOVSTACK_TEST_API_KEY", "")
ADMIN_API_KEY = os.getenv("GOVSTACK_ADMIN_API_KEY", "")

# Test organization details
TEST_ORG_NAME = "Tech Innovators Network (THiNK)"
TEST_ORG_URL = "https://think.ke"
TEST_ORG_DOMAIN = "think.ke"

# Test data configuration
TEST_COLLECTION_NAME = "immigration-faqs"
TEST_COLLECTION_DESCRIPTION = "Immigration FAQs and related documentation for testing"
TEST_DOCUMENT_DESCRIPTION = "Test document: Immigration FAQs"

# File paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "integration" / "test_data"
TEST_DOCS_DIR = PROJECT_ROOT / "tests" / "test_docs"
TEST_AUDIO_DIR = PROJECT_ROOT / "tests" / "test_audio"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
TEST_DATA_DIR.mkdir(exist_ok=True, parents=True)

# Test files
TEST_PDF_FILE = TEST_DOCS_DIR / "immigration-report.pdf"
TEST_AUDIO_FILE = TEST_AUDIO_DIR / "swahili2.mp3"

# Logging configuration
LOG_FILE = LOGS_DIR / "govstack_integration_tests.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Test execution settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

# Crawl configuration
CRAWL_DEPTH = 2
CRAWL_CONCURRENT_REQUESTS = 5
CRAWL_FOLLOW_EXTERNAL = False
CRAWL_STRATEGY = "breadth_first"

# Test user details
TEST_USER_ID = "test-user-think-integration"
TEST_SESSION_ID: Optional[str] = None  # Will be set during test execution

# Validation flags
SKIP_LONG_RUNNING_TESTS = os.getenv("SKIP_LONG_RUNNING_TESTS", "false").lower() == "true"
SKIP_CRAWL_TESTS = os.getenv("SKIP_CRAWL_TESTS", "false").lower() == "true"
SKIP_CLEANUP = os.getenv("SKIP_CLEANUP", "false").lower() == "true"

# Test result tracking
class TestResults:
    """Container for test results tracking"""
    def __init__(self):
        self.collection_id: Optional[str] = None
        self.document_id: Optional[int] = None
        self.webpage_id: Optional[int] = None
        self.crawl_task_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.message_id: Optional[str] = None
        self.rating_id: Optional[int] = None
        self.indexing_job_id: Optional[str] = None
        self.transcription_id: Optional[int] = None
        
        self.passed: int = 0
        self.failed: int = 0
        self.skipped: int = 0
        self.errors: list = []
        
    def add_pass(self):
        self.passed += 1
        
    def add_fail(self, error: str):
        self.failed += 1
        self.errors.append(error)
        
    def add_skip(self):
        self.skipped += 1
        
    def summary(self) -> dict:
        return {
            "total": self.passed + self.failed + self.skipped,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": f"{(self.passed / (self.passed + self.failed) * 100):.2f}%" if (self.passed + self.failed) > 0 else "N/A",
            "errors": self.errors
        }

# Global test results instance
test_results = TestResults()


def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not API_KEY:
        errors.append("GOVSTACK_TEST_API_KEY environment variable not set")
    
    if not BASE_URL:
        errors.append("GOVSTACK_BASE_URL environment variable not set")
        
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    return True
