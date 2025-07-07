#!/bin/bash

# Database Backup Cron Service
# This script runs inside a backup container and handles periodic backups

set -e

POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_DB=${POSTGRES_DB:-govstackdb}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
BACKUP_SCHEDULE=${BACKUP_SCHEDULE:-"0 2 * * *"}  # Default: daily at 2 AM
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

BACKUP_DIR="/backups"

echo "Database Backup Service Starting..."
echo "Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "Database: $POSTGRES_DB"
echo "Schedule: $BACKUP_SCHEDULE"
echo "Retention: $BACKUP_RETENTION_DAYS days"

# Function to perform backup
perform_backup() {
    local backup_type=${1:-scheduled}
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/govstackdb_${backup_type}_${timestamp}.sql"
    
    echo "Creating backup: $backup_file"
    
    # Wait for PostgreSQL to be ready
    until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
    done
    
    # Create backup
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges > "$backup_file"
    
    # Compress backup
    gzip "$backup_file"
    backup_file="${backup_file}.gz"
    
    echo "✅ Backup completed: $backup_file"
    
    # Clean up old backups
    find "$BACKUP_DIR" -name "govstackdb_${backup_type}_*.sql.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
    echo "🧹 Cleaned up backups older than $BACKUP_RETENTION_DAYS days"
}

# Function to handle shutdown signal
shutdown_backup() {
    echo "🛑 Shutdown signal received, creating final backup..."
    perform_backup "shutdown"
    exit 0
}

# Set up signal handlers
trap shutdown_backup SIGTERM SIGINT

# Create initial backup
perform_backup "startup"

# Set up cron job for Alpine Linux dcron
echo "$BACKUP_SCHEDULE /usr/local/bin/backup_script.sh scheduled" > /var/spool/cron/crontabs/root
chmod 0600 /var/spool/cron/crontabs/root

# Create the backup script that cron will call
cat > /usr/local/bin/backup_script.sh << 'EOF'
#!/bin/bash
source /backup_env.sh
perform_backup "$1"
EOF
chmod +x /usr/local/bin/backup_script.sh

# Export functions and variables for cron
declare -f perform_backup > /backup_env.sh
echo "POSTGRES_HOST=$POSTGRES_HOST" >> /backup_env.sh
echo "POSTGRES_PORT=$POSTGRES_PORT" >> /backup_env.sh
echo "POSTGRES_USER=$POSTGRES_USER" >> /backup_env.sh
echo "POSTGRES_DB=$POSTGRES_DB" >> /backup_env.sh
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> /backup_env.sh
echo "BACKUP_DIR=$BACKUP_DIR" >> /backup_env.sh
echo "BACKUP_RETENTION_DAYS=$BACKUP_RETENTION_DAYS" >> /backup_env.sh

# Start cron daemon
echo "Starting cron daemon..."
crond -f &

# Keep the container running and wait for signals
echo "🔄 Backup service is running..."
while true; do
    sleep 60
done
