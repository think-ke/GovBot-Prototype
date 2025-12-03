#!/bin/bash

echo "Building analytics Docker image..."
docker build -t analytics .

echo "Starting analytics container..."
docker run -d --name analytics-test -p 8005:8005 analytics

echo "Waiting for service to start..."
sleep 5

echo "Testing health endpoint..."
curl -f http://localhost:8005/analytics/health

echo "Testing root endpoint..."
curl -f http://localhost:8005/analytics

echo "Stopping and removing test container..."
docker stop analytics-test
docker rm analytics-test

echo "Test completed!"
