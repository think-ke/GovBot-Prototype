# Metabase Setup Documentation

## Overview
Metabase has been added to the GovStack Docker Compose configuration for business intelligence and data visualization capabilities.

## Configuration Details

### Service Configuration
- **Image**: `metabase/metabase:latest`
- **Port**: 3000 (configurable via `METABASE_PORT` environment variable)
- **Application Database**: PostgreSQL (using the existing `postgres` service)
- **Database Name**: `metabase` (separate from the main `govstackdb`)

### Data Persistence
- **Volume Mount**: `./data/metabase:/metabase-data`
- **Purpose**: Stores Metabase application data and configurations locally

### Environment Variables
You can customize the following environment variables in your `.env` file:

```bash
# Metabase Configuration
METABASE_PORT=3000
METABASE_ENCRYPTION_SECRET_KEY=your-secret-key-here
METABASE_SITE_URL=http://localhost:3000

# PostgreSQL (shared with existing configuration)
POSTGRES_PASSWORD=your-postgres-password
```

### Recommended Environment Variables
For production use, add these to your `.env` file:

```bash
# Generate a strong encryption key for Metabase
METABASE_ENCRYPTION_SECRET_KEY=$(openssl rand -base64 32)

# Set your site URL if using a domain
METABASE_SITE_URL=https://your-domain.com
```

## Accessing Metabase

1. Start the services: `docker-compose up -d`
2. Wait for initialization (2-3 minutes)
3. Access Metabase at: http://localhost:3000
4. Complete the initial setup wizard

## Initial Setup Steps

1. **Admin Account**: Create an admin account with strong credentials
2. **Organization**: Configure your organization name and preferences
3. **Database Connection**: Connect to your business databases
   - Use the existing PostgreSQL service for data analysis
   - Host: `postgres`
   - Port: `5432`
   - Database: `govstackdb`
   - Username: `postgres`
   - Password: Your `POSTGRES_PASSWORD`

## Health Check
Metabase includes a health check endpoint at `/api/health` that monitors:
- Application startup status
- Database connectivity
- Service availability

## Performance Recommendations

### Java Heap Settings
The configuration includes optimized Java heap settings:
- Initial heap: 1GB (`-Xms1g`)
- Maximum heap: 2GB (`-Xmx2g`)

For higher usage environments, consider increasing these values:
```yaml
JAVA_OPTS: "-Xmx4g -Xms2g"  # For high-traffic environments
```

### System Requirements
Based on Metabase documentation:
- **Baseline**: 1 CPU core, 1GB RAM
- **Per 20 concurrent users**: +1 CPU core, +2GB RAM
- **Example**: 40 concurrent users = 3 CPU cores, 5GB RAM

## Security Considerations

1. **Encryption Key**: Always set `METABASE_ENCRYPTION_SECRET_KEY` in production
2. **Database Security**: Metabase uses a separate `metabase` database for its application data
3. **Network**: Runs on the internal `govstack-net` network
4. **HTTPS**: Configure reverse proxy for HTTPS in production

## Backup and Maintenance

### Metabase Application Data
The Metabase application database is automatically backed up as part of the PostgreSQL backup process since it uses the same PostgreSQL instance.

### Application Data Volume
The `./data/metabase` directory contains:
- H2 database files (if any)
- Plugin files
- Configuration files
- Log files

## Troubleshooting

### Common Issues
1. **Startup Time**: Metabase takes 2-3 minutes to fully initialize
2. **Memory Issues**: Increase `JAVA_OPTS` memory settings if needed
3. **Database Connection**: Ensure PostgreSQL is healthy before Metabase starts

### Logs
View Metabase logs:
```bash
docker-compose logs -f metabase
```

### Service Status
Check service health:
```bash
docker-compose ps
curl http://localhost:3000/api/health
```

## Integration with GovStack

Metabase can connect to and visualize data from:
- The main GovStack PostgreSQL database (`govstackdb`)
- MinIO object storage (for file-based data)
- External databases and APIs
- Chroma vector database (for AI/ML insights)

This provides comprehensive business intelligence capabilities for the GovStack platform.
