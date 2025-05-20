#!/usr/bin/env python
"""
Migration script to update the chat table structure to the new format.
"""
import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, ForeignKey, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models
from app.db.models.chat import Base, Chat, ChatMessage
from app.db.database import engine as async_engine

# Sync engine for schema operations
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
SYNC_DATABASE_URL = DATABASE_URL.replace('+asyncpg', '')

def sync_create_tables():
    """Create tables using synchronous engine - for fine control of schema changes."""
    try:
        sync_engine = create_engine(SYNC_DATABASE_URL)
        metadata = MetaData()
        
        # Drop existing chat_messages table first
        with sync_engine.connect() as conn:
            logger.info("Checking if old chat_messages table exists...")
            if sync_engine.dialect.has_table(conn, 'chat_messages'):
                logger.info("Dropping old chat_messages table...")
                conn.execute(f"DROP TABLE chat_messages CASCADE")
                conn.commit()
        
        # Create new tables
        logger.info("Creating new chat_messages table with updated schema...")
        metadata.create_all(sync_engine)
        
        logger.info("Table schema updated successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error updating schema: {str(e)}")
        sys.exit(1)

async def migrate_data():
    """Migrate data from old structure to new structure."""
    async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
    
    try:
        async with async_session() as session:
            # Create new tables
            await session.run_sync(lambda sync_session: Base.metadata.create_all(sync_session.bind))
            
            # Commit the changes
            await session.commit()
            
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise

async def main():
    """Main migration function."""
    logger.info("Starting chat table migration...")
    
    # Create tables with sync engine
    sync_create_tables()
    
    # Migrate data
    await migrate_data()
    
    logger.info("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
