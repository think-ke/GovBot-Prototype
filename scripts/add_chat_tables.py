"""
Script to add chat persistence tables to the database.

This script adds Chat and ChatMessage tables to support storing and retrieving chat history.
"""
import os
import sys
import logging
import argparse
import asyncio
from sqlalchemy import Column, Boolean, DateTime, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base

# Add project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Define models (copy from app.db.models.chat to ensure independent operation)
class Chat(Base):
    """
    Model for tracking chat conversations.
    """
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(64), nullable=True, index=True)  # Optional user identification
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    meta_data = Column(JSON, nullable=True)  # For additional chat session metadata


class ChatMessage(Base):
    """
    Model for storing individual messages in a chat conversation.
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'request', 'response', 'tool-call', 'tool-return', etc
    content = Column(Text, nullable=False)
    model_name = Column(String(64), nullable=True)
    timestamp = Column(DateTime(timezone=True))
    meta_data = Column(JSON, nullable=True)  # For additional message metadata, like tokens used
    message_idx = Column(Integer, nullable=False)  # Order of messages in the conversation


async def add_chat_tables():
    """Add the chat tables to the database if they don't exist."""
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
    
    # Handle Windows-specific issue with localhost
    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")
    
    logger.info(f"Connecting to database: {database_url}")
    
    # Create engine
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        # Check if tables already exist using proper async query format
        has_chats_table = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "chats")
        )
        has_chat_messages_table = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "chat_messages")
        )
        
        if has_chats_table and has_chat_messages_table:
            logger.info("Chat tables already exist.")
        else:
            # Create tables
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
            logger.info("Chat tables created successfully.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Add chat persistence tables to the database")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    try:
        asyncio.run(add_chat_tables())
        print("✅ Chat tables migration completed successfully!")
    except Exception as e:
        logger.error(f"Error in database migration: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
