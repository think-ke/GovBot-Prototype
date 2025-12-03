# Document Indexing for GovStack

This directory contains tools and utilities for indexing crawled web documents in the GovStack system.

## Overview

The indexing system automatically processes crawled web documents and adds them to a vector database for efficient retrieval. Key features:

- Automatic indexing after crawl completion
- Tracks indexed/unindexed status in the database
- Command-line utilities for manual indexing and status checking
- Only processes new (unindexed) documents

## Core Components

- **Indexer Module**: `app/core/rag/indexer.py` - Contains the main indexing logic
- **Database Model**: `app/db/models/webpage.py` - Includes fields to track indexing status
- **Integration with Crawler**: Automatic indexing is triggered at the end of a crawl operation

## Utility Scripts

### Run Indexing Manually

To manually index documents for a specific collection:

```bash
python scripts/run_indexing.py --collection <collection_id>
```

To index all collections:

```bash
python scripts/run_indexing.py
```

### Check Indexing Status

To check the indexing status of a specific collection:

```bash
python scripts/check_indexing_status.py --collection <collection_id>
```

To check the status of all collections:

```bash
python scripts/check_indexing_status.py
```

### Adding Index Tracking Fields

If you're upgrading from a previous version, you'll need to add the indexing columns to your database:

```bash
python scripts/add_indexing_columns.py
```

## Configuration

The indexing system uses the following environment variables:

- `DATABASE_URL`: Connection string for the PostgreSQL database (default: `postgresql+asyncpg://postgres:postgres@localhost/govstackdb`)
- `CHROMA_HOST`: Hostname for ChromaDB (default: `localhost`)
- `CHROMA_PORT`: Port for ChromaDB (default: `8050`) 
- `OPENAI_API_KEY`: API key for OpenAI embeddings (required for indexing)

## How It Works

1. When a web crawl completes, `start_background_indexing()` is called with the collection ID
2. The indexer runs asynchronously in the background while the API returns
3. Unindexed documents are retrieved from the database
4. Documents are processed through an ingestion pipeline:
   - Text is split into chunks
   - Chunks are embedded using OpenAI embeddings
   - Embeddings are stored in ChromaDB
5. After successful indexing, documents are marked as indexed in the database

## Troubleshooting

If you encounter issues with indexing, check the following:

1. Make sure ChromaDB is running and accessible
2. Verify that the OpenAI API key is valid and has sufficient quota
3. Check the application logs for specific error messages
4. Run the status check script to see the current indexing state
