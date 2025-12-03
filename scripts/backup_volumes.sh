#!/bin/bash
set -e

# Step 2: Backup Data Volumes
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

BACKUP_DIR="$1"

echo "Backing up data volumes to ${BACKUP_DIR}..."

# Backup PostgreSQL data
if [ -d "./data/postgres" ]; then
    echo "  - Backing up postgres data..."
    tar -czf "${BACKUP_DIR}/postgres_data.tar.gz" -C ./data postgres
fi

# Backup ChromaDB data
if [ -d "./data/chroma" ]; then
    echo "  - Backing up chroma data..."
    tar -czf "${BACKUP_DIR}/chroma_data.tar.gz" -C ./data chroma
fi

# Backup MinIO data
if [ -d "./data/minio" ]; then
    echo "  - Backing up minio data..."
    tar -czf "${BACKUP_DIR}/minio_data.tar.gz" -C ./data minio
fi

# Backup storage directory
if [ -d "./storage" ]; then
    echo "  - Backing up storage directory..."
    tar -czf "${BACKUP_DIR}/storage_backup.tar.gz" storage
fi

echo "✓ Volume backups completed"
ls -lh "${BACKUP_DIR}"
