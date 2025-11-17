#!/bin/bash
set -e

# Restore Script for GovStack
# Usage: ./restore_from_backup.sh <backup_directory>

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_directory>"
    echo "Example: $0 ./data_backups/backup_20241030_120000"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "=========================================="
echo "GovStack Restore Script"
echo "Backup: ${BACKUP_DIR}"
echo "=========================================="

# Step 1: Stop all services
echo ""
echo "Step 1: Stopping all Docker services..."
docker compose down
echo "✓ All services stopped"

# Step 2: Clear existing data
echo ""
echo "Step 2: Clearing existing data directories..."
sudo rm -rf ./data/postgres/*
sudo rm -rf ./data/chroma/*
sudo rm -rf ./data/minio/*
sudo rm -rf ./data/metabase/*
sudo rm -rf ./storage/*
echo "✓ Data directories cleared"

# Step 3: Restore data volumes
echo ""
echo "Step 3: Restoring data volumes..."

if [ -f "${BACKUP_DIR}/postgres_data.tar.gz" ]; then
    echo "  - Restoring postgres data..."
    tar -xzf "${BACKUP_DIR}/postgres_data.tar.gz" -C ./data/
    echo "  ✓ postgres data restored"
fi

if [ -f "${BACKUP_DIR}/chroma_data.tar.gz" ]; then
    echo "  - Restoring chroma data..."
    tar -xzf "${BACKUP_DIR}/chroma_data.tar.gz" -C ./data/
    echo "  ✓ chroma data restored"
fi

if [ -f "${BACKUP_DIR}/minio_data.tar.gz" ]; then
    echo "  - Restoring minio data..."
    tar -xzf "${BACKUP_DIR}/minio_data.tar.gz" -C ./data/
    echo "  ✓ minio data restored"
fi

if [ -f "${BACKUP_DIR}/metabase_data.tar.gz" ]; then
    echo "  - Restoring metabase data..."
    tar -xzf "${BACKUP_DIR}/metabase_data.tar.gz" -C ./data/
    echo "  ✓ metabase data restored"
fi

if [ -f "${BACKUP_DIR}/storage_backup.tar.gz" ]; then
    echo "  - Restoring storage directory..."
    tar -xzf "${BACKUP_DIR}/storage_backup.tar.gz" -C ./
    echo "  ✓ storage directory restored"
fi

# Step 4: Start services
echo ""
echo "Step 4: Starting Docker services..."
docker compose up -d
echo "✓ Services started"

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Step 5: Restore databases from SQL dumps (optional, if you want to restore from SQL)
echo ""
echo "Step 5: Database restoration options..."
echo "The data volumes have been restored. If you also want to restore from SQL dumps:"
echo "  docker compose exec -T postgres psql -U postgres < ${BACKUP_DIR}/postgres_full_backup.sql"
echo ""
echo "=========================================="
echo "Restore Complete!"
echo "=========================================="
echo "All data has been restored from: ${BACKUP_DIR}"
echo "Services are now running."
echo "=========================================="
