# Database Backup System

This document explains the PostgreSQL backup system for the GovStack application.

## Backup Structure

Backups are stored in the `data/` folder alongside other persistent data:
- `data/backups/` - Production database backups
- `data/backups-dev/` - Development database backups

## Automated Backups

### Production Environment
- **Schedule**: Daily at 2:00 AM
- **Retention**: 30 days
- **Service**: `backup` service in `docker-compose.yml`

### Development Environment
- **Schedule**: Every 6 hours
- **Retention**: 7 days
- **Service**: `backup-dev` service in `docker-compose.dev.yml`

## Manual Backup

You can create manual backups using the provided script:

```bash
# Create a manual backup for production
./scripts/postgres_backup.sh prod manual

# Create a manual backup for development
./scripts/postgres_backup.sh dev manual
```

## Graceful Shutdown with Backup

Use the shutdown script to ensure a backup is created before stopping services:

```bash
# Shutdown production with backup
./shutdown_with_backup.sh prod

# Shutdown development with backup
./shutdown_with_backup.sh dev
```

## Backup File Format

Backup files are named with the following pattern:
```
govstackdb_{environment}_{type}_{timestamp}.sql.gz
```

Examples:
- `govstackdb_prod_scheduled_20250626_020000.sql.gz`
- `govstackdb_dev_manual_20250626_140530.sql.gz`
- `govstackdb_prod_shutdown_20250626_180000.sql.gz`

## Restore from Backup

To restore from a backup:

1. Stop the application services
2. Extract the backup file:
   ```bash
   gunzip data/backups/govstackdb_prod_shutdown_20250626_180000.sql.gz
   ```

3. Restore using docker exec:
   ```bash
   # For production
   docker exec -i govstack-server-postgres-1 psql -U postgres -d govstackdb < data/backups/govstackdb_prod_shutdown_20250626_180000.sql
   
   # For development
   docker exec -i govstack-test-server-postgres-dev-1 psql -U postgres -d govstackdb < data/backups-dev/govstackdb_dev_shutdown_20250626_180000.sql
   ```

4. Restart the application services

## Monitoring Backup Status

Check backup service logs:
```bash
# Production backup logs
docker logs govstack-server-backup-1

# Development backup logs
docker logs govstack-test-server-backup-dev-1
```

## Backup Service Features

- **Automatic cleanup**: Keeps only the configured number of days worth of backups
- **Compression**: All backups are gzip compressed to save space
- **Health monitoring**: Backup services restart automatically if they fail
- **Environment variables**: Easily configurable via Docker Compose environment variables
