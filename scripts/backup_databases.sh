#!/bin/bash
set -e

# Step 1: Backup PostgreSQL Databases
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./data_backups/backup_${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"

echo "Backing up PostgreSQL databases to ${BACKUP_DIR}..."
docker compose exec -T postgres pg_dumpall -U postgres > "${BACKUP_DIR}/postgres_full_backup.sql"
docker compose exec -T postgres pg_dump -U postgres -d govstackdb > "${BACKUP_DIR}/govstackdb_backup.sql"

echo "✓ Database backups completed in ${BACKUP_DIR}"
echo "${BACKUP_DIR}"
