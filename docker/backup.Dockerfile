FROM postgres:17.5-alpine

# Install dcron and bash
RUN apk add --no-cache dcron bash

# Create backup directory
RUN mkdir -p /backups

# Create cron directories
RUN mkdir -p /var/spool/cron/crontabs

# Copy backup service script
COPY scripts/backup_service.sh /usr/local/bin/backup_service.sh
RUN chmod +x /usr/local/bin/backup_service.sh

# Set working directory
WORKDIR /backups

# Expose backup directory as volume
VOLUME ["/backups"]

# Run the backup service
CMD ["/usr/local/bin/backup_service.sh"]
