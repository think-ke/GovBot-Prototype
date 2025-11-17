#!/bin/bash

# GovStack API Integration Test Runner
# Runs comprehensive integration tests against a live GovStack instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GovStack API Integration Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}Created .env file. Please edit it with your API keys.${NC}"
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Source environment variables
source "$PROJECT_ROOT/.env"

# Check for required environment variables
if [ -z "$GOVSTACK_TEST_API_KEY" ]; then
    if [ -n "$GOVSTACK_API_KEY" ]; then
        export GOVSTACK_TEST_API_KEY="$GOVSTACK_API_KEY"
        echo -e "${GREEN}Using GOVSTACK_API_KEY as test API key${NC}"
    else
        echo -e "${RED}Error: GOVSTACK_TEST_API_KEY or GOVSTACK_API_KEY not set${NC}"
        exit 1
    fi
fi

if [ -z "$GOVSTACK_ADMIN_API_KEY" ]; then
    export GOVSTACK_ADMIN_API_KEY="$GOVSTACK_TEST_API_KEY"
    echo -e "${YELLOW}Warning: Using test API key for admin operations${NC}"
fi

# Set default base URL if not provided
if [ -z "$GOVSTACK_BASE_URL" ]; then
    export GOVSTACK_BASE_URL="http://localhost:5000"
    echo -e "${YELLOW}Using default base URL: $GOVSTACK_BASE_URL${NC}"
fi

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Base URL: $GOVSTACK_BASE_URL"
echo "  API Key: ${GOVSTACK_TEST_API_KEY:0:20}..."
echo "  Logs Directory: $PROJECT_ROOT/logs"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if required Python packages are installed
echo -e "${BLUE}Checking dependencies...${NC}"
python3 -c "import requests" 2>/dev/null || {
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install requests urllib3
}

# Parse command line arguments
SKIP_CRAWL_TESTS=${SKIP_CRAWL_TESTS:-false}
SKIP_LONG_RUNNING_TESTS=${SKIP_LONG_RUNNING_TESTS:-false}
SKIP_CLEANUP=${SKIP_CLEANUP:-false}

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-crawl)
            SKIP_CRAWL_TESTS=true
            shift
            ;;
        --skip-long-running)
            SKIP_LONG_RUNNING_TESTS=true
            shift
            ;;
        --skip-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --base-url)
            GOVSTACK_BASE_URL="$2"
            shift 2
            ;;
        --api-key)
            GOVSTACK_TEST_API_KEY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-crawl              Skip web crawling tests"
            echo "  --skip-long-running       Skip long-running tests"
            echo "  --skip-cleanup            Skip cleanup of test data"
            echo "  --base-url <url>          Set the base URL for the API"
            echo "  --api-key <key>           Set the API key"
            echo "  --help                    Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  GOVSTACK_BASE_URL         Base URL for the API (default: http://localhost:5000)"
            echo "  GOVSTACK_TEST_API_KEY     API key for testing"
            echo "  GOVSTACK_ADMIN_API_KEY    Admin API key (optional)"
            echo "  SKIP_CRAWL_TESTS          Skip crawl tests (true/false)"
            echo "  SKIP_LONG_RUNNING_TESTS   Skip long-running tests (true/false)"
            echo "  SKIP_CLEANUP              Skip cleanup (true/false)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Export variables for Python script
export SKIP_CRAWL_TESTS
export SKIP_LONG_RUNNING_TESTS
export SKIP_CLEANUP

# Show test configuration
echo -e "${BLUE}Test Configuration:${NC}"
echo "  Skip crawl tests: $SKIP_CRAWL_TESTS"
echo "  Skip long-running tests: $SKIP_LONG_RUNNING_TESTS"
echo "  Skip cleanup: $SKIP_CLEANUP"
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Run the tests
echo -e "${GREEN}Starting integration tests...${NC}"
echo ""

cd "$SCRIPT_DIR"

if python3 test_runner.py; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ All tests completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    EXIT_CODE=0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${RED}========================================${NC}"
    EXIT_CODE=1
fi

# Show log file location
echo ""
echo -e "${BLUE}Test logs saved to:${NC}"
echo "  $PROJECT_ROOT/logs/govstack_integration_tests.log"
echo ""

exit $EXIT_CODE
