#!/usr/bin/env python
"""
Migration script to add chat event tracking tables to the database.
"""

import asyncio
import os
import sys
import logging
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models
from app.db.models.chat_event import ChatEvent, Base

async def add_event_tracking_tables():
    """Add the chat event tracking tables to the database if they don't exist."""
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
    
    # Handle Windows-specific issue with localhost
    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")

    logger.info(f"Connecting to database: {database_url}")
    
    # Create engine
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        # Check if tables already exist
        has_chat_events_table = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "chat_events")
        )
        
        if has_chat_events_table:
            logger.info("Chat event tracking tables already exist.")
        else:
            # Create tables
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
            logger.info("Chat event tracking tables created successfully.")
    
    await engine.dispose()

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Add chat event tracking tables to the database")
    parser.add_argument(
        "--database-url",
        help="Database URL (defaults to DATABASE_URL environment variable)"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
    
    try:
        asyncio.run(add_event_tracking_tables())
        print("✅ Chat event tracking tables migration completed successfully!")
    except Exception as e:
        logger.error(f"Error in database migration: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
