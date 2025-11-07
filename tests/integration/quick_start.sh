#!/bin/bash

# Quick Start Script for GovStack Integration Tests
# This script helps you set up and run the tests quickly

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    GovStack API Integration Test Suite - Quick Start         ║
║    Testing Organization: Tech Innovators Network (THiNK)     ║
║    Website: https://think.ke                                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$(echo -e ${YELLOW}$prompt [${GREEN}$default${YELLOW}]: ${NC})" input
        eval "$var_name=\${input:-$default}"
    else
        read -p "$(echo -e ${YELLOW}$prompt: ${NC})" input
        eval "$var_name=\"$input\""
    fi
}

echo -e "${BLUE}Step 1: Configuration Setup${NC}"
echo ""

# Check if .env exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${GREEN}Found existing .env file${NC}"
    source "$PROJECT_ROOT/.env"
    
    # Check for API keys
    if [ -n "$GOVSTACK_API_KEY" ]; then
        DEFAULT_API_KEY="$GOVSTACK_API_KEY"
    fi
    if [ -n "$GOVSTACK_ADMIN_API_KEY" ]; then
        DEFAULT_ADMIN_KEY="$GOVSTACK_ADMIN_API_KEY"
    fi
else
    echo -e "${YELLOW}No .env file found${NC}"
fi

# Prompt for configuration
echo ""
prompt_input "Enter GovStack API Base URL" "http://localhost:5000" BASE_URL
prompt_input "Enter API Key" "${DEFAULT_API_KEY}" API_KEY

if [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: API Key is required${NC}"
    exit 1
fi

prompt_input "Enter Admin API Key (press Enter to use same as API Key)" "" ADMIN_KEY
if [ -z "$ADMIN_KEY" ]; then
    ADMIN_KEY="$API_KEY"
fi

# Test behavior options
echo ""
echo -e "${BLUE}Step 2: Test Options${NC}"
echo ""

read -p "$(echo -e ${YELLOW}Skip web crawling tests? [y/N]: ${NC})" skip_crawl
SKIP_CRAWL=${skip_crawl:-n}

read -p "$(echo -e ${YELLOW}Skip long-running tests? [y/N]: ${NC})" skip_long
SKIP_LONG=${skip_long:-n}

read -p "$(echo -e ${YELLOW}Keep test data after completion? [y/N]: ${NC})" keep_data
KEEP_DATA=${keep_data:-n}

# Export variables
export GOVSTACK_BASE_URL="$BASE_URL"
export GOVSTACK_TEST_API_KEY="$API_KEY"
export GOVSTACK_ADMIN_API_KEY="$ADMIN_KEY"

if [[ "$SKIP_CRAWL" =~ ^[Yy]$ ]]; then
    export SKIP_CRAWL_TESTS=true
else
    export SKIP_CRAWL_TESTS=false
fi

if [[ "$SKIP_LONG" =~ ^[Yy]$ ]]; then
    export SKIP_LONG_RUNNING_TESTS=true
else
    export SKIP_LONG_RUNNING_TESTS=false
fi

if [[ "$KEEP_DATA" =~ ^[Yy]$ ]]; then
    export SKIP_CLEANUP=true
else
    export SKIP_CLEANUP=false
fi

# Health check
echo ""
echo -e "${BLUE}Step 3: Health Check${NC}"
echo ""
echo -e "${YELLOW}Checking if API is accessible...${NC}"

if command -v curl &> /dev/null; then
    if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is healthy and accessible${NC}"
    else
        echo -e "${RED}⚠️  Warning: Cannot reach API at $BASE_URL${NC}"
        read -p "$(echo -e ${YELLOW}Continue anyway? [y/N]: ${NC})" continue
        if [[ ! "$continue" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}curl not available, skipping health check${NC}"
fi

# Install dependencies
echo ""
echo -e "${BLUE}Step 4: Dependencies${NC}"
echo ""

if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install -q requests urllib3 || {
        echo -e "${RED}Failed to install dependencies${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Test Configuration Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "  Base URL:              ${GREEN}$BASE_URL${NC}"
echo -e "  API Key:               ${GREEN}${API_KEY:0:20}...${NC}"
echo -e "  Skip Crawl Tests:      ${GREEN}$SKIP_CRAWL_TESTS${NC}"
echo -e "  Skip Long Tests:       ${GREEN}$SKIP_LONG_RUNNING_TESTS${NC}"
echo -e "  Keep Test Data:        ${GREEN}$SKIP_CLEANUP${NC}"
echo -e "  Log Directory:         ${GREEN}$PROJECT_ROOT/logs${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Confirm and run
read -p "$(echo -e ${YELLOW}Ready to run tests? [Y/n]: ${NC})" confirm
confirm=${confirm:-y}

if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${GREEN}Starting test execution...${NC}"
    echo ""
    sleep 1
    
    cd "$SCRIPT_DIR"
    
    if python3 test_runner.py; then
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ Tests completed successfully!${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "${BLUE}📊 View detailed logs at:${NC}"
        echo -e "   ${GREEN}$PROJECT_ROOT/logs/govstack_integration_tests.log${NC}"
        echo ""
    else
        echo ""
        echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
        echo -e "${RED}❌ Some tests failed${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "${BLUE}📊 Check logs for details:${NC}"
        echo -e "   ${YELLOW}$PROJECT_ROOT/logs/govstack_integration_tests.log${NC}"
        echo ""
        exit 1
    fi
else
    echo ""
    echo -e "${YELLOW}Test execution cancelled${NC}"
    echo ""
    echo -e "${BLUE}To run tests later, use:${NC}"
    echo -e "   cd $SCRIPT_DIR"
    echo -e "   ./run_tests.sh"
    echo ""
fi
