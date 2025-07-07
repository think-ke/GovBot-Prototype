# External Server Testing Quick Start Guide

This guide explains how to test against an existing GovStack API server instead of spinning up a local development environment.

## Prerequisites

1. **Docker and Docker Compose installed**
2. **Access to an existing GovStack API server**
3. **Network connectivity** between your test environment and the target server

## Quick Setup

### 1. Configure the External API URL

Edit the `.env.external` file to point to your server:

```bash
# Edit the external configuration
nano .env.external

# Set your server IP/URL
EXTERNAL_API_URL=http://YOUR_SERVER_IP:5005
```

### 2. Start External Testing Environment

```bash
# Start the external test environment (no local API)
./run_tests.sh start-external
```

This will start:
- Test Service UI: http://localhost:8084
- Prometheus: http://localhost:9090  
- Grafana: http://localhost:3000 (admin/admin)

### 3. Run Tests Against External Server

```bash
# Run all scalability tests
./run_tests.sh run-tests --api-url http://YOUR_SERVER_IP:5005

# Quick performance check
./run_tests.sh quick-check --api-url http://YOUR_SERVER_IP:5005

# Run specific test types
./run_tests.sh run-tests --test-types baseline,concurrent --max-users 500
```

### 4. Interactive Load Testing with Locust

```bash
# Start Locust web UI for manual testing
./run_tests.sh locust-ui --api-url http://YOUR_SERVER_IP:5005
```

Then open http://localhost:8089 to control the load test manually.

## Configuration Options

### Environment Variables

You can set these in `.env.external`:

```bash
# Target server
EXTERNAL_API_URL=http://192.168.1.100:5005

# Test parameters
MAX_USERS=1000
DAILY_USERS=40000
MAX_RESPONSE_TIME_MS=3000  # Higher for network latency

# Network settings
NETWORK_TIMEOUT=60
CONNECTION_RETRIES=3
```

### Command Line Options

```bash
# Specify different server
./run_tests.sh run-tests --api-url http://10.0.1.50:5005

# Adjust user count
./run_tests.sh run-tests --max-users 500 --daily-users 20000

# Run specific tests
./run_tests.sh run-tests --test-types baseline,concurrent,stress
```

## Test Types Available

- **baseline**: Single user performance baseline
- **concurrent**: Multiple concurrent users (10, 25, 50, 100, 250, 500, 1000)
- **daily_load**: Simulate realistic daily usage patterns
- **stress**: High-intensity stress testing
- **memory**: Memory usage and latency analysis

## Network Considerations

When testing external servers:

1. **Latency**: Network latency will be higher than local testing
2. **Timeouts**: The configuration uses longer timeouts for network calls
3. **Retries**: Built-in retry logic for network failures
4. **Monitoring**: Prometheus can monitor the test service but not the external API

## Viewing Results

### Real-time Monitoring

- **Grafana Dashboard**: http://localhost:3000
- **Prometheus Metrics**: http://localhost:9090
- **Test Service Status**: http://localhost:8084

### Generated Reports

Test results are saved in the `results/` directory:
- `scalability_test_results_TIMESTAMP.json`
- `performance_metrics_TIMESTAMP.json`
- `token_usage_TIMESTAMP.json`

## Cleanup

```bash
# Stop external test environment
./run_tests.sh stop-external

# Clean up test data
./run_tests.sh cleanup

# Remove Docker volumes
./run_tests.sh cleanup --volumes
```

## Troubleshooting

### Connection Issues

```bash
# Test basic connectivity
curl -f http://YOUR_SERVER_IP:5005/health

# Check if API endpoint exists
curl -X POST http://YOUR_SERVER_IP:5005/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### View Logs

```bash
# View test service logs
./run_tests.sh logs test-service

# View all service logs
docker-compose -p govstack-testing-external -f docker-compose.external.yml logs -f
```

### Common Issues

1. **API not accessible**: Check firewall and network connectivity
2. **Authentication errors**: Ensure the external API doesn't require authentication
3. **Timeout errors**: Increase `NETWORK_TIMEOUT` in `.env.external`
4. **High failure rates**: The external server may be overloaded

## Example: Testing Production Server

```bash
# Configure for production testing
cat > .env.external << EOF
EXTERNAL_API_URL=https://api.govstack.example.com
MAX_USERS=100
DAILY_USERS=5000
MAX_RESPONSE_TIME_MS=5000
NETWORK_TIMEOUT=120
EOF

# Start external test environment
./run_tests.sh start-external

# Run conservative load test
./run_tests.sh run-tests --max-users 100 --test-types baseline,concurrent
```

This configuration is safer for production environments with lower user counts and longer timeouts.
