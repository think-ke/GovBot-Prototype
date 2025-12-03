"""
Command-line utility to check the indexing status of document collections.

This script provides information about which documents in a collection
have been indexed and which are still pending.
"""

import argparse
import asyncio
import sys
import os
import logging
from datetime import datetime, timezone
from tabulate import tabulate

# Add project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.models.webpage import Webpage
from sqlalchemy import select, distinct, func, and_
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

async def get_indexing_stats(collection_id=None):
    """Get indexing statistics for a specific collection or all collections."""
    async with async_session_maker() as db:
        if collection_id:
            # Stats for a specific collection
            stats = {}
            
            # Get total documents
            query = select(func.count(Webpage.id)).where(
                and_(
                    Webpage.collection_id == collection_id,
                    Webpage.content_markdown != None
                )
            )
            result = await db.execute(query)
            stats['total_documents'] = result.scalar() or 0
            
            # Get indexed documents
            query = select(func.count(Webpage.id)).where(
                and_(
                    Webpage.collection_id == collection_id,
                    Webpage.content_markdown != None,
                    Webpage.is_indexed == True
                )
            )
            result = await db.execute(query)
            stats['indexed_documents'] = result.scalar() or 0
            
            # Get unindexed documents
            query = select(func.count(Webpage.id)).where(
                and_(
                    Webpage.collection_id == collection_id,
                    Webpage.content_markdown != None,
                    Webpage.is_indexed == False
                )
            )
            result = await db.execute(query)
            stats['unindexed_documents'] = result.scalar() or 0
            
            # Get latest indexing time
            query = select(func.max(Webpage.indexed_at)).where(
                Webpage.collection_id == collection_id
            )
            result = await db.execute(query)
            latest_indexed = result.scalar()
            stats['latest_indexed'] = latest_indexed.isoformat() if latest_indexed else None
            
            return {collection_id: stats}
        else:
            # Stats for all collections
            collection_ids = await get_all_collection_ids()
            all_stats = {}
            
            for cid in collection_ids:
                stats = await get_indexing_stats(cid)
                all_stats.update(stats)
            
            return all_stats

async def run_status_check(collection_id=None):
    """Run the status check and display results."""
    if collection_id:
        logger.info(f"Checking indexing status for collection: {collection_id}")
        stats = await get_indexing_stats(collection_id)
    else:
        logger.info("Checking indexing status for all collections")
        stats = await get_indexing_stats()
    
    # Prepare data for table display
    table_data = []
    for cid, data in stats.items():
        table_data.append([
            cid,
            data['total_documents'],
            data['indexed_documents'],
            data['unindexed_documents'],
            f"{(data['indexed_documents'] / data['total_documents'] * 100) if data['total_documents'] > 0 else 0:.1f}%",
            data['latest_indexed'] or "Never"
        ])
    
    # Display table
    headers = ["Collection ID", "Total Docs", "Indexed", "Unindexed", "Progress", "Last Indexed"]
    print("\nIndexing Status:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Display summary
    total_docs = sum(data['total_documents'] for data in stats.values())
    indexed_docs = sum(data['indexed_documents'] for data in stats.values())
    print(f"\nSummary: {indexed_docs} of {total_docs} documents indexed")
    if total_docs > 0:
        print(f"Overall progress: {indexed_docs / total_docs * 100:.1f}%\n")

def main():
    """Parse command-line arguments and run status check."""
    parser = argparse.ArgumentParser(description="Check indexing status of document collections")
    parser.add_argument(
        "--collection", "-c", 
        help="Collection ID to check. If not specified, all collections will be checked."
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_status_check(args.collection))
    except KeyboardInterrupt:
        logger.info("Status check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in status check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
