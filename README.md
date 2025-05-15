# GovStack: AI-Powered eCitizen Services Agent

GovStack is an intelligent document management and citizen assistance system designed to handle government-related documents with secure storage, retrieval, and processing capabilities. The system is specifically tailored to support eCitizen services in Kenya through AI-powered information retrieval and assistance.

## Features

- AI-powered assistance for eCitizen services in Kenya
- RAG (Retrieval Augmented Generation) capabilities for accurate information retrieval
- Document upload, storage, and retrieval with semantic search
- Web crawling capabilities for automatic information gathering
- Collection-based organization of documents and web content
- Secure authentication and authorization
- MinIO integration for scalable object storage
- ChromaDB for vector database capabilities
- PostgreSQL for relational data storage
- Docker-based deployment for production and development environments
- Fully containerized architecture for easy deployment across environments

## Prerequisites

- Docker and Docker Compose v2.x+
- For local development:
  - Python 3.11+ (required for compatibility with dependencies)
  - Git
  - 4GB+ RAM available for running containers
  - 20GB+ free disk space for databases and document storage
- For API access:
  - Valid OpenAI API key for LLM functionality
  - Optional: Additional API keys as specified in .env.example

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
  - Development API: http://localhost:9090
  - Development Console: http://localhost:9091
  - Default credentials: minioadmin/minioadmin (unless changed in .env)

- **PostgreSQL**:
  - Production Port: 5432
  - Development Port: 5433
  - Default credentials: postgres/postgres (unless changed in .env)

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
│   ├── core/             # Core business logic
│   │   ├── crawlers/     # Web crawling components
│   │   ├── orchestrator.py  # Central orchestration of AI agents
│   │   └── rag/          # Retrieval Augmented Generation components
│   ├── db/               # Database models and utilities
│   │   └── models/       # SQLAlchemy ORM models
│   └── utils/            # Utility functions and shared code
│       ├── prompts.py    # LLM prompt templates
│       └── storage.py    # Storage utilities (MinIO interface)
├── docker/               # Docker configuration files
│   ├── api.Dockerfile    # Production API container definition
│   └── api.dev.Dockerfile # Development API container definition
├── scripts/              # Utility scripts for operations and maintenance
│   ├── add_collection_id_column.py  # Database migration script
│   ├── add_indexing_columns.py      # Database migration script
│   ├── run_indexing.py              # Script to run RAG indexing
│   └── update_webpage_collections.py # Collection management script
├── data/                 # Persistent data storage (created by containers)
│   ├── chroma/           # ChromaDB vector database files
│   ├── minio/            # MinIO object storage
│   └── postgres/         # PostgreSQL database files
├── .env                  # Environment variables for production
├── .env.example          # Example environment configuration
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Production Docker configuration
├── docker-compose.dev.yml  # Development Docker configuration
├── server.htpasswd       # ChromaDB authentication file
└── README.md             # Project documentation
```

### Key Components

- **FastAPI Application**: The main API server in `app/api/fast_api_app.py`
- **Orchestrator**: Manages AI agent interactions in `app/core/orchestrator.py`
- **Web Crawler**: Handles web content retrieval in `app/core/crawlers/web_crawler.py`
- **RAG System**: Manages vector indexing in `app/core/rag/indexer.py`
- **Database Models**: 
  - `app/db/models/webpage.py`: Stores crawled web content
  - `app/db/models/document.py`: Stores uploaded documents

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

## Backup and Restore

### Creating Backups

Regularly back up all data for disaster recovery:

```bash
# Back up PostgreSQL database
docker compose exec postgres pg_dump -U postgres govstackdb > backup_$(date +%Y%m%d).sql

# Back up MinIO data
rsync -avz ./data/minio /path/to/backup/

# Back up ChromaDB vectors
rsync -avz ./data/chroma /path/to/backup/
```

### Restoring from Backup

```bash
# Restore PostgreSQL database
cat backup_20230515.sql | docker compose exec -T postgres psql -U postgres -d govstackdb

# Restore MinIO and ChromaDB
rsync -avz /path/to/backup/minio/ ./data/minio/
rsync -avz /path/to/backup/chroma/ ./data/chroma/
```

## License

This project is proprietary and confidential.