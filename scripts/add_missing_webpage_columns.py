"""
Script to add missing columns to the Webpage table.

This script adds any missing columns to the webpages table to ensure
compatibility with the latest model definition.
"""

import asyncio
import sys
import os
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def add_missing_columns():
    """Add missing columns to the Webpage table."""
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
    
    # Handle Windows-specific issue with localhost
    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")
    
    logger.info(f"Connecting to database: {database_url}")
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        # Check which columns exist
        check_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'webpages' AND column_name IN ('is_seed', 'is_indexed', 'indexed_at')
        """)
        
        try:
            result = await conn.execute(check_query)
            existing_columns = [row[0] for row in result.fetchall()]
            
            has_is_seed = 'is_seed' in existing_columns
            has_is_indexed = 'is_indexed' in existing_columns
            has_indexed_at = 'indexed_at' in existing_columns
            
            logger.info(f"Existing columns check - is_seed: {has_is_seed}, is_indexed: {has_is_indexed}, indexed_at: {has_indexed_at}")
        
        except Exception as e:
            logger.error(f"Error checking existing columns: {e}")
            raise
        
        # Add columns if they don't exist
        try:
            if not has_is_seed:
                logger.info("Adding is_seed column...")
                add_is_seed = text("ALTER TABLE webpages ADD COLUMN is_seed BOOLEAN NOT NULL DEFAULT FALSE")
                await conn.execute(add_is_seed)
                logger.info("Added is_seed column")
            else:
                logger.info("is_seed column already exists")
            
            if not has_is_indexed:
                logger.info("Adding is_indexed column...")
                add_is_indexed = text("ALTER TABLE webpages ADD COLUMN is_indexed BOOLEAN NOT NULL DEFAULT FALSE")
                await conn.execute(add_is_indexed)
                logger.info("Added is_indexed column")
            else:
                logger.info("is_indexed column already exists")
            
            if not has_indexed_at:
                logger.info("Adding indexed_at column...")
                add_indexed_at = text("ALTER TABLE webpages ADD COLUMN indexed_at TIMESTAMP WITH TIME ZONE")
                await conn.execute(add_indexed_at)
                logger.info("Added indexed_at column")
            else:
                logger.info("indexed_at column already exists")
            
            # Verify all columns were added successfully
            verify_query = text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'webpages' AND column_name IN ('is_seed', 'is_indexed', 'indexed_at')
            """)
            result = await conn.execute(verify_query)
            final_columns = [row[0] for row in result.fetchall()]
            
            logger.info(f"Final verification - columns present: {final_columns}")
            
            if len(final_columns) == 3:
                logger.info("All required columns are now present in the webpages table")
            else:
                logger.warning(f"Some columns may still be missing. Expected 3 columns, found {len(final_columns)}")
            
            logger.info("Database update completed successfully")
            
        except Exception as e:
            logger.error(f"Error adding columns: {e}")
            raise

if __name__ == "__main__":
    try:
        asyncio.run(add_missing_columns())
        logger.info("Script completed successfully.")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)
