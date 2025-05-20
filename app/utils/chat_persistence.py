"""
Chat persistence service for storing and retrieving chat history.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter

from app.db.models.chat import Chat, ChatMessage

logger = logging.getLogger(__name__)


class ChatPersistenceService:
    """Service for storing and retrieving chat history."""
    @staticmethod
    async def create_chat_session(db: AsyncSession, user_id: Optional[str] = None) -> str:
        """
        Create a new chat session.
        
        Args:
            db: Database session
            user_id: Optional user identifier
            
        Returns:
            The session ID for the new chat
        """
        # Generate a unique session ID
        session_id = str(uuid4())
        
        # Create chat record
        chat = Chat(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        logger.info(f"Created new chat session with ID: {session_id}")
        return session_id
        
    @staticmethod
    async def create_chat_session_with_id(db: AsyncSession, session_id: str, user_id: Optional[str] = None) -> str:
        """
        Create a new chat session with a specific session ID.
        
        Args:
            db: Database session
            session_id: The session ID to use
            user_id: Optional user identifier
            
        Returns:
            The session ID that was provided
        """
        # Create chat record with the provided session ID
        chat = Chat(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        logger.info(f"Created new chat session with provided ID: {session_id}")
        return session_id

    @staticmethod
    async def get_chat_by_session_id(db: AsyncSession, session_id: str) -> Optional[Chat]:
        """
        Retrieve a chat by its session ID.
        
        Args:
            db: Database session
            session_id: The session ID to look up
            
        Returns:
            The chat object if found, None otherwise
        """
        query = select(Chat).where(Chat.session_id == session_id)
        result = await db.execute(query)
        chat = result.scalars().first()
        
        return chat

    @staticmethod
    async def save_message(
        db: AsyncSession,
        session_id: str,
        message_type: str,
        message_object: Dict[str, Any],
        history: Optional[List[Any]] = None
    ) -> bool:
        """
        Save a single message for a chat session.
        
        Args:
            db: Database session
            session_id: The session ID to save the message for
            message_type: Type of message ('user' or 'assistant')
            message_object: Dictionary containing the message content
            history: Optional raw message history from the agent (only for assistant messages)
                     This should be the result of to_jsonable_python(result.all_messages())
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, get the chat
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.error(f"Chat session {session_id} not found")
                return False
            
            # Create message
            message = ChatMessage(
                chat_id=chat.id,
                message_id=str(uuid4()),
                message_type=message_type,
                message_object=message_object,
                history=history,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.add(message)
            
            # Update the chat's updated_at timestamp
            chat.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            logger.info(f"Saved {message_type} message for chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            await db.rollback()
            return False
    
    @staticmethod
    async def load_history(db: AsyncSession, session_id: str) -> Optional[List]:
        """
        Load message history for a chat session.
        
        Args:
            db: Database session
            session_id: The session ID to load messages for
            
        Returns:
            List of model messages if found and valid, None otherwise
        """
        try:
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.warning(f"Chat session {session_id} not found when loading history")
                return None
            
            # Get the most recent assistant message with history
            query = select(ChatMessage).where(
                (ChatMessage.chat_id == chat.id) & 
                (ChatMessage.message_type == 'assistant') & 
                (ChatMessage.history.isnot(None))
            ).order_by(ChatMessage.timestamp.desc())
            
            result = await db.execute(query)
            message = result.scalars().first()
            
            if message and message.history:
                logger.info(f"Found message history for session {session_id}")
                # Convert history back to ModelMessage format using ModelMessagesTypeAdapter
                return ModelMessagesTypeAdapter.validate_python(message.history)
            
            logger.info(f"No message history found for session {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading message history: {str(e)}")
            return None
    @staticmethod
    async def delete_chat_session(db: AsyncSession, session_id: str) -> bool:
        """
        Delete a chat session and all its messages.
        
        Args:
            db: Database session
            session_id: The session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.error(f"Chat session {session_id} not found")
                return False
            
            await db.delete(chat)
            await db.commit()
            
            logger.info(f"Deleted chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session: {str(e)}")
            await db.rollback()
            return False
