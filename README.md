# GovStack: AI-Powered eCitizen Services Agent

GovStack is an intelligent document management and citizen assistance system designed to handle government-related documents with secure storage, retrieval, and processing capabilities. The system is specifically tailored to support eCitizen services in Kenya through AI-powered information retrieval and assistance.

## Features

### Core Features
- **AI-powered assistance** for eCitizen services in Kenya using PydanticAI agents
- **RAG (Retrieval Augmented Generation)** capabilities for accurate information retrieval
- **Document management** with upload, storage, and retrieval using semantic search
- **Web crawling** capabilities for automatic information gathering
- **Collection-based organization** of documents and web content
- **Conversation history persistence** with the ability to continue conversations
- **Token usage tracking** for OpenAI API cost monitoring and projections

### Infrastructure & Storage
- **MinIO integration** for scalable object storage
- **ChromaDB** for vector database capabilities with authentication
- **PostgreSQL** for relational data storage with automated backups
- **Metabase** for business intelligence and data visualization
- **Docker-based deployment** for production and development environments
- **Fully containerized architecture** for easy deployment across environments

### Backup & Recovery
- **Automated database backups** with configurable retention policies
- **Graceful shutdown** with automatic backup creation
- **Manual backup tools** for on-demand database snapshots
- **Disaster recovery procedures** with comprehensive restore capabilities

### Testing & Scalability
- **Comprehensive testing suite** for performance and scalability validation
- **Load testing** supporting up to 1000 concurrent users and 40,000 daily users
- **External API testing** capabilities for testing against remote deployments
- **Token usage tracking** and cost projection for scaling scenarios
- **Performance monitoring** with Prometheus and Grafana integration

## Prerequisites

- **Docker and Docker Compose v2.x+**
- **For local development:**
  - Python 3.11+ (required for compatibility with dependencies)
  - Git
  - 4GB+ RAM available for running containers (8GB+ recommended for testing)
  - 20GB+ free disk space for databases and document storage
- **For API access:**
  - Valid OpenAI API key for LLM functionality
  - Optional: Additional API keys as specified in .env.example
- **For scalability testing:**
  - Additional RAM and CPU cores (16GB RAM, 8 CPU cores for 1000+ concurrent users)
  - Network connectivity for external API testing

## Quick Start

### Setting Up Environment Variables

1. Clone the repository:
   ```bash
   git clone https://your-repository-url/govstack.git
   cd govstack
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env   # If you're creating a new installation
   ```

3. Edit the `.env` file to customize settings:
   - Set `OPENAI_API_KEY` with your valid key
   - Configure database credentials (`POSTGRES_PASSWORD`)
   - Set secure passwords for ChromaDB and MinIO
   - Enable/disable GPU acceleration with `USE_GPU=true` if available
   
4. Set ChromaDB authentication credentials in your `.env` file:
   - Define `CHROMA_USERNAME` and `CHROMA_PASSWORD` values
   - Then create a `server.htpasswd` file using these credentials:
   ```bash
      # Use the same username and password you set in .env
      docker run --rm --entrypoint htpasswd httpd:2 -Bbn "$CHROMA_USERNAME" "$CHROMA_PASSWORD" > server.htpasswd
   ```

### Running in Production Mode

1. Launch the full stack:
   ```bash
   docker compose up -d
   ```

2. Access the API at http://localhost:5000

### Running in Development Mode

1. Start the development stack:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

2. Access the development API at http://localhost:5005

## System Architecture

<iframe src="https://app.eraser.io/workspace/JxI0qDfxxU7BF0aRxjqk/preview?elements=7v0nc64pjZXHYe_DV-yt3g&type=embed" width="100%" height="500px" frameborder="0" allowfullscreen></iframe>

This diagram illustrates the core components and data flow of the GovStack system. For a more detailed architectural explanation, see the [Technical Design Document](./docs/technical_design.md).

## Component Access

- **API Server**: 
  - Production: http://localhost:5000
  - Development: http://localhost:5005
  - API Documentation: http://localhost:5000/docs

- **ChromaDB**:
  - Production: http://localhost:8050
  - Development: http://localhost:8001
  - Default credentials: See your `.env` file or server.htpasswd

- **MinIO Object Storage**:
  - Production API: http://localhost:9000
  - Production Console: http://localhost:9001
  - Development API: http://localhost:9002
  - Development Console: http://localhost:9092
  - Default credentials: minioadmin/minioadmin (unless changed in .env)

- **PostgreSQL**:
  - Production Port: 5432
  - Development Port: 5433
  - Default credentials: postgres/postgres (unless changed in .env)

- **Analytics Module**:
  - Production API: http://localhost:8005
  - Development API: http://localhost:8006
  - API Documentation: http://localhost:8005/docs
  - Health Check: http://localhost:8005/analytics/health

- **Analytics Dashboard**:
  - Production Web Interface: http://localhost:3001
  - Development Web Interface: http://localhost:3002
  - Health Check: http://localhost:3001/api/health (production) or http://localhost:3002/api/health (development)
  - Real-time analytics visualization and business intelligence

- **Metabase Analytics**:
  - Web Interface: http://localhost:3000
  - API Health Check: http://localhost:3000/api/health
  - Database: Uses PostgreSQL `metabase` database for application data
  - Setup: Complete initial setup wizard on first access

- **Testing Infrastructure**:
  - Test Service UI: http://localhost:8084 (when running tests)
  - Prometheus Monitoring: http://localhost:9090 (when running tests)
  - Grafana Dashboard: http://localhost:3000 (when running tests)
  - Locust Load Testing UI: http://localhost:8089 (when running load tests)

## API Documentation

GovStack provides a full OpenAPI-compliant REST API. You can access the interactive API documentation at:

- Production: http://localhost:5000/docs
- Development: http://localhost:5005/docs

### Key API Endpoints

#### Document Management

```bash
# Upload a document
curl -X POST "http://localhost:5000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf" \
  -F "collection_id=kenya-gov-docs"

# List documents by collection
curl "http://localhost:5000/documents/collection/kenya-gov-docs"

# Get document details
curl "http://localhost:5000/documents/123"
```

#### Web Crawling & Content Management

GovStack provides an AI-powered interface to Kenya's eCitizen services, helping citizens:

- Find the right government services and documentation requirements
- Get guidance on application processes and procedures
- Retrieve information about service fees and payment methods
- Access document templates and examples
- Navigate complex government processes with natural language queries

The system uses Retrieval Augmented Generation (RAG) to ensure responses are grounded in accurate, up-to-date official information.

## Web Crawler Features

### Collection-Based Crawling

The web crawler allows you to organize crawled webpages into collections using the `collection_id` parameter. This is useful for:

- Separating crawls by topic or domain
- Tracking different crawl sessions
- Organizing content for specific RAG applications

#### Example crawl with collection_id:

```bash
curl -X POST http://localhost:5000/crawl/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ecitizen.go.ke/",
    "depth": 3,
    "concurrent_requests": 10,
    "follow_external": false,
    "strategy": "breadth_first",
    "collection_id": "ecitizen-may2023"
  }'
```

#### Retrieve webpages by collection:

```bash
curl http://localhost:5000/webpages/collection/ecitizen-may2023
```

#### Update existing webpages with collection_id:

You can use the provided script to add collection_id to existing webpages:

```bash
# List existing collections
python scripts/update_webpage_collections.py list

# Add collection_id to all webpages from a specific domain
python scripts/update_webpage_collections.py domain ecitizen.go.ke ecitizen-official

# Add collection_id to webpages by ID range
python scripts/update_webpage_collections.py id-range 1 100 batch-one
```

This feature makes it easy to manage multiple crawl jobs and organize content by source or topic.

### Extracting Crawled Text Content

You can extract all text content from webpages in a specific collection, with filtering by crawl time:

```bash
# Extract all texts from a collection as raw text
curl -X POST http://localhost:5000/extract-texts/ \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "ecitizen-may2023",
    "hours_ago": 24,
    "output_format": "text"
  }'

# Extract as JSON with metadata
curl -X POST http://localhost:5000/extract-texts/ \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "ecitizen-may2023",
    "hours_ago": 24,
    "output_format": "json"
  }'

# Get collection statistics
curl http://localhost:5000/collection-stats/ecitizen-may2023
```

This feature makes it easy to:
- Export crawled content for further processing
- Use the extracted text for training or fine-tuning LLMs
- Create custom datasets from web content
- Filter by recency to get only the latest information

## Database Migration

If you're updating an existing installation, you'll need to add the collection_id column to the database:

```bash
# Run the migration script to add collection_id column
python scripts/add_collection_id_column.py
```

## Development Workflow

### Local Development

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the API server locally:
   ```bash
   uvicorn app.api.fast_api_app:app --reload --port 5005
   ```

### Building and Updating Docker Images

To rebuild the Docker images after code changes:

```bash
docker compose -f docker-compose.dev.yml build api
docker compose -f docker-compose.dev.yml up -d api
```

## File Structure

```
govstack/
├── app/                  # Application source code
│   ├── api/              # API endpoints and FastAPI application
│   │   ├── fast_api_app.py  # Main FastAPI application entry point
│   │   └── endpoints/    # API endpoint modules organized by feature
│   │       ├── chat_endpoints.py     # Chat and conversation endpoints
│   │       └── webpage_endpoints.py  # Web crawling and webpage endpoints
│   ├── core/             # Core business logic
│   │   ├── crawlers/     # Web crawling components
│   │   │   ├── web_crawler.py  # Main web crawler implementation
│   │   │   └── utils.py        # Crawler utility functions
│   │   ├── orchestrator.py  # Central orchestration of AI agents
│   │   └── rag/          # Retrieval Augmented Generation components
│   │       ├── indexer.py      # Vector indexing for RAG
│   │       ├── tool_loader.py  # Tool loading utilities
│   │       └── README.md       # RAG system documentation
│   ├── db/               # Database models and utilities
│   │   ├── database.py   # Database configuration and connection
│   │   └── models/       # SQLAlchemy ORM models
│   │       ├── chat.py      # Chat sessions and message models
│   │       ├── document.py  # Document storage models
│   │       └── webpage.py   # Webpage and crawling models
│   ├── models/           # Additional model definitions
│   └── utils/            # Utility functions and shared code
│       ├── chat_persistence.py  # Chat history persistence
│       ├── prompts.py           # LLM prompt templates
│       ├── storage.py           # Storage utilities (MinIO interface)
│       └── README_chat_persistence.md  # Chat persistence documentation
├── backups/              # Database backup storage
│   └── prod/            # Production database backups
├── data/                 # Persistent data storage (created by containers)
│   ├── backups/         # Database backup files
│   ├── backups-dev/     # Development database backups
│   ├── chroma/          # ChromaDB vector database files
│   ├── chroma-dev/      # Development ChromaDB files
│   ├── minio/           # MinIO object storage
│   ├── minio-dev/       # Development MinIO storage
│   ├── postgres/        # PostgreSQL database files
│   └── postgres-dev/    # Development PostgreSQL files
├── docker/               # Docker configuration files
│   ├── api.Dockerfile    # Production API container definition
│   ├── api.dev.Dockerfile # Development API container definition
│   └── backup.Dockerfile # Database backup container definition
├── docs/                 # Documentation files
│   ├── dqf.md           # Data Quality Framework documentation
│   ├── GovStack_Detailed_Presentation_Slides.md
│   ├── GovStack_Technical_Architecture_Presentation.md
│   ├── implementation_status.md  # Implementation status tracking
│   └── technical_design.md       # Technical design documentation
├── examples/             # Example code and usage
│   └── chat_api_examples.md  # Chat API usage examples
├── scripts/              # Utility scripts for operations and maintenance
│   ├── __init__.py      # Python package initialization
│   ├── add_chat_tables.py           # Chat table migration script
│   ├── add_collection_id_column.py  # Collection ID migration script
│   ├── add_indexing_columns.py      # Indexing columns migration script
│   ├── backup_service.sh            # Backup service script
│   ├── check_indexing_status.py     # Indexing status checker
│   ├── migrate_chat_tables.py       # Chat table migration
│   ├── postgres_backup.sh           # PostgreSQL backup script
│   ├── run_indexing.py              # RAG indexing runner
│   ├── run_migration.py             # Database migration runner
│   ├── test_chat_persistence.py     # Chat persistence tests
│   ├── test_new_chat_persistence.py # New chat persistence tests
│   └── update_webpage_collections.py # Collection management script
├── storage/              # Additional storage utilities
├── tests/                # Comprehensive testing suite
│   ├── cli.py           # Command-line interface for tests
│   ├── config.py        # Test configuration
│   ├── run_tests.sh     # Test execution script
│   ├── requirements.txt # Test dependencies
│   ├── Dockerfile       # Test container definition
│   ├── docker-compose.test.yml      # Test environment Docker config
│   ├── docker-compose.external.yml  # External testing Docker config
│   ├── .env.test        # Test environment variables
│   ├── .env.external    # External testing environment variables
│   ├── prometheus.yml   # Prometheus monitoring config
│   ├── prometheus.external.yml # External Prometheus config
│   ├── integration_tests/  # Integration test suite
│   ├── load_tests/         # Load and performance tests
│   ├── scalability_tests/  # Scalability testing
│   ├── unit_tests/         # Unit test suite
│   ├── utils/              # Test utilities
│   ├── results/            # Test result storage
│   ├── README.md           # Testing documentation
│   └── EXTERNAL_TESTING.md # External testing guide
├── .env                  # Environment variables for production
├── .env.dev              # Development environment variables
├── .env.example          # Example environment configuration
├── .gitignore            # Git ignore patterns
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Production Docker configuration
├── docker-compose.dev.yml  # Development Docker configuration
├── docker_inspector.sh  # Docker inspection utility
├── server.htpasswd       # ChromaDB authentication file
├── shutdown_with_backup.sh  # Graceful shutdown with backup script
├── README.md             # Project documentation
└── README_DATABASE_BACKUPS.md  # Database backup documentation
```

### Key Components

- **FastAPI Application**: The main API server in `app/api/fast_api_app.py`
- **Orchestrator**: Manages AI agent interactions in `app/core/orchestrator.py`
- **Web Crawler**: Handles web content retrieval in `app/core/crawlers/web_crawler.py`
- **RAG System**: Manages vector indexing in `app/core/rag/indexer.py`
- **Chat System**: Processes conversations and maintains context in `app/api/endpoints/chat_endpoints.py`
- **Chat Persistence**: Stores and retrieves chat history in `app/utils/chat_persistence.py`
- **Database Models**: 
  - `app/db/models/webpage.py`: Stores crawled web content
  - `app/db/models/document.py`: Stores uploaded documents
  - `app/db/models/chat.py`: Stores chat sessions and message history

## Troubleshooting

### Common Issues

1. **Connection refused to ChromaDB**:
   - Ensure the ChromaDB container is running: `docker ps | grep chroma`
   - Check credentials in `.env` match those in `server.htpasswd`
   - Verify port mapping: `docker compose ps chroma`
   - Check logs for specific errors: `docker compose logs chroma`
   - Make sure the network is properly configured

2. **Document upload failures**:
   - Verify MinIO is running: `docker ps | grep minio`
   - Check storage permissions and credentials in `.env`
   - Ensure bucket exists: 
     ```bash
     # Using MinIO client (mc)
     mc alias set govstack http://localhost:9000 minioadmin minioadmin
     mc ls govstack
     ```
   - Verify volume mounts are correctly configured in docker-compose.yml

3. **Database connection issues**:
   - Verify PostgreSQL is running: `docker ps | grep postgres`
   - Check database credentials in `.env` file
   - Test direct connection: 
     ```bash
     docker compose exec postgres psql -U postgres -d govstackdb -c "SELECT 1"
     ```
   - Check if database has been initialized properly:
     ```bash
     docker compose exec postgres psql -U postgres -c "\l"
     ```

4. **API server not starting**:
   - Check API server logs: `docker compose logs govstack-server`
   - Verify all required environment variables are set in `.env`
   - Confirm the database URL is correctly formatted
   - Ensure ports are not already in use: `netstat -tulpn | grep 5000`

5. **Slow performance or memory issues**:
   - Check container resource usage: `docker stats`
   - Increase container resources in docker-compose.yml if needed
   - Consider enabling faster database indexes for frequently queried fields
   - Check if the system is running out of disk space: `df -h`

6. **ChromaDB indexing failures**:
   - Verify connection to ChromaDB from the API container
   - Check available memory, as vector operations can be memory-intensive
   - Look for specific error messages in logs
   - Run manual indexing with debug mode: 
     ```bash
     python scripts/run_indexing.py --collection your-collection --debug
     ```

### Logs

View logs for a specific service:

```bash
# Production
docker compose logs -f <service-name>

# Development
docker compose -f docker-compose.dev.yml logs -f <service-name>
```

### Health Checks

Run health checks for all services:

```bash
# Check if all containers are running
docker compose ps

# Check API server health
curl http://localhost:5000/health

# Check ChromaDB health
curl -u thinkAdmin:thinkPassword http://localhost:8050/api/v1/heartbeat

# Check MinIO health
curl -I http://localhost:9000/minio/health/live
```

## Deployment

GovStack is designed to be deployed easily using Docker in various environments. You can deploy it on-premises, in a cloud environment, or on a dedicated server.

### Deployment Prerequisites

- Server with Docker and Docker Compose installed (v2.x+ recommended)
- At least 4GB RAM, 2 CPU cores recommended
- 20GB+ storage space for the database and document storage
- Port 5000 available for the API service
- Ports 8050, 9000, 9001, and 5432 available for supporting services
- Ports 8005-8006 available for analytics services
- Ports 3001-3002 available for analytics dashboard

### Cloud Deployment Options

#### AWS Deployment

1. Create an EC2 instance with Ubuntu 22.04 LTS
   - Recommended: t3.medium or larger
   - At least 20GB EBS storage

2. Install Docker and Docker Compose:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2
   sudo usermod -aG docker $USER
   ```

3. Clone the repository and configure:
   ```bash
   git clone https://your-repository-url/govstack.git
   cd govstack
   cp .env.example .env
   ```

4. Edit the `.env` file with your specific configuration, especially:
   - Set secure passwords for database and services
   - Configure any API keys needed for services
   - Update the `OPENAI_API_KEY` with your valid key

5. Launch the stack:
   ```bash
   sudo docker compose up -d
   ```

6. Configure AWS security groups to allow traffic on port 5000 (and other necessary ports)

#### Azure Deployment

1. Create an Azure VM with Ubuntu 22.04 LTS
   - Recommended: Standard B2s or larger
   - At least 20GB storage

2. Install Docker and Docker Compose following the same steps as AWS

3. Configure Network Security Group to allow inbound traffic on required ports

4. Follow the same repository setup and launch steps as AWS

### Secure Production Deployment

For production environments, additional security measures are recommended:

1. **Use HTTPS**: Set up a reverse proxy (Nginx/Traefik) with SSL certificates
   ```bash
   # Example Nginx configuration for HTTPS
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Set secure passwords**: Update all default passwords in the `.env` file

3. **Implement firewall rules**: Restrict access to only necessary ports
   ```bash
   # Example using ufw
   sudo ufw allow ssh
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

4. **Enable database backup**: Set up regular PostgreSQL backups
   ```bash
   # Add to crontab
   0 2 * * * docker exec govstack-server_postgres_1 pg_dump -U postgres -d govstackdb > /backup/govstack_$(date +\%Y\%m\%d).sql
   ```

5. **Monitor the system**: Use tools like Prometheus and Grafana for monitoring

### Scaling Considerations

For deployments requiring higher scale:

1. **Horizontal Scaling**: Deploy multiple API containers behind a load balancer
2. **Database Scaling**: Consider using a managed PostgreSQL service for larger deployments
3. **Object Storage**: For large document collections, consider using S3 or Azure Blob Storage instead of MinIO
4. **Vector Database**: For large vector collections, scale ChromaDB or consider alternatives like Pinecone or Weaviate

### CI/CD Integration

For automated deployments, you can use GitHub Actions or GitLab CI:

```yaml
# Example GitHub Actions workflow
name: Deploy GovStack

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /path/to/govstack
            git pull
            docker compose down
            docker compose build --no-cache
            docker compose up -d
```

### Updating the Application

When new code changes are available, follow these steps to update your deployment:

1. Pull the latest code changes:
   ```bash
   git pull origin main
   ```

2. Check for any changes to the environment variables or dependencies:
   ```bash
   # Compare your current .env with the example
   diff .env .env.example
   
   # Check for changes to requirements.txt
   cat requirements.txt
   ```

3. Run database migrations if needed:
   ```bash
   # Check for new migration scripts in the scripts/ directory
   ls -la scripts/
   
   # Run any new migration scripts
   python scripts/run_migration.py
   ```

4. Rebuild and restart the containers:
   ```bash
   # For production
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   
   # For development
   docker compose -f docker-compose.dev.yml down
   docker compose -f docker-compose.dev.yml build --no-cache
   docker compose -f docker-compose.dev.yml up -d
   ```

5. Verify the application is running correctly:
   ```bash
   # Check container status
   docker compose ps
   
   # Check the API health endpoint
   curl http://localhost:5000/health
   ```

## Performance Tuning

### API Server Tuning

Adjust the number of workers in the API server based on available CPU cores:

```bash
# Edit the docker-compose.yml file
# Change CMD to include more workers:
CMD ["uvicorn", "app.api.fast_api_app:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
```

### Database Tuning

For high-load environments, tune PostgreSQL performance:

1. Create a custom PostgreSQL configuration:
   ```bash
   # Create a custom postgresql.conf file with optimized settings
   mkdir -p config/postgres
   cp postgresql.conf.example config/postgres/postgresql.conf
   ```

2. Mount it in the docker-compose.yml file:
   ```yaml
   postgres:
     volumes:
       - ./config/postgres/postgresql.conf:/etc/postgresql/postgresql.conf
     command: postgres -c config_file=/etc/postgresql/postgresql.conf
   ```

3. Key settings to adjust:
   - `shared_buffers`: 25% of available RAM
   - `effective_cache_size`: 50-75% of available RAM
   - `work_mem`: Increase for complex queries
   - `maintenance_work_mem`: Increase for faster index creation

### ChromaDB Performance

For large vector collections:

1. Increase memory allocated to the ChromaDB container:
   ```yaml
   chroma:
     deploy:
       resources:
         limits:
           memory: 4G
   ```

2. Consider sharding the vector database for very large collections

## Backup and Disaster Recovery

GovStack includes a comprehensive backup and disaster recovery system to protect your data and ensure business continuity.

### Automated Database Backups

GovStack automatically backs up your PostgreSQL database using dedicated backup containers:

#### Production Environment
- **Schedule**: Daily at 2:00 AM
- **Retention**: 30 days
- **Location**: `./backups/prod/`
- **Service**: `backup` service in docker-compose.yml

#### Development Environment  
- **Schedule**: Every 6 hours
- **Retention**: 7 days
- **Location**: `./data/backups-dev/`
- **Service**: `backup-dev` service in docker-compose.dev.yml

### Manual Backup Operations

Create manual backups using the provided scripts:

```bash
# Create a manual backup for production
./scripts/postgres_backup.sh prod manual

# Create a manual backup for development
./scripts/postgres_backup.sh dev manual
```

### Graceful Shutdown with Backup

Always use the graceful shutdown script to ensure a backup is created before stopping services:

```bash
# Shutdown production with backup
./shutdown_with_backup.sh prod

# Shutdown development with backup
./shutdown_with_backup.sh dev
```

This script will:
1. Create a final database backup
2. Gracefully stop services in dependency order
3. Provide backup confirmation with file location

### Backup File Format

Backup files follow a consistent naming pattern:
```
govstackdb_{environment}_{type}_{timestamp}.sql.gz
```

**Examples:**
- `govstackdb_prod_scheduled_20250626_020000.sql.gz`
- `govstackdb_dev_manual_20250626_140530.sql.gz`
- `govstackdb_prod_shutdown_20250626_180000.sql.gz`

### Disaster Recovery Procedures

#### Complete System Restore

1. **Stop all services:**
   ```bash
   docker compose down  # or docker compose -f docker-compose.dev.yml down
   ```

2. **Restore database from backup:**
   ```bash
   # Extract the backup file
   gunzip data/backups/govstackdb_prod_shutdown_20250626_180000.sql.gz
   
   # Start only the database service
   docker compose up -d postgres
   
   # Restore the database
   docker exec -i govstack-server-postgres-1 psql -U postgres -d govstackdb < data/backups/govstackdb_prod_shutdown_20250626_180000.sql
   ```

3. **Restore file storage (if needed):**
   ```bash
   # Restore MinIO data from backup
   rsync -avz /path/to/backup/minio/ ./data/minio/
   
   # Restore ChromaDB vectors from backup
   rsync -avz /path/to/backup/chroma/ ./data/chroma/
   ```

4. **Start all services:**
   ```bash
   docker compose up -d
   ```

#### Monitoring Backup Health

Check backup service status and logs:

```bash
# Production backup logs
docker logs govstack-server-backup-1

# Development backup logs  
docker logs govstack-test-server-backup-dev-1

# Check backup service status
docker compose ps backup
```

### Backup Best Practices

- **Regular Testing**: Test restore procedures regularly
- **Off-site Storage**: Copy backups to remote storage for disaster recovery
- **Monitoring**: Set up alerts for backup failures
- **Documentation**: Keep restore procedures documented and accessible

For detailed backup configuration, see [README_DATABASE_BACKUPS.md](./README_DATABASE_BACKUPS.md).

## Token Usage Tracking & Cost Management

GovStack includes comprehensive token usage tracking to help you monitor and project OpenAI API costs:

### Automatic Token Tracking

All API requests automatically track:
- **Request tokens**: Input tokens sent to the LLM
- **Response tokens**: Output tokens generated by the LLM  
- **Total tokens**: Combined token usage
- **Cost estimates**: Based on current OpenAI pricing

### Supported Models & Pricing

The system tracks costs for:
- **GPT-4**: $0.03 input / $0.06 output per 1K tokens
- **GPT-4 Turbo**: $0.005 input / $0.015 output per 1K tokens
- **GPT-3.5 Turbo**: $0.001 input / $0.002 output per 1K tokens
- **Embeddings**: $0.00002 per 1K tokens

### Usage Analytics

Token usage data includes:
- **Timestamp tracking**: When each request was made  
- **Model identification**: Which LLM model was used
- **Request correlation**: Link usage to specific chat sessions
- **Cost projections**: Estimate monthly/daily costs based on usage patterns

### Scalability Cost Projections

For scaling planning, the system can project costs for:
- **1,000 concurrent users**: Estimated monthly API costs
- **40,000 daily users**: Daily and monthly usage projections
- **Peak load scenarios**: Cost implications of high-traffic periods

## Scalability Testing Suite

GovStack includes a comprehensive testing infrastructure to validate performance at scale.

### Testing Capabilities

The testing suite can simulate:
- **Up to 1,000 concurrent users**
- **40,000 daily users** with realistic usage patterns
- **Performance benchmarking** under various load conditions
- **External API testing** against remote deployments

### Test Types Available

#### Load Testing Scenarios
- **Baseline Performance**: Single-user performance metrics
- **Concurrent Users**: 10, 25, 50, 100, 250, 500, 1000 concurrent users  
- **Daily Load Simulation**: Realistic usage patterns throughout the day
- **Stress Testing**: Push the system beyond normal limits
- **Memory & Latency Analysis**: Resource usage and response time tracking

#### Key Metrics Measured
- **Response Times**: Average, median, P95, P99, maximum
- **Success Rates**: Request success/failure ratios
- **Memory Usage**: RAM consumption patterns over time
- **Token Usage**: OpenAI API costs and usage projections
- **Throughput**: Requests per second capacity
- **Network Latency**: Connection and processing delays

### Running Performance Tests

#### Quick Performance Check
```bash
cd tests/
./run_tests.sh quick-check
```

#### Full Scalability Test Suite
```bash
# Run all test types
cd tests/
./run_tests.sh run-tests

# Run specific test types
./run_tests.sh run-tests --test-types baseline,concurrent --max-users 500
```

#### Interactive Load Testing
```bash
# Start Locust web UI for manual testing control
cd tests/
./run_tests.sh locust-ui
# Then open http://localhost:8089
```

### External API Testing

Test against existing GovStack deployments without running local services:

#### Setup External Testing
```bash
cd tests/
# Configure target server
nano .env.external  # Set EXTERNAL_API_URL=http://your-server:5005

# Start external test environment
./run_tests.sh start-external

# Run tests against external server
./run_tests.sh run-tests --api-url http://your-server:5005
```

### Monitoring & Analytics

The testing infrastructure includes:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Performance visualization dashboards  
- **Real-time monitoring**: Live performance metrics during tests
- **Test result storage**: Historical test run data
- **Automated reporting**: Performance summaries and recommendations

### Test Environment Requirements

#### Minimum Requirements
- 4GB RAM, 2 CPU cores
- Docker and Docker Compose

#### Recommended for Full Scale Testing  
- 16GB RAM, 8 CPU cores
- SSD storage for database performance
- Stable network connection for external testing

For detailed testing documentation, see [tests/README.md](./tests/README.md).

## Backup and Restore

### Legacy Backup Commands

For additional backup operations, you can also use these direct commands:

```bash
# Back up PostgreSQL database
docker compose exec postgres pg_dump -U postgres govstackdb > backup_$(date +%Y%m%d).sql

# Back up MinIO data
rsync -avz ./data/minio /path/to/backup/

# Back up ChromaDB vectors
rsync -avz ./data/chroma /path/to/backup/
```

### Legacy Restore Commands

```bash
# Restore PostgreSQL database
cat backup_20230515.sql | docker compose exec -T postgres psql -U postgres -d govstackdb

# Restore MinIO and ChromaDB
rsync -avz /path/to/backup/minio/ ./data/minio/
rsync -avz /path/to/backup/chroma/ ./data/chroma/
```

**Note**: The automated backup system described above is the recommended approach for production use.

## License

This project is proprietary and confidential.

# GovStack API

GovStack is a comprehensive document management and AI-powered chat API that provides secure access to government information and services through intelligent conversation and document processing capabilities.

## Features

- **AI-Powered Chat**: Intelligent conversations with government data using advanced language models
- **Document Management**: Secure upload, storage, and retrieval of documents
- **Web Crawling**: Automated website crawling and content extraction
- **API Key Security**: Role-based access control with read, write, and delete permissions
- **Collection Management**: Organize and manage document collections with statistics
- **Vector Search**: Advanced semantic search capabilities using ChromaDB

## Quick Start

### Environment Setup

1. Copy the environment configuration:
```bash
cp .env.example .env.dev
```

2. Update the configuration in `.env.dev` with your API keys:
```bash
# Required API Keys
OPENAI_API_KEY="your-openai-api-key-here"
EXA_API_KEY="your-exa-api-key-here"

# API Security - Change these in production!
GOVSTACK_API_KEY="your-secure-master-api-key-here"
GOVSTACK_ADMIN_API_KEY="your-secure-admin-api-key-here"
```

### Authentication

All API endpoints (except `/` and `/health`) require API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api-info
```

#### API Key Permissions

- **Master Key** (`GOVSTACK_API_KEY`): Full access (read, write, delete)
- **Admin Key** (`GOVSTACK_ADMIN_API_KEY`): Read and write access
- Custom keys can be configured with specific permissions

### Core Endpoints

#### Health Check
```bash
# Public endpoint - no authentication required
GET /health
```

#### API Information
```bash
# Get your API key permissions
GET /api-info
Headers: X-API-Key: your-api-key-here
```

### Chat API

#### Start a Conversation
```bash
POST /chat/
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "message": "What services does the government provide for business registration?",
  "session_id": "optional-session-id",
  "user_id": "user123"
}
```

#### Get Chat History
```bash
GET /chat/{session_id}
X-API-Key: your-api-key-here
```

#### Delete Chat Session
```bash
DELETE /chat/{session_id}
X-API-Key: your-api-key-here
```

### Document Management

#### Upload Document
```bash
POST /documents/
X-API-Key: your-api-key-here
Content-Type: multipart/form-data

# Form fields:
# - file: Document file
# - description: Optional description
# - is_public: Boolean (default: false)
# - collection_id: Optional collection identifier
```

#### Get Document
```bash
GET /documents/{document_id}
X-API-Key: your-api-key-here
```

#### List Documents
```bash
GET /documents/?skip=0&limit=100
X-API-Key: your-api-key-here
```

### Web Crawling

#### Start Website Crawl
```bash
POST /crawl/
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "url": "https://example.gov",
  "depth": 3,
  "concurrent_requests": 10,
  "collection_id": "gov-docs"
}
```

#### Check Crawl Status
```bash
GET /crawl/{task_id}
X-API-Key: your-api-key-here
```

#### Fetch Single Webpage
```bash
POST /webpages/fetch-webpage/
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "url": "https://example.gov/page",
  "skip_ssl_verification": false
}
```

### Collection Management

#### Get Collection Statistics
```bash
GET /collection-stats/{collection_id}
X-API-Key: your-api-key-here
```

#### Get All Collections
```bash
GET /collection-stats/
X-API-Key: your-api-key-here
```

## Environment Variables

### Core Settings
```bash
USE_GPU=false                    # Enable GPU acceleration
DOCKER_RUNTIME=runc             # Docker runtime
DEV_MODE=true                   # Development mode
LOG_LEVEL=DEBUG                 # Logging level
```

### API Keys
```bash
OPENAI_API_KEY="sk-..."         # OpenAI API key
EXA_API_KEY="xxx-xxx-xxx"       # Exa search API key
GOVSTACK_API_KEY="master-key"   # Master API key (full access)
GOVSTACK_ADMIN_API_KEY="admin-key" # Admin API key (read/write)
```

### Database Configuration
```bash
POSTGRES_PASSWORD=your-password
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres-dev:5432/govstackdb
```

### ChromaDB Configuration
```bash
CHROMA_HOST=chroma-dev
CHROMA_PORT=8000
CHROMA_USERNAME=your-username
CHROMA_PASSWORD=your-password
CHROMA_CLIENT_AUTHN_CREDENTIALS=username:password
CHROMA_DEV_PORT=8001
```

### MinIO Configuration
```bash
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=govstack-docs
MINIO_DEV_PORT=9001
MINIO_CONSOLE_DEV_PORT=9091
```

## Security

### API Key Authentication
- All endpoints require valid API keys via `X-API-Key` header
- Different permission levels: read, write, delete
- Keys are validated against environment variables

### Permission Levels
- **Read**: Access to GET endpoints, chat history, document retrieval
- **Write**: Document upload, chat interactions, crawl operations
- **Delete**: Resource deletion capabilities

### Best Practices
1. Use different API keys for different applications
2. Rotate API keys regularly
3. Store API keys securely (environment variables, secret management)
4. Monitor API usage through logs
5. Use HTTPS in production

## Response Formats

### Success Response
```json
{
  "session_id": "uuid",
  "answer": "Response text",
  "sources": [...],
  "confidence": 0.95,
  "usage": {...}
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env.dev

# Run the application
python -m app.api.fast_api_app
```

### Docker Development
```bash
# Build and run with docker-compose
docker-compose up -d
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

## Monitoring and Logging

The application uses structured logging with configurable levels. All API requests are logged with trace IDs for debugging.

### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARNING`: Warning messages
- `ERROR`: Error conditions

## Support

For issues and questions, please check the logs and ensure proper API key configuration.