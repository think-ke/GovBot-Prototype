# GovStack: AI-Powered eCitizen Services Agent

GovStack is an intelligent document management and citizen assistance system designed to handle government-related documents with secure storage, retrieval, and processing capabilities. The system is specifically tailored to support eCitizen services in Kenya through AI-powered information retrieval and assistance.

## Features

- AI-powered assistance for eCitizen services in Kenya
- RAG (Retrieval Augmented Generation) capabilities for accurate information retrieval
- Document upload, storage, and retrieval with semantic search
- Secure authentication and authorization
- MinIO integration for object storage
- ChromaDB for vector database capabilities
- PostgreSQL for relational data storage
- Docker-based deployment for production and development environments

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

## Quick Start

### Setting Up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env   # If you're creating a new installation
   ```

2. Edit the `.env` file to customize settings like database passwords and API keys.

### Running in Production Mode

1. Start the ChromaDB server (first time setup):
   ```bash
   # Linux/macOS
   ./start_chroma.sh
   
   # Windows
   start_chroma.bat
   ```

2. Launch the full stack:
   ```bash
   docker compose up -d
   ```

3. Access the API at http://localhost:5000

### Running in Development Mode

1. Set up the development environment:
   ```bash
   # Linux/macOS
   ./start_chroma.sh --dev
   
   # Windows
   start_chroma.bat --dev
   ```

2. Start the development stack:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

3. Access the development API at http://localhost:5005

## Component Access

- **API Server**: 
  - Production: http://localhost:5000
  - Development: http://localhost:5005

- **ChromaDB**:
  - Production: http://localhost:8050
  - Development: http://localhost:8001
  - Default credentials: See your `.env` file or server.htpasswd

- **MinIO Object Storage**:
  - Production API: http://localhost:9000
  - Production Console: http://localhost:9001
  - Development API: http://localhost:9001
  - Development Console: http://localhost:9091
  - Default credentials: minioadmin/minioadmin (unless changed in .env)

- **PostgreSQL**:
  - Port: 5432
  - Default credentials: postgres/postgres (unless changed in .env)

## eCitizen Services Integration

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
├── app/                # Application source code
│   ├── api/            # API endpoints and server
│   ├── core/           # Core business logic
│   ├── db/             # Database models and utilities
│   └── utils/          # Utility functions
├── docker/             # Docker configuration files
├── data/               # Persistent data (created by containers)
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Production Docker configuration
└── docker-compose.dev.yml  # Development Docker configuration
```

## Troubleshooting

### Common Issues

1. **Connection refused to ChromaDB**:
   - Ensure the ChromaDB container is running: `docker ps | grep chroma`
   - Check credentials in `.env` match those in `server.htpasswd`

2. **Document upload failures**:
   - Verify MinIO is running: `docker ps | grep minio`
   - Check storage permissions and credentials

3. **Database connection issues**:
   - Verify PostgreSQL is running: `docker ps | grep postgres`
   - Check database credentials in `.env` file

### Logs

View logs for a specific service:

```bash
# Production
docker compose logs -f <service-name>

# Development
docker compose -f docker-compose.dev.yml logs -f <service-name>
```

## License

This project is proprietary and confidential.