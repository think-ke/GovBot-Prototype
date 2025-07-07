#!/bin/bash

# GovStack Scalability Testing - script provides easy commands to run various types of tests

# Function to check if the API is accessible
check_api() {
    local url="${EXTERNAL_API_URL:-$API_URL}"
    print_info "Checking if API is accessible at $url..."
    
    if curl -f -s --connect-timeout 10 --max-time 30 "$url/health" > /dev/null; then
        print_success "API is accessible at $url"
    else
        print_warning "API is not accessible at $url"
        print_info "Make sure the server is running and accessible from this machine."
        print_info "For local testing: docker-compose -f docker-compose.dev.yml up -d"
        print_info "For external testing: Check network connectivity and server status"
        
        # Don't exit - let tests try anyway as the health endpoint might not exist
        print_info "Continuing with tests anyway (health endpoint might not be available)..."
    fi
}

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
API_URL="http://localhost:5005"
MAX_USERS=1000
DAILY_USERS=40000
TEST_TYPES="baseline,concurrent,daily_load,stress,memory"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to start the test environment
start_test_env() {
    print_info "Starting test environment..."
    check_docker
    
    cd "$(dirname "$0")"
    
    # Load environment variables
    if [ -f .env.test ]; then
        export $(cat .env.test | grep -v '^#' | grep -v '^$' | grep '=' | sed 's/#.*//' | xargs)
    fi
    
    # Start services
    docker-compose -p govstack-testing -f docker-compose.test.yml up -d
    
    print_success "Test environment started"
    print_info "Services available:"
    echo "  - Test Service UI: http://localhost:8084"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    echo "  - Test Database: localhost:5434"
}

# Function to start external test environment (no local API)
start_external_test_env() {
    print_info "Starting external test environment..."
    check_docker
    
    cd "$(dirname "$0")"
    
    # Load external environment variables
    if [ -f .env.external ]; then
        export $(cat .env.external | grep -v '^#' | grep -v '^$' | grep '=' | sed 's/#.*//' | xargs)
        print_info "Using external API: ${EXTERNAL_API_URL:-not set}"
    else
        print_warning "No .env.external file found. Using defaults."
        export EXTERNAL_API_URL="http://192.168.1.100:5005"
    fi
    
    # Check if external API is accessible
    check_api
    
    # Copy external prometheus config
    cp prometheus.external.yml prometheus.yml
    
    # Start external test services
    docker-compose -p govstack-testing-external -f docker-compose.external.yml up -d
    
    print_success "External test environment started"
    print_info "Services available:"
    echo "  - Test Service UI: http://localhost:8084"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    echo "  - Target API: $EXTERNAL_API_URL"
}

# Function to stop the test environment
stop_test_env() {
    print_info "Stopping test environment..."
    cd "$(dirname "$0")"
    docker-compose -p govstack-testing -f docker-compose.test.yml down
    print_success "Test environment stopped"
}

# Function to stop external test environment
stop_external_test_env() {
    print_info "Stopping external test environment..."
    cd "$(dirname "$0")"
    docker-compose -p govstack-testing-external -f docker-compose.external.yml down
    print_success "External test environment stopped"
}

# Function to run tests using the CLI
run_tests() {
    print_info "Running scalability tests..."
    
    # Parse test types
    IFS=',' read -ra TYPES <<< "$TEST_TYPES"
    
    # Build command
    CMD="python -m tests.cli run"
    
    for type in "${TYPES[@]}"; do
        CMD="$CMD --test $type"
    done
    
    CMD="$CMD --max-users $MAX_USERS --daily-users $DAILY_USERS --api-url $API_URL"
    
    if [ ! -z "$OUTPUT_FILE" ]; then
        CMD="$CMD --output $OUTPUT_FILE"
    fi
    
    if [ "$VERBOSE" = "true" ]; then
        CMD="$CMD --verbose"
    fi
    
    print_info "Executing: $CMD"
    eval $CMD
}

# Function to run a quick check
quick_check() {
    print_info "Running quick performance check..."
    python -m tests.cli quick-check --api-url "$API_URL"
}

# Function to start Locust UI
start_locust() {
    print_info "Starting Locust web UI..."
    python -m tests.cli locust-ui --target "$API_URL"
}

# Function to run unit tests
run_unit_tests() {
    print_info "Running unit tests..."
    python -m pytest tests/unit_tests/ -v
}

# Function to run integration tests
run_integration_tests() {
    print_info "Running integration tests..."
    python -m pytest tests/integration_tests/ -v
}

# Function to clean up test data
cleanup() {
    print_info "Cleaning up test data..."
    
    # Remove test result files
    find . -name "scalability_test_results_*.json" -type f -delete
    find . -name "performance_metrics_*.json" -type f -delete
    find . -name "token_usage_*.json" -type f -delete
    
    # Clean up Docker volumes (optional)
    if [ "$1" = "--volumes" ]; then
        docker-compose -p govstack-testing -f docker-compose.test.yml down -v
        print_info "Docker volumes cleaned"
    fi
    
    print_success "Cleanup completed"
}

# Function to show logs
show_logs() {
    service=${1:-test-service}
    print_info "Showing logs for $service..."
    docker-compose -p govstack-testing -f docker-compose.test.yml logs -f "$service"
}

# Function to show help
show_help() {
    cat << EOF
🚀 GovStack Scalability Testing Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  start-env           Start full test environment (includes local API)
  start-external      Start external test environment (tests remote API)
  stop-env            Stop test environment  
  stop-external       Stop external test environment
  run-tests           Run scalability tests
  quick-check         Run a quick performance check
  unit-tests          Run unit tests
  integration-tests   Run integration tests
  locust-ui           Start Locust web UI for interactive testing
  cleanup             Clean up test result files
  logs [service]      Show logs for a service (default: test-service)
  help                Show this help message

Options:
  --api-url URL       API base URL (default: $API_URL)
  --max-users N       Maximum concurrent users (default: $MAX_USERS)
  --daily-users N     Daily users target (default: $DAILY_USERS)
  --test-types LIST   Comma-separated test types (default: $TEST_TYPES)
  --output FILE       Output file for results
  --verbose           Enable verbose output

Environment Variables:
  EXTERNAL_API_URL    URL of external GovStack API to test
  You can create a .env.test or .env.external file to set default values.

Examples:
  # External server testing
  $0 start-external                               # Start external test environment
  $0 run-tests --api-url http://192.168.1.100:5005 # Test external server
  
  # Local testing  
  $0 start-env                                    # Start test environment
  $0 run-tests --max-users 500                   # Run tests with 500 max users
  $0 quick-check --api-url http://api:5005       # Quick check against Docker API
  $0 run-tests --test-types baseline,concurrent  # Run only specific tests
  $0 cleanup --volumes                           # Clean up including Docker volumes

For more detailed information, see the README.md file.
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --max-users)
            MAX_USERS="$2"
            shift 2
            ;;
        --daily-users)
            DAILY_USERS="$2"
            shift 2
            ;;
        --test-types)
            TEST_TYPES="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="true"
            shift
            ;;
        --volumes)
            CLEANUP_VOLUMES="--volumes"
            shift
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            else
                print_error "Unknown option: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Execute command
case $COMMAND in
    start-env)
        start_test_env
        ;;
    start-external)
        start_external_test_env
        ;;
    stop-env)
        stop_test_env
        ;;
    stop-external)
        stop_external_test_env
        ;;
    run-tests)
        check_api
        run_tests
        ;;
    quick-check)
        check_api
        quick_check
        ;;
    unit-tests)
        run_unit_tests
        ;;
    integration-tests)
        run_integration_tests
        ;;
    locust-ui)
        start_locust
        ;;
    cleanup)
        cleanup $CLEANUP_VOLUMES
        ;;
    logs)
        show_logs $2
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        print_error "No command specified. Use '$0 help' for usage information."
        exit 1
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        print_info "Use '$0 help' for usage information."
        exit 1
        ;;
esac