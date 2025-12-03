#!/usr/bin/env python
"""
Migration script to add the message rating table.
"""
import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models
from app.db.models.message_rating import Base, MessageRating
from app.db.database import engine as async_engine

# Sync engine for schema operations
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
SYNC_DATABASE_URL = DATABASE_URL.replace('+asyncpg', '')

def sync_create_tables():
    """Create message rating table using synchronous engine."""
    try:
        sync_engine = create_engine(SYNC_DATABASE_URL)
        metadata = MetaData()
        
        # Check if table already exists
        with sync_engine.connect() as conn:
            logger.info("Checking if message_ratings table exists...")
            if sync_engine.dialect.has_table(conn, 'message_ratings'):
                logger.info("Message ratings table already exists.")
                return
        
        # Create new table
        logger.info("Creating message_ratings table...")
        metadata.create_all(sync_engine)
        
        logger.info("Message ratings table created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating message ratings table: {str(e)}")
        sys.exit(1)

async def add_message_rating_table():
    """Add the message rating table to the database if it doesn't exist."""
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
    
    # Handle Windows-specific issue with localhost
    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")
    
    logger.info(f"Connecting to database: {database_url}")
    
    # Create engine
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        # Check if table already exists
        has_message_ratings_table = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "message_ratings")
        )
        
        if has_message_ratings_table:
            logger.info("Message ratings table already exists.")
        else:
            # Create table
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
            logger.info("Message ratings table created successfully.")

async def main():
    """Main migration function."""
    logger.info("Starting message rating table migration...")
    
    try:
        await add_message_rating_table()
        logger.info("Migration completed successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
