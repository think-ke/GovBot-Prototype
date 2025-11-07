"""
Logging utilities for GovStack API Integration Tests
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOGS_DIR


class TestLogger:
    """Custom logger for integration tests with both file and console output"""
    
    def __init__(self, name: str = "GovStackTests"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # File handler - detailed logs
        file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler - user-friendly output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def info(self, msg: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(msg, *args, **kwargs)
        
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(msg, *args, **kwargs)
        
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(msg, *args, **kwargs)
        
    def error(self, msg: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(msg, *args, **kwargs)
        
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(msg, *args, **kwargs)
        
    def test_start(self, test_name: str):
        """Log the start of a test"""
        separator = "=" * 80
        self.logger.info(f"\n{separator}")
        self.logger.info(f"🧪 Starting Test: {test_name}")
        self.logger.info(separator)
        
    def test_pass(self, test_name: str, details: Optional[str] = None):
        """Log a test pass"""
        msg = f"✅ PASSED: {test_name}"
        if details:
            msg += f" - {details}"
        self.logger.info(msg)
        
    def test_fail(self, test_name: str, reason: str):
        """Log a test failure"""
        self.logger.error(f"❌ FAILED: {test_name} - {reason}")
        
    def test_skip(self, test_name: str, reason: str):
        """Log a test skip"""
        self.logger.warning(f"⏭️  SKIPPED: {test_name} - {reason}")
        
    def story(self, story: str):
        """Log a user story"""
        self.logger.info(f"\n📖 User Story: {story}")
        
    def api_request(self, method: str, endpoint: str, status_code: Optional[int] = None):
        """Log an API request"""
        if status_code:
            self.logger.debug(f"🌐 {method} {endpoint} -> {status_code}")
        else:
            self.logger.debug(f"🌐 {method} {endpoint}")
            
    def api_response(self, data: dict, truncate: bool = True):
        """Log API response data"""
        if truncate and isinstance(data, dict):
            # Log only key fields for readability
            summary = {k: v for k, v in list(data.items())[:5]}
            self.logger.debug(f"📥 Response: {summary}")
        else:
            self.logger.debug(f"📥 Response: {data}")
            
    def section(self, title: str):
        """Log a section separator"""
        separator = "-" * 80
        self.logger.info(f"\n{separator}")
        self.logger.info(f"📂 {title}")
        self.logger.info(separator)


def create_test_run_log():
    """Create a separate log file for this test run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_log = LOGS_DIR / f"test_run_{timestamp}.log"
    
    return run_log


# Create global logger instance
logger = TestLogger()


def log_test_summary(results: dict):
    """Log test execution summary"""
    logger.section("TEST EXECUTION SUMMARY")
    logger.info(f"Total Tests: {results['total']}")
    logger.info(f"✅ Passed: {results['passed']}")
    logger.info(f"❌ Failed: {results['failed']}")
    logger.info(f"⏭️  Skipped: {results['skipped']}")
    logger.info(f"Success Rate: {results['success_rate']}")
    
    if results['errors']:
        logger.section("ERRORS ENCOUNTERED")
        for i, error in enumerate(results['errors'], 1):
            logger.error(f"{i}. {error}")
