#!/bin/bash

# PostgreSQL Backup Script
# Usage: ./postgres_backup.sh [dev|prod] [backup_type]
# backup_type: manual, scheduled, shutdown

set -e

# Default values
ENVIRONMENT=${1:-prod}
BACKUP_TYPE=${2:-manual}

# Set environment-specific variables
if [ "$ENVIRONMENT" = "dev" ]; then
    POSTGRES_HOST="postgres-dev"
    POSTGRES_PORT="5432"
    POSTGRES_USER="postgres"
    POSTGRES_DB="govstackdb"
    BACKUP_DIR="./data/backups-dev"
    COMPOSE_SERVICE="postgres-dev"
else
    POSTGRES_HOST="postgres"
    POSTGRES_PORT="5432"
    POSTGRES_USER="postgres"
    POSTGRES_DB="govstackdb"
    BACKUP_DIR="./data/backups"
    COMPOSE_SERVICE="postgres"
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/govstackdb_${ENVIRONMENT}_${BACKUP_TYPE}_${TIMESTAMP}.sql"

echo "Creating PostgreSQL backup for $ENVIRONMENT environment..."
echo "Backup type: $BACKUP_TYPE"
echo "Backup file: $BACKUP_FILE"

# Get postgres password from environment or use default
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}

# Create the backup using docker exec
if [ "$ENVIRONMENT" = "dev" ]; then
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" govstack-test-server-postgres-dev-1 \
        pg_dump -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --verbose --clean --if-exists --no-owner --no-privileges > "$BACKUP_FILE"
else
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" govstack-server-postgres-1 \
        pg_dump -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --verbose --clean --if-exists --no-owner --no-privileges > "$BACKUP_FILE"
fi

# Compress the backup file
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "Backup completed successfully: $BACKUP_FILE"

# Keep only the last 10 backups of each type
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "govstackdb_${ENVIRONMENT}_${BACKUP_TYPE}_*.sql.gz" -type f | \
    sort -r | tail -n +11 | xargs -r rm -f

echo "Backup process completed."

# Return the backup file path for use in other scripts
echo "$BACKUP_FILE"
