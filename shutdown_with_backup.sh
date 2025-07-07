#!/bin/bash

# Graceful Shutdown Script with Database Backup
# Usage: ./shutdown_with_backup.sh [dev|prod]

set -e

ENVIRONMENT=${1:-prod}

echo "========================================="
echo "Graceful Shutdown with Backup - $ENVIRONMENT"
echo "========================================="

# Determine the compose file to use
if [ "$ENVIRONMENT" = "dev" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    echo "Using development environment"
else
    COMPOSE_FILE="docker-compose.yml"
    echo "Using production environment"
fi

# Check if the services are running
if ! docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    echo "No services appear to be running."
    exit 0
fi

echo "Step 1: Creating database backup..."
BACKUP_FILE=$(./scripts/postgres_backup.sh "$ENVIRONMENT" "shutdown")

if [ $? -eq 0 ]; then
    echo "✅ Database backup completed successfully"
    echo "📁 Backup saved to: $BACKUP_FILE"
else
    echo "❌ Database backup failed!"
    read -p "Do you want to continue with shutdown anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Shutdown cancelled."
        exit 1
    fi
fi

echo "Step 2: Gracefully stopping services..."

# Stop the services in reverse dependency order
echo "Stopping API service..."
docker compose -f "$COMPOSE_FILE" stop api 2>/dev/null || docker compose -f "$COMPOSE_FILE" stop govstack-server 2>/dev/null || true

echo "Stopping support services..."
docker compose -f "$COMPOSE_FILE" stop minio minio-dev chroma chroma-dev 2>/dev/null || true

echo "Stopping database (this may take a moment)..."
if [ "$ENVIRONMENT" = "dev" ]; then
    docker compose -f "$COMPOSE_FILE" stop postgres-dev
else
    docker compose -f "$COMPOSE_FILE" stop postgres
fi

echo "Step 3: Removing containers..."
docker compose -f "$COMPOSE_FILE" down

echo "========================================="
echo "✅ Shutdown completed successfully!"
echo "📁 Database backup: $BACKUP_FILE"
echo "========================================="
