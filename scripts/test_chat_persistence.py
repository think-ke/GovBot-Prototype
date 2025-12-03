"""
Test script for chat persistence functionality.

This script demonstrates how to use the chat persistence service with the PydanticAI agent.
It creates a chat session, sends a message, saves the conversation, then continues the
conversation with a follow-up question.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.models.chat import Base
from app.utils.chat_persistence import ChatPersistenceService
from app.core.orchestrator import generate_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def test_chat_persistence():
    """Test the chat persistence functionality."""
    logger.info("Starting chat persistence test")
    
    # Create database tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a database session
    async with async_session() as db:
        # Create a new chat session
        user_id = "test_user_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        session_id = await ChatPersistenceService.create_chat_session(db, user_id)
        logger.info(f"Created new chat session with ID: {session_id}")
        
        # Step 1: Send an initial message and save the conversation
        logger.info("Step 1: Sending initial message")
        agent = generate_agent()
        result = agent.run_sync(
            "What is the role of the Kenya Film Commission in the film industry?"
        )
        
        # Log the response
        logger.info(f"Initial response: {result.output.answer[:100]}...")
        
        # Save the messages
        success = await ChatPersistenceService.save_messages(db, session_id, result.all_messages())
        if success:
            logger.info("Successfully saved initial messages")
        else:
            logger.error("Failed to save initial messages")
            return
        
        # Step 2: Continue the conversation with a follow-up question
        logger.info("Step 2: Loading previous messages and sending follow-up")
        
        # Load the previous messages - use the new method to properly handle relationships
        chat_with_messages = await ChatPersistenceService.get_chat_with_messages(db, session_id)
        if not chat_with_messages:
            logger.error("Failed to load message history")
            return
            
        message_history = await ChatPersistenceService.load_messages(db, session_id)
        if not message_history:
            logger.error("Failed to load message history")
            return
        
        # Create a new agent with the message history
        follow_up_agent = generate_agent(message_history=message_history)
        
        # Send a follow-up question
        follow_up_result = follow_up_agent.run_sync(
            "Can you elaborate on their support for filmmakers?"
        )
        
        # Log the response
        logger.info(f"Follow-up response: {follow_up_result.output.answer[:100]}...")
        
        # Save only the new messages
        success = await ChatPersistenceService.save_messages(db, session_id, follow_up_result.new_messages())
        if success:
            logger.info("Successfully saved follow-up messages")
        else:
            logger.error("Failed to save follow-up messages")
            return
        
        # Step 3: Retrieve the full conversation
        logger.info("Step 3: Retrieving the full conversation")
        
        # Get the chat by session ID
        chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
        if not chat:
            logger.error(f"Failed to retrieve chat with session ID: {session_id}")
            return
        
        # Print the chat metadata
        logger.info(f"Chat session ID: {chat.session_id}")
        logger.info(f"User ID: {chat.user_id}")
        logger.info(f"Created at: {chat.created_at}")
        logger.info(f"Updated at: {chat.updated_at}")
        logger.info(f"Number of messages: {len(chat.messages)}")
        
        logger.info("Chat persistence test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_chat_persistence())
