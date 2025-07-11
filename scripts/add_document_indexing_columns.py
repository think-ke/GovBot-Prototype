#!/usr/bin/env python3
"""
Migration script to add indexing tracking columns to the documents table.

This script adds is_indexed and indexed_at columns to support tracking
which documents have been processed by the RAG indexer.
"""

import asyncio
import logging
from sqlalchemy import text
from app.db.database import async_session

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def add_document_indexing_columns():
    """Add indexing columns to the documents table."""
    
    async with async_session() as session:
        try:
            # Check if columns exist
            check_columns_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name IN ('is_indexed', 'indexed_at')
            """)
            
            result = await session.execute(check_columns_query)
            existing_columns = [row[0] for row in result.fetchall()]
            
            has_is_indexed = 'is_indexed' in existing_columns
            has_indexed_at = 'indexed_at' in existing_columns
            
            logger.info(f"Existing columns check - is_indexed: {has_is_indexed}, indexed_at: {has_indexed_at}")
            
            # Add missing columns
            if not has_is_indexed:
                logger.info("Adding is_indexed column...")
                add_is_indexed = text("ALTER TABLE documents ADD COLUMN is_indexed BOOLEAN NOT NULL DEFAULT FALSE")
                await session.execute(add_is_indexed)
                logger.info("Added is_indexed column")
            else:
                logger.info("is_indexed column already exists")
            
            if not has_indexed_at:
                logger.info("Adding indexed_at column...")
                add_indexed_at = text("ALTER TABLE documents ADD COLUMN indexed_at TIMESTAMP WITH TIME ZONE")
                await session.execute(add_indexed_at)
                logger.info("Added indexed_at column")
            else:
                logger.info("indexed_at column already exists")
            
            # Commit changes
            await session.commit()
            
            # Final verification
            final_check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name IN ('is_indexed', 'indexed_at')
            """)
            
            result = await session.execute(final_check_query)
            final_columns = [row[0] for row in result.fetchall()]
            
            logger.info(f"Final column verification - columns present: {final_columns}")
            logger.info("✅ Document indexing columns migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error during migration: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_document_indexing_columns())
