"""
Command-line utility to manually run indexing for document collections.

This script provides a convenient way to index documents in a collection,
either by collection ID or for all collections.
"""

import argparse
import asyncio
import sys
import os
import logging
from datetime import datetime, timezone

# Add project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.rag.indexer import index_documents_by_collection
from app.db.models.webpage import Webpage
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")

# Handle Windows-specific issue with localhost
if "localhost" in DATABASE_URL and os.name == "nt":
    DATABASE_URL = DATABASE_URL.replace("localhost", "127.0.0.1")

# Create engine and session maker
try:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    sys.exit(1)

async def get_all_collection_ids():
    """Get all unique collection IDs from the Webpage table."""
    async with async_session_maker() as db:
        query = select(distinct(Webpage.collection_id)).where(Webpage.collection_id != None)
        result = await db.execute(query)
        collection_ids = [cid[0] for cid in result.fetchall() if cid[0]]
        return collection_ids

async def run_indexing(collection_id=None, reindex=False):
    """Run the indexing process for one or all collections."""
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting indexing process at {start_time.isoformat()}")
    
    if collection_id:
        # Index a specific collection
        logger.info(f"Indexing collection: {collection_id}")
        result = await index_documents_by_collection(collection_id)
        logger.info(f"Result for collection '{collection_id}': {result['status']}")
        if result['status'] == 'completed':
            logger.info(f"Processed {result['documents_processed']} documents, indexed {result['documents_indexed']}")
    else:
        # Index all collections
        collection_ids = await get_all_collection_ids()
        logger.info(f"Found {len(collection_ids)} collections to index: {', '.join(collection_ids)}")
        
        for cid in collection_ids:
            logger.info(f"Indexing collection: {cid}")
            result = await index_documents_by_collection(cid)
            logger.info(f"Result for collection '{cid}': {result['status']}")
            if result['status'] == 'completed':
                logger.info(f"Processed {result['documents_processed']} documents, indexed {result['documents_indexed']}")
    
    end_time = datetime.now(timezone.utc)
    logger.info(f"Indexing process completed at {end_time.isoformat()}")
    logger.info(f"Total time: {(end_time - start_time).total_seconds()} seconds")

def main():
    """Parse command-line arguments and run indexing."""
    parser = argparse.ArgumentParser(description="Index documents in a collection")
    parser.add_argument(
        "--collection", "-c", 
        help="Collection ID to index. If not specified, all collections will be indexed."
    )
    parser.add_argument(
        "--reindex", "-r", 
        action="store_true",
        help="Reindex all documents, including those already indexed. Not yet implemented."
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_indexing(args.collection, args.reindex))
    except KeyboardInterrupt:
        logger.info("Indexing process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in indexing process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
