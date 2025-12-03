#!/usr/bin/env python
"""
Test script for the chat persistence functionality.
"""
import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from uuid import uuid4
from pydantic_core import to_jsonable_python
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessagesTypeAdapter

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models and utilities
from app.db.database import async_session
from app.utils.chat_persistence import ChatPersistenceService
from app.core.orchestrator import generate_agent

async def test_chat_persistence():
    """Test chat persistence functionality."""
    async with async_session() as db:
        # Create a new chat session
        session_id = await ChatPersistenceService.create_chat_session(db)
        logger.info(f"Created new chat session with ID: {session_id}")
        
        # Initialize the agent
        agent = generate_agent()
        
        # Simulate a user message
        user_message = "What is the Kenya Film Commission?"
        await ChatPersistenceService.save_message(
            db, 
            session_id, 
            "user", 
            {"query": user_message}
        )
        logger.info(f"Saved user message: {user_message}")
        
        # Generate a response
        result = agent.run_sync(user_message)
        
        # Save the assistant's response
        assistant_message_obj = {
            "session_id": session_id,
            "answer": result.output.answer,
            "sources": result.output.sources,
            "confidence": result.output.confidence,
            "retriever_type": result.output.retriever_type,
            "trace_id": str(uuid4())
        }
        
        # Extract history
        history = result.all_messages()
        history_as_python = to_jsonable_python(history)
        
        await ChatPersistenceService.save_message(
            db,
            session_id,
            "assistant",
            assistant_message_obj,
            history=history_as_python
        )
        logger.info(f"Saved assistant message and history")
        
        # Now test loading the history
        loaded_history = await ChatPersistenceService.load_history(db, session_id)
        if loaded_history:
            logger.info(f"Successfully loaded message history")
            
            # Send a follow-up message with history
            follow_up_message = "Tell me more about its role"
            await ChatPersistenceService.save_message(
                db, 
                session_id, 
                "user", 
                {"query": follow_up_message}
            )
            
            result2 = agent.run_sync(follow_up_message, message_history=loaded_history)
            logger.info(f"Generated follow-up response with history")
            
            # Save the second assistant response
            assistant_message_obj2 = {
                "session_id": session_id,
                "answer": result2.output.answer,
                "sources": result2.output.sources,
                "confidence": result2.output.confidence,
                "retriever_type": result2.output.retriever_type,
                "trace_id": str(uuid4())
            }
            
            history2 = result2.all_messages()
            history2_as_python = to_jsonable_python(history2)
            
            await ChatPersistenceService.save_message(
                db, 
                session_id, 
                "assistant", 
                assistant_message_obj2,
                history=history2_as_python
            )
            logger.info(f"Saved follow-up assistant message and history")
            
        else:
            logger.error("Failed to load message history")
        
        logger.info(f"Test completed for session {session_id}")

if __name__ == "__main__":
    asyncio.run(test_chat_persistence())
