"""
Migration script to add the collection_id column to the webpages table.
This script is useful when updating an existing database to support collection_id.
"""

import argparse
import asyncio
import os
import sys
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def add_collection_id_column(db_url):
    """Add collection_id column to webpages table if it doesn't exist."""
    engine = create_async_engine(db_url, echo=False)
    
    # Check if the column already exists
    check_sql = text("""
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'webpages' 
        AND column_name = 'collection_id'
    );
    """)
    
    add_column_sql = text("""
    ALTER TABLE webpages
    ADD COLUMN IF NOT EXISTS collection_id VARCHAR(64);
    
    CREATE INDEX IF NOT EXISTS idx_webpages_collection_id ON webpages (collection_id);
    """)
    
    async with engine.begin() as conn:
        result = await conn.execute(check_sql)
        column_exists = result.scalar()
        
        if column_exists:
            logger.info("collection_id column already exists in the webpages table.")
            return False
        
        # Add the column and index
        logger.info("Adding collection_id column to webpages table...")
        await conn.execute(add_column_sql)
        logger.info("Successfully added collection_id column and index.")
        return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Add collection_id column to webpages table')
    
    # Database URL argument
    parser.add_argument('--db-url', type=str, 
                        default=os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/govstackdb'),
                        help='Database URL (default: from DATABASE_URL env var)')
    
    return parser.parse_args()

async def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    try:
        added = await add_collection_id_column(args.db_url)
        if added:
            print("Successfully added collection_id column to webpages table.")
        else:
            print("No changes were needed. The collection_id column already exists.")
    except Exception as e:
        logger.error(f"Error adding collection_id column: {e}")
        print(f"Failed to add collection_id column: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
