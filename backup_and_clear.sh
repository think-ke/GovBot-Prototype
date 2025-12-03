#!/bin/bash
set -e

# Backup and Clear Script for GovStack
# This script creates a full backup of all persistent data and then clears everything for a fresh install

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./data_backups/backup_${TIMESTAMP}"
DATA_DIR="./data"

echo "=========================================="
echo "GovStack Backup and Clear Script"
echo "Timestamp: ${TIMESTAMP}"
echo "=========================================="

# Create backup directory
echo ""
echo "Creating backup directory: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Check if postgres service is running
if docker compose ps postgres 2>/dev/null | grep -q "Up\|running"; then
    # Step 1: Backup PostgreSQL databases (only if services are running)
    echo ""
    echo "Step 1: Backing up PostgreSQL databases..."
    docker compose exec -T postgres pg_dumpall -U postgres > "${BACKUP_DIR}/postgres_full_backup.sql"
    echo "✓ PostgreSQL backup completed: ${BACKUP_DIR}/postgres_full_backup.sql"

    # Step 2: Backup individual databases for easier restore
    echo ""
    echo "Step 2: Backing up individual databases..."
    docker compose exec -T postgres pg_dump -U postgres -d govstackdb > "${BACKUP_DIR}/govstackdb_backup.sql"
    echo "✓ govstackdb backup completed"

    # Check if metabase database exists and backup
    if docker compose exec -T postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw metabase; then
        docker compose exec -T postgres pg_dump -U postgres -d metabase > "${BACKUP_DIR}/metabase_backup.sql"
        echo "✓ metabase backup completed"
    fi

    # Step 3: Stop all services
    echo ""
    echo "Step 3: Stopping all Docker services..."
    docker compose down
    echo "✓ All services stopped"
else
    echo ""
    echo "Services are not running. Skipping database dumps."
    echo "Will backup data volumes only."
    
    # Make sure services are stopped
    echo ""
    echo "Ensuring all services are stopped..."
    docker compose down 2>/dev/null || true
    echo "✓ All services stopped"
fi

# Step 4: Backup data volumes
echo ""
echo "Step 4: Backing up data volumes..."

# Backup PostgreSQL data
if [ -d "${DATA_DIR}/postgres" ]; then
    echo "  - Backing up postgres data..."
    sudo tar -czf "${BACKUP_DIR}/postgres_data.tar.gz" -C "${DATA_DIR}" postgres
    sudo chown $USER:$USER "${BACKUP_DIR}/postgres_data.tar.gz"
    echo "  ✓ postgres data backed up"
fi

# Backup ChromaDB data
if [ -d "${DATA_DIR}/chroma" ]; then
    echo "  - Backing up chroma data..."
    sudo tar -czf "${BACKUP_DIR}/chroma_data.tar.gz" -C "${DATA_DIR}" chroma
    sudo chown $USER:$USER "${BACKUP_DIR}/chroma_data.tar.gz"
    echo "  ✓ chroma data backed up"
fi

# Backup MinIO data
if [ -d "${DATA_DIR}/minio" ]; then
    echo "  - Backing up minio data..."
    sudo tar -czf "${BACKUP_DIR}/minio_data.tar.gz" -C "${DATA_DIR}" minio
    sudo chown $USER:$USER "${BACKUP_DIR}/minio_data.tar.gz"
    echo "  ✓ minio data backed up"
fi

# Backup Metabase data
if [ -d "${DATA_DIR}/metabase" ]; then
    echo "  - Backing up metabase data..."
    sudo tar -czf "${BACKUP_DIR}/metabase_data.tar.gz" -C "${DATA_DIR}" metabase
    sudo chown $USER:$USER "${BACKUP_DIR}/metabase_data.tar.gz"
    echo "  ✓ metabase data backed up"
fi

# Backup existing backups
if [ -d "${DATA_DIR}/backups" ]; then
    echo "  - Backing up existing backup data..."
    sudo tar -czf "${BACKUP_DIR}/backups_archive.tar.gz" -C "${DATA_DIR}" backups
    sudo chown $USER:$USER "${BACKUP_DIR}/backups_archive.tar.gz"
    echo "  ✓ existing backups archived"
fi

# Step 5: Backup storage directory
echo ""
echo "Step 5: Backing up storage directory..."
if [ -d "./storage" ]; then
    tar -czf "${BACKUP_DIR}/storage_backup.tar.gz" storage
    echo "✓ storage backup completed"
fi

# Step 6: Create backup manifest
echo ""
echo "Step 6: Creating backup manifest..."
cat > "${BACKUP_DIR}/manifest.txt" << EOF
GovStack Backup Manifest
========================
Backup Date: $(date)
Timestamp: ${TIMESTAMP}

Contents:
- postgres_full_backup.sql: Complete PostgreSQL dump (all databases)
- govstackdb_backup.sql: GovStack application database
- metabase_backup.sql: Metabase application database (if exists)
- postgres_data.tar.gz: PostgreSQL data directory
- chroma_data.tar.gz: ChromaDB vector store data
- minio_data.tar.gz: MinIO object storage data
- metabase_data.tar.gz: Metabase data (if exists)
- backups_archive.tar.gz: Previous backup archives
- storage_backup.tar.gz: Storage directory

Disk Usage:
$(du -sh "${BACKUP_DIR}")

File List:
$(ls -lh "${BACKUP_DIR}")
EOF
echo "✓ Manifest created"

# Display backup summary
echo ""
echo "=========================================="
echo "Backup Summary"
echo "=========================================="
cat "${BACKUP_DIR}/manifest.txt"

# Step 7: Clear data directories (with confirmation)
echo ""
echo "=========================================="
echo "WARNING: About to clear all data!"
echo "=========================================="
echo "The following directories will be cleared:"
echo "  - ${DATA_DIR}/postgres"
echo "  - ${DATA_DIR}/chroma"
echo "  - ${DATA_DIR}/minio"
echo "  - ${DATA_DIR}/metabase"
echo "  - ${DATA_DIR}/backups"
echo "  - ./storage"
echo ""
echo "Backup location: ${BACKUP_DIR}"
echo ""
read -p "Type 'YES' to proceed with clearing data: " confirmation

if [ "$confirmation" != "YES" ]; then
    echo "Aborting. Data has been backed up but not cleared."
    exit 1
fi

echo ""
echo "Step 7: Clearing data directories..."

# Clear PostgreSQL data
if [ -d "${DATA_DIR}/postgres" ]; then
    echo "  - Clearing postgres data..."
    sudo rm -rf "${DATA_DIR}/postgres"/*
    echo "  ✓ postgres data cleared"
fi

# Clear ChromaDB data
if [ -d "${DATA_DIR}/chroma" ]; then
    echo "  - Clearing chroma data..."
    sudo rm -rf "${DATA_DIR}/chroma"/*
    echo "  ✓ chroma data cleared"
fi

# Clear MinIO data
if [ -d "${DATA_DIR}/minio" ]; then
    echo "  - Clearing minio data..."
    sudo rm -rf "${DATA_DIR}/minio"/*
    echo "  ✓ minio data cleared"
fi

# Clear Metabase data
if [ -d "${DATA_DIR}/metabase" ]; then
    echo "  - Clearing metabase data..."
    sudo rm -rf "${DATA_DIR}/metabase"/*
    echo "  ✓ metabase data cleared"
fi

# Clear backup directories
if [ -d "${DATA_DIR}/backups" ]; then
    echo "  - Clearing backup data..."
    sudo rm -rf "${DATA_DIR}/backups"/*
    echo "  ✓ backup data cleared"
fi

# Clear storage directory
if [ -d "./storage" ]; then
    echo "  - Clearing storage directory..."
    sudo rm -rf ./storage/*
    echo "  ✓ storage directory cleared"
fi

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo "✓ All data has been backed up to: ${BACKUP_DIR}"
echo "✓ All data directories have been cleared"
echo ""
echo "Next steps:"
echo "  1. Run: docker compose up -d --build"
echo "  2. This will create fresh databases and volumes"
echo ""
echo "To restore from backup:"
echo "  1. Stop services: docker compose down"
echo "  2. Extract archives from ${BACKUP_DIR}"
echo "  3. Restore databases from SQL dumps"
echo "  4. Start services: docker compose up -d"
echo "=========================================="
