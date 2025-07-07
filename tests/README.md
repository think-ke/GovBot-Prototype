# GovStack Scalability Testing Suite

This comprehensive testing suite is designed to evaluate the GovStack API's performance, scalability, and reliability under various load conditions. It can simulate up to 1000 concurrent users and 40,000 daily users to help you understand how your system performs at scale.

## 🎯 What This Tests

### Load Testing Scenarios
- **Baseline Performance**: Single-user performance metrics
- **Concurrent Users**: 10, 25, 50, 100, 250, 500, 1000 concurrent users
- **Daily Load Simulation**: Realistic usage patterns throughout the day
- **Stress Testing**: Push the system to its limits
- **Memory & Latency Analysis**: Track resource usage and response times

### Key Metrics Measured
- **Response Times**: Average, median, P95, P99, max
- **Success Rates**: Request success/failure ratios
- **Memory Usage**: RAM consumption patterns
- **Token Usage**: OpenAI API costs and projections
- **Throughput**: Requests per second
- **Latency**: Network and processing delays

## 🚀 Quick Start & Setup

### Step 1: Prerequisites & System Requirements

#### Required Software
```bash
# Docker & Docker Compose (recommended method)
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER  # Add user to docker group
# Log out and back in for group changes to take effect

# OR Python environment (manual setup)
python3 --version  # Requires Python 3.8+
pip3 install -r requirements.txt
```

#### System Resources
- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB RAM, 4 CPU cores
- **For 1000+ concurrent users**: 16GB RAM, 8 CPU cores
- **Disk Space**: 2GB free space for Docker images and test data

### Step 2: Environment Setup

#### Clone and Navigate
```bash
cd /path/to/your/govstack
cd tests/
```

#### Configure Environment
```bash
# Copy the example environment file
cp .env.test.example .env.test

# Edit the configuration file
nano .env.test

# Essential settings to configure:
# API_BASE_URL=http://localhost:5005
# MAX_USERS=1000
# DAILY_USERS=40000
# POSTGRES_PASSWORD=your_secure_password
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
```

### Step 3: Start the Main GovStack API

Before running tests, ensure the main GovStack API is running:

```bash
# Option A: Start from the project root
cd ../  # Go to govstack root directory
docker-compose -f docker-compose.dev.yml up -d

# Option B: Start API only
docker-compose -f docker-compose.dev.yml up -d api postgres chroma minio

# Verify API is running
curl http://localhost:5005/health
```

### Step 4: Launch the Testing Environment

#### Method A: Full Docker Environment (Recommended)
```bash
# Navigate to tests directory
cd tests/

# Start complete test environment with monitoring
./run_tests.sh start-env

# This will start:
# - Test Service API (http://localhost:8084)
# - Prometheus Monitoring (http://localhost:9090) 
# - Grafana Dashboard (http://localhost:3000)
# - Test Database (localhost:5434)
```

#### Method B: Manual Python Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the test microservice manually
python -m tests.cli service --port 8084 --host 0.0.0.0
```

### Step 5: Verify Setup

#### Check All Services
```bash
# Check if all services are running
docker-compose -f docker-compose.test.yml ps

# Expected output should show:
# - api (healthy)
# - test-service (running)
# - postgres-test (healthy) 
# - chroma-test (running)
# - minio-test (running)
# - prometheus (running)
# - grafana (running)
```

#### Test API Connectivity
```bash
# Quick connectivity test
./run_tests.sh quick-check

# Manual API test
curl -X POST http://localhost:5005/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What services does the government provide?", "collection_id": "govstack-docs"}'
```

### Step 6: Access Test Interfaces

#### Web-Based Test Dashboard
```bash
# Open test service UI
open http://localhost:8084

# Available endpoints:
# GET  /health              - Service health check
# POST /tests/run           - Start test execution
# GET  /tests/{id}/status   - Check test progress
# GET  /tests/{id}/results  - Get test results
# GET  /docs                - API documentation
```

#### Monitoring Dashboards
```bash
# Prometheus Metrics
open http://localhost:9090

# Grafana Dashboards (login: admin/admin)
open http://localhost:3000

# Import pre-configured dashboards from:
# tests/monitoring/grafana-dashboards/
```

### Step 7: Run Your First Tests

#### Simple Test Run
```bash
# Run all tests with default settings
./run_tests.sh run-tests

# Quick performance check (single request test)
./run_tests.sh quick-check
```

#### Interactive Testing with Locust
```bash
# Start Locust web UI for manual testing
./run_tests.sh locust-ui

# Access Locust UI at http://localhost:8089
# Configure users and spawn rate through the web interface
```

#### Custom Test Configuration
```bash
# Test with specific parameters
./run_tests.sh run-tests \
  --max-users 500 \
  --daily-users 20000 \
  --test-types baseline,concurrent \
  --api-url http://localhost:5005

# Run only specific test types
./run_tests.sh run-tests --test-types baseline,stress

# Generate detailed output
./run_tests.sh run-tests --verbose --output results_$(date +%Y%m%d).json
```

## 📋 Prerequisites

### Required Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use the Docker approach (no local Python setup needed)
```

### Environment Setup
```bash
# Copy and customize the environment file
cp .env.test.example .env.test
# Edit .env.test with your settings
```

### Required Services
- **GovStack API**: Your main API must be running
- **Database**: PostgreSQL for test data
- **Vector DB**: ChromaDB for embeddings
- **Object Storage**: MinIO for file storage

## 🛠️ Usage Guide

### Command Line Interface

#### Run All Tests
```bash
python -m tests.cli run \
  --max-users 1000 \
  --daily-users 40000 \
  --api-url http://localhost:5005 \
  --output results.json
```

#### Quick Health Check
```bash
python -m tests.cli quick-check --api-url http://localhost:5005
```

#### Start Test Microservice
```bash
python -m tests.cli service --port 8084 --host 0.0.0.0
```

#### Interactive Locust UI
```bash
python -m tests.cli locust-ui --target http://localhost:5005
```

### Bash Script Interface

```bash
# Start test environment
./run_tests.sh start-env

# Run performance tests
./run_tests.sh run-tests --max-users 500

# Run unit tests
./run_tests.sh unit-tests

# Run integration tests
./run_tests.sh integration-tests

# Clean up
./run_tests.sh cleanup --volumes
```

## 📡 Test Service API Reference

The testing module includes a RESTful API service for remote test execution and monitoring.

### Starting the Test Service

#### Docker Method (Recommended)
```bash
# Start complete environment including test service
./run_tests.sh start-env

# Service available at http://localhost:8084
```

#### Standalone Method
```bash
# Start only the test service
python -m tests.cli service --port 8084 --host 0.0.0.0

# With custom configuration
python -m tests.cli service \
  --port 8084 \
  --host 0.0.0.0 \
  --api-url http://localhost:5005 \
  --max-users 1000
```

### API Endpoints

#### Health Check
```bash
# Check service health
curl http://localhost:8084/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-06-24T10:30:00Z",
  "version": "1.0.0",
  "api_connectivity": true
}
```

#### Start Test Run
```bash
# Start a comprehensive test run
curl -X POST http://localhost:8084/tests/run \
  -H "Content-Type: application/json" \
  -d '{
    "test_types": ["baseline", "concurrent", "daily_load"],
    "max_users": 1000,
    "daily_users": 40000,
    "spawn_rate": 10,
    "test_duration": 300,
    "api_url": "http://localhost:5005"
  }'

# Response:
{
  "test_id": "test_20250624_103000_abc123",
  "status": "started",
  "estimated_duration": 1800,
  "message": "Test run initiated successfully"
}
```

#### Check Test Status
```bash
# Get test execution status
curl http://localhost:8084/tests/{test_id}/status

# Response:
{
  "test_id": "test_20250624_103000_abc123",
  "status": "running",
  "progress": {
    "current_phase": "concurrent_users",
    "completed_phases": ["baseline"],
    "remaining_phases": ["daily_load", "stress", "memory"],
    "percent_complete": 35,
    "current_users": 250,
    "elapsed_time": 630,
    "estimated_remaining": 1170
  },
  "current_metrics": {
    "avg_response_time": 1850.5,
    "success_rate": 0.97,
    "requests_per_second": 18.5,
    "active_users": 250
  }
}
```

#### Get Test Results
```bash
# Retrieve complete test results
curl http://localhost:8084/tests/{test_id}/results

# Download results as file
curl http://localhost:8084/tests/{test_id}/results/download \
  -o test_results.json
```

#### List All Tests
```bash
# Get list of all test runs
curl http://localhost:8084/tests

# With filtering
curl "http://localhost:8084/tests?status=completed&limit=10"

# Response:
{
  "tests": [
    {
      "test_id": "test_20250624_103000_abc123",
      "status": "completed",
      "started_at": "2025-06-24T10:30:00Z",
      "completed_at": "2025-06-24T11:00:00Z",
      "duration": 1800,
      "test_types": ["baseline", "concurrent"],
      "max_users": 1000,
      "summary": {
        "overall_success_rate": 0.96,
        "avg_response_time": 1950.2,
        "total_requests": 15420
      }
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 10
}
```

#### Stop Test Run
```bash
# Stop a running test
curl -X POST http://localhost:8084/tests/{test_id}/stop

# Response:
{
  "test_id": "test_20250624_103000_abc123",
  "status": "stopping",
  "message": "Test stop initiated"
}
```

#### Get System Metrics
```bash
# Current system metrics
curl http://localhost:8084/metrics/system

# Response:
{
  "cpu_usage": 45.2,
  "memory_usage": 68.5,
  "disk_usage": 23.1,
  "network_io": {
    "bytes_sent": 1048576,
    "bytes_received": 2097152
  },
  "docker_stats": {
    "containers_running": 7,
    "images": 12,
    "volumes": 8
  }
}
```

#### Test Configuration Templates
```bash
# Get available test templates
curl http://localhost:8084/templates

# Get specific template
curl http://localhost:8084/templates/quick-performance-check

# Response:
{
  "name": "quick-performance-check",
  "description": "Quick 5-minute performance validation",
  "config": {
    "test_types": ["baseline", "concurrent"],
    "max_users": 100,
    "test_duration": 300,
    "spawn_rate": 20
  }
}
```

### API Client Examples

#### Python Client
```python
import httpx
import asyncio
import time

class GovStackTestClient:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        
    async def run_quick_test(self):
        async with httpx.AsyncClient() as client:
            # Start test
            response = await client.post(f"{self.base_url}/tests/run", json={
                "test_types": ["baseline", "concurrent"],
                "max_users": 100,
                "daily_users": 5000
            })
            
            test_data = response.json()
            test_id = test_data["test_id"]
            print(f"Started test: {test_id}")
            
            # Poll for completion
            while True:
                status_response = await client.get(f"{self.base_url}/tests/{test_id}/status")
                status = status_response.json()
                
                print(f"Status: {status['status']} - {status.get('progress', {}).get('percent_complete', 0)}% complete")
                
                if status["status"] in ["completed", "failed", "stopped"]:
                    break
                    
                await asyncio.sleep(10)
            
            # Get results
            results_response = await client.get(f"{self.base_url}/tests/{test_id}/results")
            results = results_response.json()
            
            return results

# Usage
async def main():
    client = GovStackTestClient()
    results = await client.run_quick_test()
    print(f"Test completed with {results['summary']['overall_success_rate']*100:.1f}% success rate")

asyncio.run(main())
```

#### JavaScript/Node.js Client
```javascript
const axios = require('axios');

class GovStackTestClient {
    constructor(baseUrl = 'http://localhost:8084') {
        this.baseUrl = baseUrl;
        this.client = axios.create({ baseURL: baseUrl });
    }

    async runQuickTest() {
        try {
            // Start test
            const startResponse = await this.client.post('/tests/run', {
                test_types: ['baseline', 'concurrent'],
                max_users: 100,
                daily_users: 5000
            });

            const testId = startResponse.data.test_id;
            console.log(`Started test: ${testId}`);

            // Poll for completion
            while (true) {
                const statusResponse = await this.client.get(`/tests/${testId}/status`);
                const status = statusResponse.data;

                console.log(`Status: ${status.status} - ${status.progress?.percent_complete || 0}% complete`);

                if (['completed', 'failed', 'stopped'].includes(status.status)) {
                    break;
                }

                await new Promise(resolve => setTimeout(resolve, 10000));
            }

            // Get results
            const resultsResponse = await this.client.get(`/tests/${testId}/results`);
            return resultsResponse.data;

        } catch (error) {
            console.error('Test execution failed:', error.message);
            throw error;
        }
    }
}

// Usage
(async () => {
    const client = new GovStackTestClient();
    const results = await client.runQuickTest();
    console.log(`Test completed with ${(results.summary.overall_success_rate * 100).toFixed(1)}% success rate`);
})();
```

#### Bash/cURL Client
```bash
#!/bin/bash

# Simple bash client for test automation
BASE_URL="http://localhost:8084"

# Start test
echo "Starting test..."
RESPONSE=$(curl -s -X POST "$BASE_URL/tests/run" \
  -H "Content-Type: application/json" \
  -d '{
    "test_types": ["baseline", "concurrent"],
    "max_users": 100,
    "daily_users": 5000
  }')

TEST_ID=$(echo "$RESPONSE" | jq -r '.test_id')
echo "Test ID: $TEST_ID"

# Poll for completion
while true; do
    STATUS_RESPONSE=$(curl -s "$BASE_URL/tests/$TEST_ID/status")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress.percent_complete // 0')
    
    echo "Status: $STATUS - ${PROGRESS}% complete"
    
    if [[ "$STATUS" == "completed" || "$STATUS" == "failed" || "$STATUS" == "stopped" ]]; then
        break
    fi
    
    sleep 10
done

# Get results
echo "Fetching results..."
curl -s "$BASE_URL/tests/$TEST_ID/results" | jq '.' > "test_results_$TEST_ID.json"
echo "Results saved to test_results_$TEST_ID.json"

# Extract key metrics
SUCCESS_RATE=$(curl -s "$BASE_URL/tests/$TEST_ID/results" | jq -r '.summary.overall_success_rate')
echo "Overall success rate: $(echo "$SUCCESS_RATE * 100" | bc -l)%"
```

### WebSocket Real-time Updates

The test service also provides WebSocket endpoints for real-time test monitoring:

```javascript
// Connect to real-time test updates
const ws = new WebSocket('ws://localhost:8084/ws/tests/{test_id}');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Test update:', data);
    
    // Update UI with current metrics
    updateDashboard(data.metrics);
};

ws.onopen = function() {
    console.log('Connected to test monitoring');
};

ws.onclose = function() {
    console.log('Disconnected from test monitoring');
};
```

### Prometheus Metrics Endpoint

```bash
# Get Prometheus-format metrics
curl http://localhost:8084/metrics

# Sample metrics output:
# govstack_test_requests_total{method="POST",status="200"} 1542
# govstack_test_response_time_seconds{quantile="0.5"} 1.85
# govstack_test_response_time_seconds{quantile="0.95"} 3.24
# govstack_test_active_users 250
# govstack_test_success_rate 0.97
```

## 📊 Understanding Results

### Test Report Structure
```json
{
  "baseline": {
    "avg_response_time_ms": 1250.5,
    "success_rate": 0.98,
    "total_requests": 10
  },
  "concurrent_users": {
    "100_users": {
      "avg_response_time_ms": 2100.3,
      "success_rate": 0.95,
      "requests_per_second": 15.2
    }
  },
  "token_projections": {
    "projected_daily_cost": 45.67,
    "projected_monthly_cost": 1370.10
  }
}
```

### Key Performance Indicators

#### ✅ Good Performance
- Response time < 2000ms
- Success rate > 95%
- Memory growth < 100MB per 1000 requests
- Token costs reasonable for your budget

#### ⚠️ Warning Signs
- Response time 2000-5000ms
- Success rate 90-95%
- High memory usage growth
- Escalating token costs

#### ❌ Poor Performance
- Response time > 5000ms
- Success rate < 90%
- Memory leaks detected
- Unsustainable token costs

## 🏗️ Architecture

### Test Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Test Runner   │    │  Test Service   │    │   Monitoring    │
│   (CLI/Script)  │────│  (FastAPI)      │────│  (Prometheus)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   GovStack API  │──────────────┘
                        │   (Target)      │
                        └─────────────────┘
                                 │
                    ┌─────────────────────────────┐
                    │       Dependencies          │
                    │  ┌─────────┐ ┌─────────┐   │
                    │  │Database │ │ChromaDB │   │
                    │  └─────────┘ └─────────┘   │
                    │  ┌─────────┐ ┌─────────┐   │
                    │  │ MinIO   │ │  Redis  │   │
                    │  └─────────┘ └─────────┘   │
                    └─────────────────────────────┘
```

### Test Types Explained

#### 1. Baseline Performance
- **Purpose**: Establish performance baselines
- **Method**: Sequential single-user requests
- **Metrics**: Response time, success rate, basic functionality

#### 2. Concurrent Users Test
- **Purpose**: Test system under concurrent load
- **Method**: Simultaneous requests from multiple virtual users
- **Scaling**: 10 → 25 → 50 → 100 → 250 → 500 → 1000 users
- **Metrics**: Scalability limits, resource contention

#### 3. Daily Load Simulation
- **Purpose**: Simulate realistic daily usage patterns
- **Method**: Variable load based on typical usage hours
- **Pattern**: Peak hours (9-11 AM, 2-4 PM), off-peak periods
- **Metrics**: System behavior under real-world conditions

#### 4. Stress Testing
- **Purpose**: Find system breaking points
- **Scenarios**:
  - Rapid-fire requests
  - Long conversations
  - Large payloads
- **Metrics**: Error rates, recovery time, limits

#### 5. Memory & Latency Analysis
- **Purpose**: Monitor resource usage patterns
- **Method**: Track memory consumption during load
- **Metrics**: Memory leaks, garbage collection, performance degradation

## 🔧 Configuration & Advanced Setup

### Environment Variables Reference

Create a `.env.test` file with these configurations:

```bash
# Core API Configuration
API_BASE_URL=http://localhost:5005      # Target API endpoint
API_TIMEOUT=30                          # Request timeout in seconds
API_COLLECTION_ID=govstack-docs         # Default collection for queries

# Load Testing Parameters
MAX_USERS=1000                          # Maximum concurrent users
DAILY_USERS=40000                       # Target daily active users
SPAWN_RATE=10                           # Users spawned per second
TEST_DURATION=300                       # Test duration in seconds
RAMP_UP_TIME=60                         # Time to reach max users

# Performance Thresholds
MAX_MEMORY_MB=2048                      # Memory usage alert threshold
MAX_RESPONSE_TIME_MS=2000               # Response time alert threshold
MIN_SUCCESS_RATE=0.95                   # Minimum acceptable success rate
MAX_ERROR_RATE=0.05                     # Maximum acceptable error rate

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres-test:5432/govstackdb
POSTGRES_PASSWORD=postgres              # PostgreSQL password
POSTGRES_DB=govstackdb                  # Database name

# Object Storage (MinIO)
MINIO_ENDPOINT=minio-test               # MinIO server endpoint
MINIO_PORT=9000                         # MinIO port
MINIO_ACCESS_KEY=minioadmin             # MinIO access key
MINIO_SECRET_KEY=minioadmin             # MinIO secret key
MINIO_BUCKET_NAME=govstack-docs         # Primary bucket name
MINIO_SECURE=false                      # Use HTTPS (true/false)

# Vector Database (ChromaDB)
CHROMA_HOST=chroma-test                 # ChromaDB host
CHROMA_PORT=8000                        # ChromaDB port
CHROMA_COLLECTION_NAME=govstack         # Default collection name

# Monitoring & Observability
ENABLE_PROMETHEUS=true                  # Enable Prometheus metrics
PROMETHEUS_PORT=8000                    # Prometheus metrics port
ENABLE_GRAFANA=true                     # Enable Grafana dashboards
GRAFANA_ADMIN_PASSWORD=admin            # Grafana admin password

# Test Behavior
TRACK_TOKEN_USAGE=true                  # Monitor OpenAI token usage
SAVE_RESPONSES=false                    # Save API responses for analysis
ENABLE_DETAILED_LOGS=true               # Detailed logging
LOG_LEVEL=INFO                          # Logging level (DEBUG/INFO/WARN/ERROR)

# Test Service Configuration
TEST_SERVICE_HOST=0.0.0.0               # Test service bind address
TEST_SERVICE_PORT=8084                  # Test service port
ENABLE_CORS=true                        # Enable CORS for web UI

# OpenAI Configuration (if applicable)
OPENAI_API_KEY=your_api_key_here        # OpenAI API key for token tracking
OPENAI_ORG_ID=your_org_id               # OpenAI organization ID

# Network Configuration
REQUEST_TIMEOUT=30                      # HTTP request timeout
CONNECTION_TIMEOUT=10                   # Connection timeout
MAX_RETRIES=3                          # Maximum retry attempts
RETRY_DELAY=1                          # Delay between retries (seconds)

# Test Data Configuration
SAMPLE_QUERIES_FILE=config/sample_queries.json  # Custom test queries
USER_SCENARIOS_FILE=config/user_scenarios.json  # Custom user scenarios
```

### Advanced Docker Compose Configuration

#### Resource Limits
```yaml
# Add to docker-compose.test.yml services
services:
  test-service:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

#### Network Configuration
```yaml
# Custom network settings
networks:
  govstack-test-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

#### Volume Persistence
```yaml
# Add persistent volumes for test data
volumes:
  test_results:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

### Custom Test Queries Configuration

Create `config/sample_queries.json`:
```json
{
  "categories": {
    "business_registration": [
      "What services does the government provide for business registration?",
      "How do I register a new business?",
      "What documents are required for business registration?",
      "How long does business registration take?",
      "What are the fees for business registration?"
    ],
    "citizen_services": [
      "How do I apply for a passport?",
      "What are the requirements for obtaining a driver's license?",
      "How do I register to vote?",
      "Where can I get a birth certificate?",
      "How do I apply for social benefits?"
    ],
    "tax_information": [
      "How do I file my tax return?",
      "What tax deductions am I eligible for?",
      "When is the tax filing deadline?",
      "How do I pay my taxes online?",
      "What records should I keep for taxes?"
    ],
    "permits_licenses": [
      "How do I apply for a building permit?",
      "What licenses do I need to start a restaurant?",
      "How do I get a professional license?",
      "What are the requirements for a fishing license?",
      "How do I renew my business license?"
    ]
  },
  "complex_queries": [
    "I'm starting a restaurant business. What permits, licenses, and registrations do I need, and how long will the entire process take?",
    "My elderly parent needs help with multiple government services. What support is available and how can I help them access these services?",
    "I'm moving to a new city. What government services do I need to update, and what's the most efficient order to handle everything?"
  ],
  "load_test_queries": [
    "Quick health check query",
    "Simple information request",
    "Basic service inquiry",
    "Standard help request"
  ]
}
```

### User Scenarios Configuration

Create `config/user_scenarios.json`:
```json
{
  "scenarios": [
    {
      "name": "new_citizen",
      "weight": 30,
      "description": "New citizen seeking basic information",
      "queries": [
        "How do I register to vote?",
        "Where can I get a driver's license?",
        "What government services are available for new residents?"
      ],
      "think_time": [3, 8],
      "session_length": [2, 5]
    },
    {
      "name": "business_owner",
      "weight": 25,
      "description": "Business owner seeking permits and licenses",
      "queries": [
        "How do I register a new business?",
        "What permits do I need for a retail store?",
        "How do I file business taxes?"
      ],
      "think_time": [5, 15],
      "session_length": [3, 8]
    },
    {
      "name": "power_user",
      "weight": 15,
      "description": "Experienced user with complex needs",
      "queries": [
        "I need to transfer my business license to a new location. What's the process?",
        "How do I appeal a permit denial?",
        "What are the regulations for starting a food truck business?"
      ],
      "think_time": [2, 5],
      "session_length": [5, 12]
    },
    {
      "name": "casual_browser",
      "weight": 30,
      "description": "Casual user browsing for information",
      "queries": [
        "What services does the government provide?",
        "How do I contact the mayor's office?",
        "Where is the nearest DMV office?"
      ],
      "think_time": [10, 30],
      "session_length": [1, 3]
    }
  ]
}
```

### Monitoring Configuration

#### Prometheus Custom Metrics
Create `monitoring/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'govstack-api'
    static_configs:
      - targets: ['api:5005']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'test-service'
    static_configs:
      - targets: ['test-service:8084']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

#### Grafana Dashboard Configuration
Create `monitoring/grafana/dashboards/govstack-performance.json`:
```json
{
  "dashboard": {
    "title": "GovStack Performance Dashboard",
    "panels": [
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph", 
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/second"
          }
        ]
      }
    ]
  }
}
```

### Custom Test Development

#### Extending Test Classes
```python
# tests/custom_tests/my_custom_test.py
from locust import task, between
from tests.load_tests.locust_tests import GovStackUser

class CustomBusinessScenarioUser(GovStackUser):
    wait_time = between(5, 15)
    
    def on_start(self):
        """Called when a user starts"""
        super().on_start()
        self.business_context = self.setup_business_context()
    
    @task(3)
    def business_registration_flow(self):
        """Complete business registration workflow"""
        queries = [
            "How do I register a new business?",
            "What documents do I need for business registration?",
            "What are the fees for business registration?",
            "How long does the registration process take?"
        ]
        
        for query in queries:
            self.ask_question(query)
            self.wait()
    
    @task(2)
    def permit_inquiry_flow(self):
        """Permit and license inquiry workflow"""
        queries = [
            "What permits do I need for a restaurant?",
            "How do I apply for a liquor license?",
            "What are the health department requirements?"
        ]
        
        for query in queries:
            self.ask_question(query)
            self.wait()
    
    def setup_business_context(self):
        """Set up business-specific context"""
        return {
            "business_type": "restaurant",
            "location": "downtown",
            "size": "small"
        }
```

#### Running Custom Tests
```bash
# Run your custom test class
locust -f tests/custom_tests/my_custom_test.py CustomBusinessScenarioUser --host http://localhost:5005

# Include in standard test suite
python -m tests.cli run --test custom --test-file tests/custom_tests/my_custom_test.py
```

## 📈 Monitoring & Visualization

### Prometheus Metrics
- System metrics (CPU, memory, disk)
- HTTP request metrics
- Custom application metrics
- Token usage tracking

### Grafana Dashboards
- Real-time performance monitoring
- Historical trend analysis
- Alert configuration
- Custom visualizations

### Access URLs (when using Docker)
- **Test Service**: http://localhost:8084
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🧪 Test Types

### Unit Tests
```bash
# Run all unit tests
./run_tests.sh unit-tests

# Run specific test file
python -m pytest tests/unit_tests/test_api.py -v
```

### Integration Tests
```bash
# Run all integration tests
./run_tests.sh integration-tests

# Run with coverage
python -m pytest tests/integration_tests/ --cov=app --cov-report=html
```

### Load Tests
```bash
# Full scalability suite
./run_tests.sh run-tests

# Specific test types only
./run_tests.sh run-tests --test-types baseline,concurrent
```

## 📁 Output Files

### Test Results
- `scalability_test_results_YYYYMMDD_HHMMSS.json`: Complete test results
- `performance_metrics_YYYYMMDD_HHMMSS.json`: System performance data
- `token_usage_YYYYMMDD_HHMMSS.json`: Token consumption analysis

### Reports
- Console output with formatted tables and charts
- Detailed recommendations for optimization
- Cost projections for scaling

## 🚨 Setup Troubleshooting & Common Issues

### Docker & Service Issues

#### Docker Not Running
```bash
# Check Docker status
sudo systemctl status docker

# Start Docker service
sudo systemctl start docker

# Enable Docker on boot
sudo systemctl enable docker

# Test Docker installation
docker run hello-world
```

#### Port Conflicts
```bash
# Check what's using your ports
sudo netstat -tulpn | grep :5005  # API port
sudo netstat -tulpn | grep :8084  # Test service port
sudo netstat -tulpn | grep :3000  # Grafana port

# Kill processes using required ports
sudo kill -9 $(sudo lsof -t -i:5005)

# Or change ports in docker-compose.test.yml
```

#### Permission Denied Issues
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Fix file permissions
sudo chown -R $USER:$USER ./tests/
chmod +x ./tests/run_tests.sh
```

### API Connection Issues

#### API Not Accessible
```bash
# Check if main API is running
docker-compose -f ../docker-compose.dev.yml ps

# Check API logs for errors
docker-compose -f ../docker-compose.dev.yml logs api

# Restart API if needed
docker-compose -f ../docker-compose.dev.yml restart api

# Test API manually
curl -v http://localhost:5005/health
```

#### Database Connection Problems
```bash
# Check database status
docker-compose -f docker-compose.test.yml ps postgres-test

# View database logs
docker-compose -f docker-compose.test.yml logs postgres-test

# Reset database
docker-compose -f docker-compose.test.yml restart postgres-test

# Connect to database manually
docker exec -it govstack-testing-postgres-test-1 psql -U postgres -d govstackdb
```

#### ChromaDB/Vector Database Issues
```bash
# Check ChromaDB status
docker-compose -f docker-compose.test.yml ps chroma-test

# View ChromaDB logs
docker-compose -f docker-compose.test.yml logs chroma-test

# Reset ChromaDB data
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

### Environment Configuration Issues

#### Missing Environment Variables
```bash
# Check if .env.test exists
ls -la .env.test

# Create from template if missing
cp .env.test.example .env.test

# Validate environment variables
cat .env.test | grep -v '^#' | grep '='
```

#### Python Dependencies
```bash
# Install missing packages
pip install -r requirements.txt

# Install specific packages for testing
pip install locust pytest httpx rich typer

# Check Python version compatibility
python3 --version  # Should be 3.8+

# Virtual environment setup (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Memory & Performance Issues

#### Insufficient Memory
```bash
# Check system memory
free -h

# Monitor memory during tests
watch -n 1 'free -h && docker stats --no-stream'

# Reduce test load if needed
./run_tests.sh run-tests --max-users 100 --daily-users 5000
```

#### High CPU Usage
```bash
# Monitor CPU usage
htop

# Reduce test concurrency
./run_tests.sh run-tests --spawn-rate 5

# Limit Docker resources
# Add to docker-compose.test.yml:
# deploy:
#   resources:
#     limits:
#       cpus: '2.0'
#       memory: 4G
```

### Test Execution Issues

#### Tests Timing Out
```bash
# Increase API timeout in .env.test
API_TIMEOUT=60

# Or pass timeout parameter
./run_tests.sh run-tests --api-timeout 60

# Check network connectivity
ping localhost
curl -w "@curl-format.txt" -o /dev/null http://localhost:5005/health
```

#### High Token Usage/Costs
```bash
# Check current token usage
python -c "
from tests.utils.token_tracker import TokenTracker
t = TokenTracker()
print(t.get_usage_summary())
"

# Reduce test scope to control costs
./run_tests.sh run-tests --test-types baseline
./run_tests.sh run-tests --max-users 50
```

#### Test Data/Results Issues
```bash
# Clear old test results
./run_tests.sh cleanup

# Clear everything including volumes
./run_tests.sh cleanup --volumes

# Check disk space
df -h

# Remove old Docker images
docker system prune -f
```

### Service-Specific Issues

#### Prometheus Not Starting
```bash
# Check Prometheus configuration
docker-compose -f docker-compose.test.yml logs prometheus

# Validate prometheus.yml
docker exec govstack-testing-prometheus-1 promtool check config /etc/prometheus/prometheus.yml

# Reset Prometheus data
docker volume rm govstack-testing_prometheus_data
```

#### Grafana Dashboard Issues
```bash
# Access Grafana logs
docker-compose -f docker-compose.test.yml logs grafana

# Reset Grafana (login: admin/admin)
docker volume rm govstack-testing_grafana_data

# Import dashboards manually
# Go to http://localhost:3000 → + → Import
# Upload files from tests/monitoring/grafana-dashboards/
```

### Network Issues

#### Container Communication Problems
```bash
# Check Docker network
docker network ls | grep govstack

# Inspect network configuration
docker network inspect govstack-testing_govstack-test-network

# Test container-to-container connectivity
docker exec govstack-testing-test-service-1 ping api
docker exec govstack-testing-test-service-1 curl http://api:5005/health
```

#### DNS Resolution Issues
```bash
# Check /etc/hosts
cat /etc/hosts

# Test DNS resolution
nslookup localhost
dig localhost

# Use IP addresses instead of hostnames if needed
./run_tests.sh run-tests --api-url http://127.0.0.1:5005
```

### Step-by-Step Debugging

#### Complete Environment Reset
```bash
# 1. Stop everything
./run_tests.sh stop-env
docker-compose -f ../docker-compose.dev.yml down

# 2. Clean up completely
docker system prune -a -f
docker volume prune -f

# 3. Restart from scratch
docker-compose -f ../docker-compose.dev.yml up -d
sleep 30  # Wait for services to stabilize
./run_tests.sh start-env

# 4. Verify each service
curl http://localhost:5005/health
curl http://localhost:8084/health
```

#### Minimal Test Setup
```bash
# Start only essential services
docker-compose -f docker-compose.test.yml up -d postgres-test api

# Run minimal test
python -m tests.cli quick-check --api-url http://localhost:5005

# Gradually add more services
docker-compose -f docker-compose.test.yml up -d
```

### Getting Help

#### Collect Diagnostic Information
```bash
# System information
uname -a
docker --version
docker-compose --version
python3 --version

# Service status
docker-compose -f docker-compose.test.yml ps
docker stats --no-stream

# Port status
sudo netstat -tulpn | grep -E ":(5005|8084|3000|9090)"

# Log collection
mkdir -p /tmp/govstack-debug
docker-compose -f docker-compose.test.yml logs > /tmp/govstack-debug/test-logs.txt
docker-compose -f ../docker-compose.dev.yml logs > /tmp/govstack-debug/api-logs.txt
```

#### Enable Debug Mode
```bash
# Set debug environment variables
export DEBUG=1
export LOG_LEVEL=DEBUG

# Run tests with maximum verbosity
./run_tests.sh run-tests --verbose --test-types baseline

# Monitor logs in real-time
docker-compose -f docker-compose.test.yml logs -f test-service
```

### Performance Optimization Tips

#### For Better API Performance
1. **Database Optimization**: Ensure indexes are properly configured
2. **Caching**: Implement response caching for frequent queries
3. **Connection Pooling**: Optimize database connection settings
4. **Resource Limits**: Set appropriate memory and CPU limits

#### For Testing Environment
1. **Resource Allocation**: Ensure adequate system resources
2. **Network**: Use local or high-bandwidth connections
3. **Parallel Execution**: Adjust concurrency levels based on system capacity

## � Production Deployment & Scaling

### Container Deployment Options

#### Docker Swarm Deployment
```bash
# Initialize Docker Swarm
docker swarm init

# Deploy the testing stack
docker stack deploy -c docker-compose.prod.yml govstack-testing

# Scale test service replicas
docker service scale govstack-testing_test-service=3

# Monitor deployment
docker stack ps govstack-testing
```

#### Kubernetes Deployment
Create `k8s/testing-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: govstack-test-service
  labels:
    app: govstack-test-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: govstack-test-service
  template:
    metadata:
      labels:
        app: govstack-test-service
    spec:
      containers:
      - name: test-service
        image: govstack/test-service:latest
        ports:
        - containerPort: 8084
        env:
        - name: API_BASE_URL
          value: "http://govstack-api:5005"
        - name: MAX_USERS
          value: "2000"
        - name: DAILY_USERS
          value: "80000"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8084
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8084
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: govstack-test-service
spec:
  selector:
    app: govstack-test-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8084
  type: LoadBalancer
```

Apply the deployment:
```bash
kubectl apply -f k8s/testing-deployment.yaml

# Scale the deployment
kubectl scale deployment govstack-test-service --replicas=5

# Check status
kubectl get pods -l app=govstack-test-service
```

#### Load Balancer Configuration
```nginx
# nginx load balancer config
upstream govstack_test_service {
    least_conn;
    server test-service-1:8084;
    server test-service-2:8084;
    server test-service-3:8084;
}

server {
    listen 80;
    server_name test.govstack.com;

    location / {
        proxy_pass http://govstack_test_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /metrics {
        proxy_pass http://govstack_test_service;
        auth_basic "Prometheus Metrics";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

### High-Scale Testing Configuration

#### Large-Scale Environment Setup
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  test-service:
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  locust-master:
    image: locustio/locust
    ports:
      - "8089:8089"
    volumes:
      - ./tests:/mnt/locust
    command: -f /mnt/locust/load_tests/locust_tests.py --master -H http://api:5005
    environment:
      - LOCUST_LOCUSTFILE=/mnt/locust/load_tests/locust_tests.py

  locust-worker:
    image: locustio/locust
    volumes:
      - ./tests:/mnt/locust
    command: -f /mnt/locust/load_tests/locust_tests.py --worker --master-host=locust-master
    deploy:
      replicas: 10
    depends_on:
      - locust-master
```

#### Multi-Region Testing
```bash
# Deploy across multiple regions
regions=("us-east-1" "eu-west-1" "ap-southeast-1")

for region in "${regions[@]}"; do
    echo "Deploying to $region..."
    
    # Set region-specific configuration
    export AWS_REGION=$region
    export API_ENDPOINT="https://api-${region}.govstack.com"
    
    # Deploy testing infrastructure
    docker-compose -f docker-compose.multiregion.yml up -d
    
    # Start coordinated testing
    ./run_tests.sh run-tests \
      --max-users 2000 \
      --api-url $API_ENDPOINT \
      --region $region
done
```

### Performance Optimization

#### System Tuning for High Load
```bash
# Increase system limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Kernel parameter tuning
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.ip_local_port_range = 1024 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_tw_reuse = 1" >> /etc/sysctl.conf
echo "net.ipv4.tcp_fin_timeout = 30" >> /etc/sysctl.conf

# Apply changes
sysctl -p
```

#### Docker Optimization
```bash
# Optimize Docker daemon
echo '{
  "storage-driver": "overlay2",
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  }
}' > /etc/docker/daemon.json

systemctl restart docker
```

### Automated Scaling

#### Auto-scaling Script
```bash
#!/bin/bash
# auto-scale-tests.sh

METRICS_URL="http://localhost:8084/metrics/system"
MAX_CPU=80
MAX_MEMORY=85
SCALE_UP_THRESHOLD=3
SCALE_DOWN_THRESHOLD=10

check_and_scale() {
    local cpu_usage=$(curl -s $METRICS_URL | jq -r '.cpu_usage')
    local memory_usage=$(curl -s $METRICS_URL | jq -r '.memory_usage')
    local current_replicas=$(docker service ls --filter name=test-service --format "{{.Replicas}}" | cut -d'/' -f1)
    
    if (( $(echo "$cpu_usage > $MAX_CPU" | bc -l) )) || (( $(echo "$memory_usage > $MAX_MEMORY" | bc -l) )); then
        # Scale up
        new_replicas=$((current_replicas + 1))
        echo "High resource usage detected. Scaling up to $new_replicas replicas"
        docker service scale govstack-testing_test-service=$new_replicas
        
    elif (( $(echo "$cpu_usage < 30" | bc -l) )) && (( $(echo "$memory_usage < 40" | bc -l) )) && [ $current_replicas -gt 1 ]; then
        # Scale down
        new_replicas=$((current_replicas - 1))
        echo "Low resource usage detected. Scaling down to $new_replicas replicas"
        docker service scale govstack-testing_test-service=$new_replicas
    fi
}

# Run continuous monitoring
while true; do
    check_and_scale
    sleep 30
done
```

#### Kubernetes Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: govstack-test-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: govstack-test-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 60
```

### Security Configuration

#### SSL/TLS Setup
```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update docker-compose with SSL
services:
  test-service:
    ports:
      - "443:8443"
    environment:
      - SSL_CERT_PATH=/certs/cert.pem
      - SSL_KEY_PATH=/certs/key.pem
    volumes:
      - ./certs:/certs:ro
```

#### Authentication Setup
```yaml
# Add authentication service
auth-service:
  image: oauth2-proxy/oauth2-proxy
  ports:
    - "4180:4180"
  environment:
    - OAUTH2_PROXY_PROVIDER=github
    - OAUTH2_PROXY_CLIENT_ID=your_github_client_id
    - OAUTH2_PROXY_CLIENT_SECRET=your_github_client_secret
    - OAUTH2_PROXY_COOKIE_SECRET=your_random_cookie_secret
    - OAUTH2_PROXY_UPSTREAMS=http://test-service:8084
```

### Disaster Recovery

#### Backup Strategy
```bash
#!/bin/bash
# backup-test-data.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/govstack-testing"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup test results
docker run --rm -v govstack-testing_test_results:/data -v $BACKUP_DIR:/backup alpine \
  tar czf /backup/test_results_$DATE.tar.gz -C /data .

# Backup database
docker exec govstack-testing-postgres-test-1 \
  pg_dump -U postgres govstackdb | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup configuration
cp -r ./tests/config $BACKUP_DIR/config_$DATE

# Upload to cloud storage (example with AWS S3)
aws s3 sync $BACKUP_DIR s3://govstack-testing-backups/$(date +%Y/%m/%d)/

echo "Backup completed: $BACKUP_DIR"
```

#### Recovery Procedures
```bash
#!/bin/bash
# restore-test-environment.sh

BACKUP_DATE=$1
BACKUP_DIR="/backups/govstack-testing"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 YYYYMMDD_HHMMSS"
    exit 1
fi

# Stop current environment
./run_tests.sh stop-env

# Restore database
gunzip -c $BACKUP_DIR/postgres_$BACKUP_DATE.sql.gz | \
  docker exec -i govstack-testing-postgres-test-1 psql -U postgres -d govstackdb

# Restore test results
docker run --rm -v govstack-testing_test_results:/data -v $BACKUP_DIR:/backup alpine \
  tar xzf /backup/test_results_$BACKUP_DATE.tar.gz -C /data

# Restore configuration
cp -r $BACKUP_DIR/config_$BACKUP_DATE/* ./tests/config/

# Restart environment
./run_tests.sh start-env

echo "Recovery completed from backup: $BACKUP_DATE"
```

### Monitoring & Alerting

#### Comprehensive Alerting Rules
```yaml
# monitoring/alerting-rules.yml
groups:
  - name: govstack-testing
    rules:
      - alert: HighErrorRate
        expr: rate(govstack_test_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in testing service"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: govstack_test_response_time_seconds{quantile="0.95"} > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: TestServiceDown
        expr: up{job="test-service"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Test service is down"
          description: "Test service has been down for more than 1 minute"
```

#### Integration with External Monitoring
```python
# monitoring/webhook_handler.py
import requests
import json

def send_alert_to_slack(alert_data):
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    
    message = {
        "text": f"🚨 GovStack Testing Alert",
        "attachments": [
            {
                "color": "danger" if alert_data["severity"] == "critical" else "warning",
                "fields": [
                    {
                        "title": "Alert",
                        "value": alert_data["summary"],
                        "short": True
                    },
                    {
                        "title": "Details",
                        "value": alert_data["description"],
                        "short": True
                    }
                ]
            }
        ]
    }
    
    requests.post(webhook_url, json=message)

def send_alert_to_pagerduty(alert_data):
    pagerduty_url = "https://events.pagerduty.com/v2/enqueue"
    
    payload = {
        "routing_key": "YOUR_PAGERDUTY_ROUTING_KEY",
        "event_action": "trigger",
        "payload": {
            "summary": alert_data["summary"],
            "severity": alert_data["severity"],
            "source": "govstack-testing",
            "custom_details": alert_data
        }
    }
    
    requests.post(pagerduty_url, json=payload)
```

## 📚 Advanced Usage

### Custom Test Scenarios

Create your own test scenarios by extending the base classes:

```python
from tests.load_tests.locust_tests import GovStackUser

class CustomTestUser(GovStackUser):
    @task
    def custom_workflow(self):
        # Your custom test logic here
        pass
```

### API Integration

Use the test service programmatically:

```python
import httpx

async def run_automated_test():
    async with httpx.AsyncClient() as client:
        # Start test
        response = await client.post("http://localhost:8084/tests/run", json={
            "test_types": ["baseline", "concurrent"],
            "max_users": 500
        })
        
        test_id = response.json()["test_id"]
        
        # Poll for completion
        while True:
            status = await client.get(f"http://localhost:8084/tests/{test_id}/status")
            if status.json()["status"] == "completed":
                break
        
        # Get results
        results = await client.get(f"http://localhost:8084/tests/{test_id}/results")
        return results.json()
```

## 📞 Support

For questions, issues, or contributions:

1. **Documentation**: Check this README and inline code comments
2. **Issues**: Open GitHub issues for bugs or feature requests  
3. **Discussions**: Use GitHub discussions for questions
4. **Code Review**: Submit pull requests for improvements

## 📄 License

This testing suite is part of the GovStack project and follows the same license terms.
